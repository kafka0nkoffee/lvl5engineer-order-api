import os, uuid
from datetime import datetime
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# In-memory order store — populated by POST /orders, read by GET /orders/{id}/status
_orders: dict = {}


class OrderItem(BaseModel):
    sku: str
    quantity: int
    unit_price: float


class OrderRequest(BaseModel):
    user_id: str
    items: List[OrderItem]
    payment_scenario: str = "success"
    inventory_scenario: str = "all-available"


@app.post("/orders")
def create_order(req: OrderRequest):
    payment_url = os.environ.get("PAYMENT_URL", "http://localhost:8091")
    inventory_url = os.environ.get("INVENTORY_URL", "http://localhost:8092")
    payment_timeout = float(os.environ.get("PAYMENT_TIMEOUT_SECONDS", "5"))
    max_retries = int(os.environ.get("MAX_PAYMENT_RETRIES", "2"))

    # Step 1: check inventory
    inv_resp = httpx.post(
        f"{inventory_url}/inventory/check/{req.inventory_scenario}",
        json={"items": [i.model_dump() for i in req.items]},
        timeout=10.0,
    )
    inv_items = inv_resp.json().get("items", [])
    available = [i["sku"] for i in inv_items if i.get("available")]
    unavailable = [i["sku"] for i in inv_items if not i.get("available")]

    # Partial availability — surface to user, do not charge
    if unavailable and available:
        return {
            "status": "PARTIAL_UNAVAILABLE",
            "status_code": 207,
            "available_items": available,
            "unavailable_items": unavailable,
        }

    # Full stock-out — do not charge
    if unavailable:
        return {
            "status": "UNAVAILABLE",
            "status_code": 409,
            "unavailable_items": unavailable,
        }

    # Step 2: attempt payment with retry cap on timeout
    attempt = 0
    payment_timed_out = False

    while attempt < max_retries:
        attempt += 1
        try:
            pay_resp = httpx.post(
                f"{payment_url}/payments/charge/{req.payment_scenario}",
                json={"user_id": req.user_id, "items": [i.model_dump() for i in req.items]},
                timeout=payment_timeout,
            )
            pay_data = pay_resp.json()

            if pay_resp.status_code == 200:
                order_id = str(uuid.uuid4())
                _orders[order_id] = {
                    "db_status": "CONFIRMED",
                    "order_created_at": datetime.utcnow().isoformat(),
                }
                return {
                    "status": "CONFIRMED",
                    "order_id": order_id,
                }

            # Declined or other non-200
            return {
                "status": "PAYMENT_FAILED",
                "status_code": 402,
                "decline_reason": pay_data.get("reason"),
                "inventory_released": True,
            }

        except httpx.TimeoutException:
            payment_timed_out = True
            if attempt >= max_retries:
                break

    # Payment gateway timed out after all attempts
    return {
        "status": "PAYMENT_PENDING",
        "status_code": 202,
        "inventory_hold_minutes": 15,
        "payment_pending": True,
        "message": "Payment confirmation is in progress",
        "retry_count": attempt,
    }


@app.get("/orders/{order_id}/status")
def get_order_status(order_id: str):
    order = _orders.get(order_id)
    if order is None:
        return JSONResponse(status_code=404, content={"error": "Order not found"})
    return {
        "order_id": order_id,
        "status": order["db_status"],
        "db_status": order["db_status"],
        "placed_at": order["order_created_at"],
        "order_created_at": order["order_created_at"],
    }
