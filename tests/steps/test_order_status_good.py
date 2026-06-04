"""
Step definitions for order_status_good.feature.

These steps require no silent assumptions because the spec was explicit:
- The order ID is given, not generated
- The response field names are specified by the caller's contract, not the DB schema
- "ISO 8601 format" is a concrete assertion, not "non-empty string"
- The error field is a named contract obligation, not a side effect
"""
import pytest
from datetime import datetime
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient

from app.main import app, _orders

scenarios("../features/order_status_good.feature")

client = TestClient(app)
_response = {}


@given(parsers.parse('an order was successfully placed and confirmed with order ID "{order_id}"'))
def seed_confirmed_order_with_id(order_id):
    _orders[order_id] = {
        "db_status": "CONFIRMED",
        "order_created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


@given(parsers.parse('no order exists with ID "{order_id}"'))
def ensure_no_order(order_id):
    _orders.pop(order_id, None)


@when(parsers.parse('a client requests the status of order "{order_id}"'))
def request_order_status(order_id):
    _response["result"] = client.get(f"/orders/{order_id}/status")
    _response["order_id"] = order_id


@then(parsers.parse("the response HTTP status is {code:d}"))
def check_http_status(code):
    assert _response["result"].status_code == code


@then(parsers.parse('the response body contains a "{field}" field with value "{value}"'))
def check_field_value(field, value):
    body = _response["result"].json()
    assert field in body, f"Field '{field}' not found in response: {body}"
    assert str(body[field]) == value


@then(parsers.parse('the response body contains a "{field}" field in ISO 8601 format'))
def check_iso8601_field(field):
    body = _response["result"].json()
    assert field in body, f"Field '{field}' not found in response: {body}"
    value = body[field]
    # ISO 8601: must parse as a datetime
    try:
        datetime.fromisoformat(value)
    except (ValueError, TypeError):
        pytest.fail(f"Field '{field}' value '{value}' is not valid ISO 8601")


@then(parsers.parse('the response body contains an "{field}" field with value "{value}"'))
def check_named_field_value(field, value):
    body = _response["result"].json()
    assert field in body, f"Field '{field}' not found in response: {body}"
    assert str(body[field]) == value


@then(parsers.parse('the response body contains an "{field}" field'))
def check_field_present(field):
    body = _response["result"].json()
    assert field in body, f"Field '{field}' not found in response: {body}"
    assert body[field] is not None
