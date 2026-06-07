"""
Session-scoped fixtures shared across all step definition files.
Starts mock servers and the order API once per pytest session.
"""
import os, sys, time, threading
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
from mock_server import start_mock_server

PAYMENT_PORT      = 8091
INVENTORY_PORT    = 8092
API_PORT          = 8093
NOTIFICATION_PORT = 8094


@pytest.fixture(scope="session")
def payment_log_shared():
    _, log = start_mock_server(PAYMENT_PORT, os.path.join(PROJECT_ROOT, "wiremock/payment-mappings"))
    return log


@pytest.fixture(scope="session")
def inventory_log_shared():
    _, log = start_mock_server(INVENTORY_PORT, os.path.join(PROJECT_ROOT, "wiremock/inventory-mappings"))
    return log


@pytest.fixture(scope="session")
def notification_log_shared():
    _, log = start_mock_server(NOTIFICATION_PORT, os.path.join(PROJECT_ROOT, "wiremock/notification-mappings"))
    return log


@pytest.fixture(scope="session", autouse=True)
def start_all_servers(payment_log_shared, inventory_log_shared, notification_log_shared):
    import uvicorn
    os.environ["PAYMENT_URL"]             = f"http://localhost:{PAYMENT_PORT}"
    os.environ["INVENTORY_URL"]           = f"http://localhost:{INVENTORY_PORT}"
    os.environ["NOTIFICATION_URL"]        = f"http://localhost:{NOTIFICATION_PORT}"
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
def reset_all_logs(payment_log_shared, inventory_log_shared, notification_log_shared):
    yield
    payment_log_shared.reset()
    inventory_log_shared.reset()
    notification_log_shared.reset()
