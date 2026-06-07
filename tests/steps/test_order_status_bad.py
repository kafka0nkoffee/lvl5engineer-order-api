"""
Step definitions for order_status_bad.feature.

These steps are written to satisfy the bad Gherkin scenarios exactly as written.
Note how step definitions must make concrete choices that the spec never stated:
- The confirmed order is seeded directly into the app's in-memory store
- "an order that has not been placed" is interpreted as "no entry in the store"
- The timestamp field name matches "order_created_at" from the spec
"""
import pytest
import threading
from datetime import datetime
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient

from app.main import app, _orders

scenarios("../features/order_status_bad.feature")

client = TestClient(app)
_response = {}
_test_order_id = "test-order-confirmed-001"


@given(parsers.parse('an order has been created and its db_status is "{status}"'))
def seed_confirmed_order(status):
    _orders[_test_order_id] = {
        "db_status": status,
        "order_created_at": datetime.utcnow().isoformat(),
    }


@given("an order that has not been placed")
def no_order_placed():
    # Silent assumption: "not been placed" means the order_id simply doesn't exist
    # in the store. We take no action — the store has no entry for this ID.
    pass


@when("the client calls GET /orders/{order_id}/status")
def get_confirmed_order_status():
    _response["result"] = client.get(f"/orders/{_test_order_id}/status")


@when("the client calls GET /orders/nonexistent-id/status")
def get_nonexistent_order_status():
    _response["result"] = client.get("/orders/nonexistent-id/status")


@then(parsers.parse("the response status code should be {code:d}"))
def check_status_code(code):
    assert _response["result"].status_code == code


@then(parsers.parse('the response should contain the db_status field set to "{expected}"'))
def check_db_status(expected):
    body = _response["result"].json()
    assert body["db_status"] == expected


@then("the order_created_at timestamp is a non-empty string")
def check_created_at():
    body = _response["result"].json()
    assert "order_created_at" in body, f"Field 'order_created_at' not found: {body}"
    assert isinstance(body["order_created_at"], str), f"Expected string, got: {type(body['order_created_at'])}"
    assert len(body["order_created_at"]) > 0, "order_created_at is empty"
