"""
Pact provider verification tests.

These tests verify that the WireMock-compatible stub servers (mock_server.py)
honour the contracts defined in pacts/. If a stub drifts from the consumer's
expectations, these tests fail before the code ever reaches production.

Run consumer tests first to regenerate pacts/:
    pytest tests/pact/test_payment_gateway_consumer.py
    pytest tests/pact/test_inventory_service_consumer.py
Then run this file:
    pytest tests/pact/test_provider_verification.py -v
"""
import sys
import threading
import time
from pathlib import Path

import pytest

from pact import Verifier

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mock_server import start_mock_server

PACT_DIR = Path(__file__).parent.parent.parent / "pacts"
PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def payment_mock_server():
    server, _ = start_mock_server(
        8291, str(PROJECT_ROOT / "wiremock" / "payment-mappings")
    )
    time.sleep(0.1)
    yield "http://localhost:8291"
    server.shutdown()


@pytest.fixture(scope="module")
def inventory_mock_server():
    server, _ = start_mock_server(
        8292, str(PROJECT_ROOT / "wiremock" / "inventory-mappings")
    )
    time.sleep(0.1)
    yield "http://localhost:8292"
    server.shutdown()


def test_payment_gateway_provider_verification(payment_mock_server: str):
    """Verify payment gateway stubs satisfy the OrderService consumer contract."""
    pact_file = PACT_DIR / "OrderService-PaymentGateway.json"
    assert pact_file.exists(), f"Pact file not found: {pact_file}. Run consumer tests first."

    verifier = (
        Verifier("PaymentGateway", "localhost")
        .add_transport(protocol="http", port=8291, scheme="http")
        .set_request_timeout(10000)  # ms — needed for the 6s delayed timeout stub
        .add_source(pact_file)
    )
    verifier.verify()


def test_inventory_service_provider_verification(inventory_mock_server: str):
    """Verify inventory service stubs satisfy the OrderService consumer contract."""
    pact_file = PACT_DIR / "OrderService-InventoryService.json"
    assert pact_file.exists(), f"Pact file not found: {pact_file}. Run consumer tests first."

    verifier = (
        Verifier("InventoryService", "localhost")
        .add_transport(protocol="http", port=8292, scheme="http")
        .add_source(pact_file)
    )
    verifier.verify()
