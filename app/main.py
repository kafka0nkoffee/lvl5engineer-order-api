import os, uuid, httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Order Management API")

PAYMENT_URL         = os.getenv("PAYMENT_URL",   "http://localhost:8081")
INVENTORY_URL       = os.getenv("INVENTORY_URL", "http://localhost:8082")
PAYMENT_TIMEOUT     = float(os.getenv("PAYMENT_TIMEOUT_SECONDS", "5"))
MAX_PAYMENT_RETRIES = int(os.getenv("MAX_PAYMENT_RETRIES", "2"))

USERS = {
    "user-123": {"id": "user-123", "name": "Priya Sharma"},
    "user-456": {"id": "user-456", "name": "Rohan Mehta"},
    "user-789": {"id": "user-789", "name": "Ananya Das"},
    "user-321": {"id": "user-321", "name": "Vikram Nair"},
    "user-654": {"id": "user-654", "name": "Meera Pillai"},
}
ORDERS: dict = {}
INVENTORY_HOLDS: dict = {}

class OrderItem(BaseModel):
    sku: str
    quantity: int
    unit_price: float

class CreateOrderRequest(BaseModel):
    user_id: str
    items: list[OrderItem]
    payment_scenario:   str = "success"
    inventory_scenario: str = "all-available"

@app.get("/users/{user_id}")
def get_user(user_id: str):
    user = USERS.get(user_id)
    if not user: raise HTTPException(404, f"User {user_id} not found")
    return user

@app.get("/users/{user_id}/orders")
def get_user_orders(user_id: str):
    if user_id not in USERS: raise HTTPException(404, f"User {user_id} not found")
    return {"user_id": user_id, "orders": [o for o in ORDERS.values() if o["user_id"] == user_id]}

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = ORDERS.get(order_id)
    if not order: raise HTTPException(404, f"Order {order_id} not found")
    return order

@app.post("/orders")
def create_order(req: CreateOrderRequest):
    if req.user_id not in USERS:
        raise HTTPException(404, f"User {req.user_id} not found")

    total = sum(i.unit_price * i.quantity for i in req.items)
    skus  = [i.sku for i in req.items]

    # 1. Check inventory BEFORE charging
    try:
        inv = httpx.post(f"{INVENTORY_URL}/inventory/check/{req.inventory_scenario}",
                         json={"skus": skus}, timeout=5.0)
        if inv.status_code == 404:
            raise HTTPException(503, f"Inventory scenario not found: {req.inventory_scenario}")
        inventory = inv.json()
    except httpx.RequestError as e:
        raise HTTPException(503, f"Inventory service unavailable: {e}")

    available   = [i for i in inventory["items"] if     i["available"]]
    unavailable = [i for i in inventory["items"] if not i["available"]]

    # 2. Full stock-out
    if not available:
        return {"order_id": None, "status": "UNAVAILABLE",
                "message": f"{unavailable[0]['sku']} is out of stock",
                "unavailable_items": [i["sku"] for i in unavailable],
                "payment_gateway_called": False, "status_code": 409}

    # 3. Partial availability
    if unavailable:
        return {"order_id": None, "status": "PARTIAL_UNAVAILABLE",
                "message": "Some items are unavailable. Please review and resubmit.",
                "available_items":   [i["sku"] for i in available],
                "unavailable_items": [i["sku"] for i in unavailable],
                "payment_gateway_called": False, "status_code": 207}

    # 4. Attempt payment with retry cap
    attempt, payment_result, payment_timed_out = 0, None, False
    while attempt < MAX_PAYMENT_RETRIES:
        attempt += 1
        try:
            pay = httpx.post(f"{PAYMENT_URL}/payments/charge/{req.payment_scenario}",
                             json={"amount": total, "user_id": req.user_id},
                             timeout=PAYMENT_TIMEOUT)
            if pay.status_code == 404:
                raise HTTPException(503, f"Payment scenario not found: {req.payment_scenario}")
            payment_result = pay.json()
            break
        except httpx.TimeoutException:
            payment_timed_out = True
            if attempt >= MAX_PAYMENT_RETRIES: break
        except httpx.RequestError as e:
            raise HTTPException(503, f"Payment service error: {e}")

    # 5. Timeout
    if payment_timed_out:
        order_id = str(uuid.uuid4())
        INVENTORY_HOLDS[order_id] = 15
        ORDERS[order_id] = {"order_id": order_id, "user_id": req.user_id,
                            "status": "PAYMENT_PENDING",
                            "items": [i.model_dump() for i in req.items], "total": total}
        return {"order_id": order_id, "status": "PAYMENT_PENDING",
                "message": "Payment confirmation is in progress. Your items are reserved for 15 minutes.",
                "payment_pending": True, "inventory_hold_minutes": 15,
                "retry_count": attempt, "status_code": 202}

    # 6. Declined
    if payment_result and payment_result.get("status") == "DECLINED":
        return {"order_id": None, "status": "PAYMENT_FAILED",
                "message": f"Payment declined: {payment_result.get('reason', 'unknown')}",
                "decline_reason": payment_result.get("reason"),
                "inventory_released": True, "status_code": 402}

    # 7. Confirmed
    order_id = str(uuid.uuid4())
    ORDERS[order_id] = {"order_id": order_id, "user_id": req.user_id,
                        "status": "CONFIRMED",
                        "items": [i.model_dump() for i in req.items],
                        "total": total,
                        "transaction_id": payment_result.get("transaction_id") if payment_result else None}
    return {"order_id": order_id, "status": "CONFIRMED",
            "message": "Order confirmed.", "status_code": 201}
