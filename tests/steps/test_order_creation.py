import time, threading, pytest, requests
from pytest_bdd import scenarios, given, when, then, parsers
import sys; sys.path.insert(0, "/home/claude/order-api")
from mock_server import start_mock_server

scenarios("../features/order_creation.feature")

PAYMENT_PORT   = 8091
INVENTORY_PORT = 8092
API_PORT       = 8093

payment_log   = None
inventory_log = None

@pytest.fixture(scope="session", autouse=True)
def start_servers():
    global payment_log, inventory_log
    import os, uvicorn
    _, payment_log   = start_mock_server(PAYMENT_PORT,   "/home/claude/order-api/wiremock/payment-mappings")
    _, inventory_log = start_mock_server(INVENTORY_PORT, "/home/claude/order-api/wiremock/inventory-mappings")

    os.environ["PAYMENT_URL"]             = f"http://localhost:{PAYMENT_PORT}"
    os.environ["INVENTORY_URL"]           = f"http://localhost:{INVENTORY_PORT}"
    os.environ["PAYMENT_TIMEOUT_SECONDS"] = "5"
    os.environ["MAX_PAYMENT_RETRIES"]     = "2"

    from app.main import app
    config = uvicorn.Config(app, host="127.0.0.1", port=API_PORT, log_level="error")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    time.sleep(1.5)
    yield
    server.should_exit = True

@pytest.fixture(autouse=True)
def reset_logs():
    yield
    payment_log.reset()
    inventory_log.reset()

@pytest.fixture
def payment_scenario(): return "success"   # default — overridden by specific Given steps

# ── Given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('a registered user with id "{user_id}"'), target_fixture="user_id")
def registered_user(user_id): return user_id

@given("the inventory service confirms all items are in stock", target_fixture="inventory_scenario")
def inv_all_available(): return "all-available"

@given("the payment gateway will accept the charge", target_fixture="payment_scenario")
def pay_success(): return "success"

@given("the payment gateway will decline the charge", target_fixture="payment_scenario")
def pay_declined(): return "declined"

@given("the inventory service reports SHOE-RED-42 is out of stock", target_fixture="inventory_scenario")
def inv_oos(): return "out-of-stock"

@given("the inventory service reports SHOE-RED-42 as available but BELT-BRN-M as unavailable",
       target_fixture="inventory_scenario")
def inv_partial(): return "partial"

@given("the payment gateway will not respond within the timeout window", target_fixture="payment_scenario")
def pay_timeout(): return "timeout"

# ── When ──────────────────────────────────────────────────────────────────────

def _post_order(user_id, payment_scenario, inventory_scenario, skus):
    t0 = time.time()
    items = [{"sku": s, "quantity": 1, "unit_price": 89.99 if "SHOE" in s else 44.98} for s in skus]
    r = requests.post(f"http://localhost:{API_PORT}/orders",
                      json={"user_id": user_id, "items": items,
                            "payment_scenario": payment_scenario,
                            "inventory_scenario": inventory_scenario}, timeout=20)
    return {"response": r, "elapsed": time.time() - t0}

@when("the user submits an order for SHOE-RED-42 and BELT-BRN-M", target_fixture="response")
def submit_two(user_id, payment_scenario, inventory_scenario):
    return _post_order(user_id, payment_scenario, inventory_scenario, ["SHOE-RED-42", "BELT-BRN-M"])

@when("the user submits an order for SHOE-RED-42", target_fixture="response")
def submit_one(user_id, payment_scenario, inventory_scenario):
    return _post_order(user_id, payment_scenario, inventory_scenario, ["SHOE-RED-42"])

# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse('the order status is "{expected}"'))
def check_status(response, expected):
    b = response["response"].json()
    assert b["status"] == expected, f"Expected {expected}, got {b['status']}\n{b}"

@then("the response includes an order id")
def has_order_id(response):
    b = response["response"].json()
    assert b.get("order_id"), f"No order_id in: {b}"

@then("no order id is issued")
def no_order_id(response):
    b = response["response"].json()
    assert not b.get("order_id"), f"Unexpected order_id: {b.get('order_id')}"

@then(parsers.parse("the response status code is {code:d}"))
def check_http_code(response, code):
    b = response["response"].json()
    assert b.get("status_code") == code, f"Expected {code}, got {b.get('status_code')}\n{b}"

@then(parsers.parse('the response includes the decline reason "{reason}"'))
def check_decline(response, reason):
    b = response["response"].json()
    assert b.get("decline_reason") == reason, f"Expected {reason}: {b}"

@then("the inventory reservation is released")
def inv_released(response):
    b = response["response"].json()
    assert b.get("inventory_released") is True, f"Expected inventory_released=True: {b}"

@then("the payment gateway received exactly one charge request")
def payment_called_once():
    calls = payment_log.all()
    pay_calls = [c for c in calls if c["path"].startswith("/payments/")]
    assert len(pay_calls) == 1, f"Expected 1 payment call, got {len(pay_calls)}: {calls}"

@then("the inventory service received a reservation request")
def inventory_called():
    calls = inventory_log.all()
    assert calls, f"Expected inventory to be called, got: {calls}"

@then("the payment gateway is never called")
def payment_not_called():
    calls = payment_log.all()
    assert not calls, f"Expected no payment calls, got: {calls}"

@then("the response identifies SHOE-RED-42 as unavailable")
def shoe_unavailable(response):
    b = response["response"].json()
    assert "SHOE-RED-42" in b.get("unavailable_items", []), f"{b}"

@then("SHOE-RED-42 is listed as available")
def shoe_available(response):
    b = response["response"].json()
    assert "SHOE-RED-42" in b.get("available_items", []), f"{b}"

@then("BELT-BRN-M is listed as unavailable")
def belt_unavailable(response):
    b = response["response"].json()
    assert "BELT-BRN-M" in b.get("unavailable_items", []), f"{b}"

@then("no order is confirmed without explicit user action")
def no_auto_confirm(response):
    b = response["response"].json()
    assert b.get("status") != "CONFIRMED", f"Should not be auto-confirmed: {b}"
    assert not b.get("order_id"), f"Should not have order_id: {b}"

@then(parsers.parse("the response is returned within {seconds:d} seconds"))
def check_response_time(response, seconds):
    assert response["elapsed"] < seconds, \
        f"Took {response['elapsed']:.1f}s, limit {seconds}s"

@then("the inventory is held for 15 minutes")
def inv_hold(response):
    b = response["response"].json()
    assert b.get("inventory_hold_minutes") == 15, f"{b}"

@then("the user is informed that payment confirmation is in progress")
def pending_message(response):
    b = response["response"].json()
    assert b.get("payment_pending") is True
    assert "progress" in b.get("message", "").lower(), f"{b}"

@then("the payment gateway is not retried more than 2 times")
def retry_cap(response):
    b = response["response"].json()
    assert b.get("retry_count", 0) <= 2, f"Too many retries: {b}"
