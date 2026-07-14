import time, pytest, requests, os, sys
from pytest_bdd import scenarios, given, when, then, parsers

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

scenarios("../features/order_cancellation.feature")

API_PORT          = 8093
INVENTORY_PORT    = 8092
NOTIFICATION_PORT = 8094


# ── Given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('a CONFIRMED order with id "{order_id}" exists'), target_fixture="order_id")
def confirmed_order(order_id):
    from app.main import _orders
    _orders[order_id] = {
        "db_status": "CONFIRMED",
        "order_created_at": "2026-07-14T00:00:00",
        "user_id": "user-cancel-test",
        "total": 89.99,
    }
    return order_id


@given(parsers.parse('a CANCELLED order with id "{order_id}" exists'), target_fixture="order_id")
def cancelled_order(order_id):
    from app.main import _orders
    _orders[order_id] = {
        "db_status": "CANCELLED",
        "order_created_at": "2026-07-14T00:00:00",
        "user_id": "user-cancel-test",
        "total": 89.99,
    }
    return order_id


@given(parsers.parse('a PAYMENT_PENDING order with id "{order_id}" exists'), target_fixture="order_id")
def payment_pending_order(order_id):
    from app.main import _orders
    _orders[order_id] = {
        "db_status": "PAYMENT_PENDING",
        "order_created_at": "2026-07-14T00:00:00",
    }
    return order_id


@given(parsers.parse('a PAYMENT_FAILED order with id "{order_id}" exists'), target_fixture="order_id")
def payment_failed_order(order_id):
    from app.main import _orders
    _orders[order_id] = {
        "db_status": "PAYMENT_FAILED",
        "order_created_at": "2026-07-14T00:00:00",
    }
    return order_id


@given("the inventory service will accept the reservation release", target_fixture="release_scenario")
def inv_release_success(): return "success"


# ── When ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def release_scenario(): return "success"

@pytest.fixture
def cancellation_notification_scenario(): return "success"


@when(parsers.parse('the user cancels order "{order_id}"'), target_fixture="response")
def cancel_order(order_id, release_scenario, cancellation_notification_scenario):
    t0 = time.time()
    r = requests.delete(
        f"http://localhost:{API_PORT}/orders/{order_id}",
        params={
            "release_scenario": release_scenario,
            "cancellation_notification_scenario": cancellation_notification_scenario,
        },
        timeout=10,
    )
    return {"response": r, "elapsed": time.time() - t0}


# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse('the response includes the order id "{expected_id}"'))
def has_specific_order_id(response, expected_id):
    b = response["response"].json()
    assert b.get("order_id") == expected_id, \
        f"Expected order_id={expected_id}, got {b.get('order_id')}\n{b}"


@then("the inventory service receives exactly 1 reservation release request")
def inv_release_called_once(inventory_log_shared):
    calls = [c for c in inventory_log_shared.all() if "/inventory/release/" in c["path"]]
    assert len(calls) == 1, \
        f"Expected exactly 1 inventory release call, got {len(calls)}: {inventory_log_shared.all()}"


@then("the inventory service receives no reservation release requests")
def inv_release_not_called(inventory_log_shared):
    calls = [c for c in inventory_log_shared.all() if "/inventory/release/" in c["path"]]
    assert len(calls) == 0, \
        f"Expected 0 inventory release calls, got {len(calls)}: {inventory_log_shared.all()}"


@then("the notification service receives exactly 1 cancellation notification")
def notif_cancellation_called_once(notification_log_shared):
    time.sleep(0.3)
    calls = notification_log_shared.any_calls_matching("/notifications/")
    assert len(calls) == 1, \
        f"Expected exactly 1 cancellation notification, got {len(calls)}: {notification_log_shared.all()}"


@then("the notification service receives no cancellation notifications")
def notif_cancellation_not_called(notification_log_shared):
    time.sleep(0.3)
    calls = notification_log_shared.any_calls_matching("/notifications/")
    assert len(calls) == 0, \
        f"Expected 0 cancellation notifications, got {len(calls)}: {notification_log_shared.all()}"


@then(parsers.parse('the response body contains an error field with value "{expected_error}"'))
def check_error_body(response, expected_error):
    b = response["response"].json()
    assert b.get("error") == expected_error, \
        f"Expected error={expected_error!r}, got {b.get('error')!r}\n{b}"
