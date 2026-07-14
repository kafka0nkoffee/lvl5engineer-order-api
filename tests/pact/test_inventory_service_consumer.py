"""
Pact consumer tests for the order service → inventory service interaction.

All interactions are defined before serve() is called. See
test_payment_gateway_consumer.py for a full explanation of the pact-python
v3 FFI constraint that requires this structure.
"""
from pathlib import Path

import httpx

from pact import Pact

PACT_DIR = Path(__file__).parent.parent.parent / "pacts"
PACT_DIR.mkdir(exist_ok=True)


def test_inventory_service_consumer_contract():
    """
    Defines and verifies all inventory service interactions in one pass.

    Scenarios covered:
    - All items in stock → 200, all available: true
    - Item out of stock → 200, available: false
    - Partial availability → 200, mixed available flags
    """
    pact = Pact("OrderService", "InventoryService")

    # Scenario 1: all items available
    (
        pact.upon_receiving("an inventory check when all items are in stock")
        .given("all requested items are in stock")
        .with_request("POST", "/inventory/check/all-available")
        .with_body(
            {"items": [{"sku": "SHOE-RED-42", "quantity": 1, "unit_price": 89.99}]},
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(
            {
                "items": [
                    {"sku": "SHOE-RED-42", "available": True, "quantity": 3},
                    {"sku": "BELT-BRN-M", "available": True, "quantity": 1},
                ]
            },
            content_type="application/json",
        )
    )

    # Scenario 2: out of stock
    (
        pact.upon_receiving("an inventory check when an item is out of stock")
        .given("SHOE-RED-42 is out of stock")
        .with_request("POST", "/inventory/check/out-of-stock")
        .with_body(
            {"items": [{"sku": "SHOE-RED-42", "quantity": 1, "unit_price": 89.99}]},
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(
            {"items": [{"sku": "SHOE-RED-42", "available": False, "quantity": 0}]},
            content_type="application/json",
        )
    )

    # Scenario 3: partial availability
    (
        pact.upon_receiving("an inventory check with partial availability")
        .given("SHOE-RED-42 is available but BELT-BRN-M is not")
        .with_request("POST", "/inventory/check/partial")
        .with_body(
            {
                "items": [
                    {"sku": "SHOE-RED-42", "quantity": 1, "unit_price": 89.99},
                    {"sku": "BELT-BRN-M", "quantity": 1, "unit_price": 44.98},
                ]
            },
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(
            {
                "items": [
                    {"sku": "SHOE-RED-42", "available": True, "quantity": 2},
                    {"sku": "BELT-BRN-M", "available": False, "quantity": 0},
                ]
            },
            content_type="application/json",
        )
    )

    # Scenario 4: reservation release (order cancellation)
    (
        pact.upon_receiving("a reservation release for a cancelled order")
        .given("a confirmed reservation exists for the order")
        .with_request("POST", "/inventory/release/success")
        .with_body(
            {"order_id": "order-abc-123"},
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(
            {"released": True},
            content_type="application/json",
        )
    )

    with pact.serve() as mock_server:
        # Verify scenario 1
        resp = httpx.post(
            f"{mock_server.url}/inventory/check/all-available",
            json={"items": [{"sku": "SHOE-RED-42", "quantity": 1, "unit_price": 89.99}]},
        )
        assert resp.status_code == 200
        assert all(item["available"] for item in resp.json()["items"])

        # Verify scenario 2
        resp = httpx.post(
            f"{mock_server.url}/inventory/check/out-of-stock",
            json={"items": [{"sku": "SHOE-RED-42", "quantity": 1, "unit_price": 89.99}]},
        )
        assert resp.status_code == 200
        assert not resp.json()["items"][0]["available"]

        # Verify scenario 3
        resp = httpx.post(
            f"{mock_server.url}/inventory/check/partial",
            json={
                "items": [
                    {"sku": "SHOE-RED-42", "quantity": 1, "unit_price": 89.99},
                    {"sku": "BELT-BRN-M", "quantity": 1, "unit_price": 44.98},
                ]
            },
        )
        assert resp.status_code == 200
        by_sku = {i["sku"]: i for i in resp.json()["items"]}
        assert by_sku["SHOE-RED-42"]["available"] is True
        assert by_sku["BELT-BRN-M"]["available"] is False

        # Verify scenario 4
        resp = httpx.post(
            f"{mock_server.url}/inventory/release/success",
            json={"order_id": "order-abc-123"},
        )
        assert resp.status_code == 200
        assert resp.json()["released"] is True

    pact.write_file(PACT_DIR, overwrite=True)
