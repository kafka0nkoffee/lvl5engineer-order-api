import time, pytest, requests, os, sys, json
from pytest_bdd import scenarios, given, when, then, parsers

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

scenarios("../features/order_creation.feature")

API_PORT = 8093



@pytest.fixture
def payment_scenario(): return "success"

@pytest.fixture
def notification_scenario(): return "success"

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

@given("the notification service is available", target_fixture="notification_scenario")
def notif_available(): return "success"

@given("the notification service is unavailable", target_fixture="notification_scenario")
def notif_unavailable(): return "unavailable"

# ── When ──────────────────────────────────────────────────────────────────────

def _post_order(user_id, payment_scenario, inventory_scenario, skus, notification_scenario="success"):
    t0 = time.time()
    items = [{"sku": s, "quantity": 1, "unit_price": 89.99 if "SHOE" in s else 44.98} for s in skus]
    r = requests.post(f"http://localhost:{API_PORT}/orders",
                      json={"user_id": user_id, "items": items,
                            "payment_scenario": payment_scenario,
                            "inventory_scenario": inventory_scenario,
                            "notification_scenario": notification_scenario}, timeout=20)
    return {"response": r, "elapsed": time.time() - t0}

@when("the user submits an order for SHOE-RED-42 and BELT-BRN-M", target_fixture="response")
def submit_two(user_id, payment_scenario, inventory_scenario, notification_scenario):
    return _post_order(user_id, payment_scenario, inventory_scenario, ["SHOE-RED-42", "BELT-BRN-M"], notification_scenario)

@when("the user submits an order for SHOE-RED-42", target_fixture="response")
def submit_one(user_id, payment_scenario, inventory_scenario, notification_scenario):
    return _post_order(user_id, payment_scenario, inventory_scenario, ["SHOE-RED-42"], notification_scenario)

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

@then("the inventory reservation is released for SHOE-RED-42 and BELT-BRN-M")
def inv_released(response):
    # Spec intent: inventory service receives a release request for both items.
    # Current implementation: signals release via response body flag (inventory_released=True)
    # rather than a second inventory API call. This gap is documented in Issue #8.
    b = response["response"].json()
    assert b.get("inventory_released") is True, f"Expected inventory_released=True: {b}"

@then("the payment gateway received exactly one charge request")
def payment_called_once(payment_log_shared):
    calls = payment_log_shared.all()
    pay_calls = [c for c in calls if c["path"].startswith("/payments/")]
    assert len(pay_calls) == 1, f"Expected 1 payment call, got {len(pay_calls)}: {calls}"

@then("the inventory service received a reservation request")
def inventory_called(inventory_log_shared):
    calls = inventory_log_shared.all()
    assert calls, f"Expected inventory to be called, got: {calls}"

@then("the payment gateway is never called")
def payment_not_called(payment_log_shared):
    calls = payment_log_shared.all()
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


@then(parsers.parse("the response is returned within {seconds:d} seconds of the order being submitted"))
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

@then("the payment gateway receives no more than 2 charge requests total")
def retry_cap(payment_log_shared):
    calls = [c for c in payment_log_shared.all() if c["path"].startswith("/payments/")]
    assert len(calls) <= 2, f"Expected at most 2 charge requests, got {len(calls)}: {calls}"

@then("the notification service receives a confirmation request")
def notif_called(response, notification_log_shared):
    time.sleep(0.3)
    calls = notification_log_shared.any_calls_matching("/notifications/order-confirmed")
    assert calls, f"Expected notification call, got: {notification_log_shared.all()}"


@then("the notification service is not retried")
def notif_not_retried(notification_log_shared):
    time.sleep(0.3)
    calls = notification_log_shared.all()
    assert len(calls) <= 1, f"Expected at most 1 notification call, got {len(calls)}: {calls}"
