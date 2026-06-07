import time, pytest, requests, os, sys, json
from pytest_bdd import scenarios, given, when, then, parsers

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

scenarios("../features/notification_service.feature")

NOTIFICATION_PORT = 8094
API_PORT          = 8093



@pytest.fixture
def notification_scenario(): return "success"

# ── Given ─────────────────────────────────────────────────────────────────────

@given("the notification service is healthy")
def notif_healthy(): pass

@given(parsers.parse('a registered user with id "{user_id}"'), target_fixture="user_id")
def registered_user_notif(user_id): return user_id

@given("the inventory service confirms all items are in stock", target_fixture="inventory_scenario")
def inv_all_available_notif(): return "all-available"

@given("the payment gateway will accept the charge", target_fixture="payment_scenario")
def pay_success_notif(): return "success"

@given("the notification service will respond with 503 Service Unavailable", target_fixture="notification_scenario")
def notif_unavailable_503(): return "unavailable"

# ── When ──────────────────────────────────────────────────────────────────────

@when(
    parsers.parse('the order service sends a confirmed order notification for order "{order_id}" with total {total:f} for user "{user_id}"'),
    target_fixture="notif_response",
)
def send_notification_directly(order_id, total, user_id):
    r = requests.post(
        f"http://localhost:{NOTIFICATION_PORT}/notifications/order-confirmed",
        json={"order_id": order_id, "user_id": user_id, "total": total},
        timeout=5,
    )
    return r

@when("the user submits an order for SHOE-RED-42 and BELT-BRN-M", target_fixture="response")
def submit_two_notif(user_id, payment_scenario, inventory_scenario, notification_scenario):
    t0 = time.time()
    items = [
        {"sku": "SHOE-RED-42", "quantity": 1, "unit_price": 89.99},
        {"sku": "BELT-BRN-M",  "quantity": 1, "unit_price": 44.98},
    ]
    r = requests.post(
        f"http://localhost:{API_PORT}/orders",
        json={
            "user_id": user_id,
            "items": items,
            "payment_scenario": payment_scenario,
            "inventory_scenario": inventory_scenario,
            "notification_scenario": notification_scenario,
        },
        timeout=20,
    )
    return {"response": r, "elapsed": time.time() - t0}

# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse("the notification service returns status {code:d}"))
def notif_status_code(notif_response, code):
    assert notif_response.status_code == code, f"Expected {code}, got {notif_response.status_code}"

@then("the response body contains a notification_id in UUID format")
def notif_has_id(notif_response):
    import re
    body = notif_response.json()
    nid = body.get("notification_id", "")
    assert nid, f"No notification_id in: {body}"
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    assert re.match(uuid_pattern, nid, re.IGNORECASE), f"notification_id '{nid}' is not a valid UUID"

@then(parsers.parse('the response body contains status "{expected}"'))
def notif_has_status(notif_response, expected):
    body = notif_response.json()
    assert body.get("status") == expected, f"Expected status={expected}, got: {body}"

@then(parsers.parse('the order status is "{expected}"'))
def check_order_status_notif(response, expected):
    b = response["response"].json()
    assert b["status"] == expected, f"Expected {expected}, got {b['status']}\n{b}"

@then("the notification endpoint receives at most one request")
def notif_at_most_once(notification_log_shared):
    time.sleep(0.3)
    calls = notification_log_shared.all()
    assert len(calls) <= 1, f"Expected at most 1 call, got {len(calls)}: {calls}"
