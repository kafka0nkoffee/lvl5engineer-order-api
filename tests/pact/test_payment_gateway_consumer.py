"""
Pact consumer tests for the order service → payment gateway interaction.

pact-python v3 (FFI-backed) requires ALL interactions to be added to a Pact
handle BEFORE calling serve(). Once serve() is called the Rust handle is
consumed and new interactions cannot be added to it. All scenarios are therefore
defined inside a single test that starts the mock once, exercises every
interaction in sequence, then writes the .pact file.
"""
from pathlib import Path

import httpx

from pact import Pact

PACT_DIR = Path(__file__).parent.parent.parent / "pacts"
PACT_DIR.mkdir(exist_ok=True)


def test_payment_gateway_consumer_contract():
    """
    Defines and verifies all payment gateway interactions in one pass.

    Scenarios covered:
    - Successful charge → 200 ACCEPTED
    - Declined charge → 402 DECLINED / INSUFFICIENT_FUNDS
    - Gateway timeout → 504 TIMEOUT
    """
    pact = Pact("OrderService", "PaymentGateway")

    # Scenario 1: successful charge
    (
        pact.upon_receiving("a successful payment charge")
        .given("the payment gateway will accept the charge")
        .with_request("POST", "/payments/charge/success")
        .with_body(
            {"user_id": "user-123", "items": []},
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(
            {"status": "ACCEPTED", "transaction_id": "txn-abc-123", "amount": 134.97},
            content_type="application/json",
        )
    )

    # Scenario 2: declined charge
    (
        pact.upon_receiving("a declined payment charge")
        .given("the payment gateway will decline the charge")
        .with_request("POST", "/payments/charge/declined")
        .with_body(
            {"user_id": "user-456", "items": []},
            content_type="application/json",
        )
        .will_respond_with(402)
        .with_body(
            {"status": "DECLINED", "reason": "INSUFFICIENT_FUNDS"},
            content_type="application/json",
        )
    )

    # Scenario 3: gateway timeout (the provider stubs this as 504 with a delay;
    # the order service catches httpx.TimeoutException before the 504 is returned,
    # but the contract still documents what the gateway would send if reached)
    (
        pact.upon_receiving("a timed-out payment charge")
        .given("the payment gateway will not respond within the timeout window")
        .with_request("POST", "/payments/charge/timeout")
        .with_body(
            {"user_id": "user-654", "items": []},
            content_type="application/json",
        )
        .will_respond_with(504)
        .with_body(
            {"status": "TIMEOUT"},
            content_type="application/json",
        )
    )

    with pact.serve() as mock_server:
        # Verify scenario 1
        resp = httpx.post(
            f"{mock_server.url}/payments/charge/success",
            json={"user_id": "user-123", "items": []},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ACCEPTED"
        assert "transaction_id" in body

        # Verify scenario 2
        resp = httpx.post(
            f"{mock_server.url}/payments/charge/declined",
            json={"user_id": "user-456", "items": []},
        )
        assert resp.status_code == 402
        body = resp.json()
        assert body["status"] == "DECLINED"
        assert body["reason"] == "INSUFFICIENT_FUNDS"

        # Verify scenario 3
        resp = httpx.post(
            f"{mock_server.url}/payments/charge/timeout",
            json={"user_id": "user-654", "items": []},
        )
        assert resp.status_code == 504
        assert resp.json()["status"] == "TIMEOUT"

    pact.write_file(PACT_DIR, overwrite=True)
