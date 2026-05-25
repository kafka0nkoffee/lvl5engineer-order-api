#!/usr/bin/env python3
"""
Local can-i-deploy simulation.

Reads generated pact files from pacts/ and verifies that every interaction
in each pact has a corresponding stub in the WireMock mapping directories.
Exits 0 if all contracts are covered, 1 if any are missing or broken.

Usage:
    python scripts/can_i_deploy.py

This simulates the can-i-deploy gate that would block a merge in a real
CI/CD pipeline (e.g., via Pact Broker). The GitHub Actions wiring comes
in Issue #6.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PACTS_DIR = ROOT / "pacts"
PAYMENT_MAPPINGS = ROOT / "wiremock" / "payment-mappings"
INVENTORY_MAPPINGS = ROOT / "wiremock" / "inventory-mappings"

PROVIDER_MAPPING_DIRS = {
    "PaymentGateway": PAYMENT_MAPPINGS,
    "InventoryService": INVENTORY_MAPPINGS,
}


def load_stubs(mappings_dir: Path) -> list[dict]:
    """Load all WireMock JSON stub files from a directory."""
    return [json.loads(f.read_text()) for f in mappings_dir.glob("*.json")]


def stub_covers_interaction(stubs: list[dict], interaction: dict) -> bool:
    """Return True if any stub matches the interaction's request path and method."""
    req = interaction.get("request", {})
    method = req.get("method", "POST")
    path = req.get("path", "")

    for stub in stubs:
        stub_req = stub.get("request", {})
        if stub_req.get("method") == method and stub_req.get("url") == path:
            return True
    return False


def check_response_body(stubs: list[dict], interaction: dict) -> tuple[bool, str]:
    """
    Verify that the matching stub's response body contains all fields
    the consumer expects. Returns (ok, detail_message).
    """
    req = interaction.get("request", {})
    resp = interaction.get("response", {})
    method = req.get("method", "POST")
    path = req.get("path", "")
    expected_body = resp.get("body", {}).get("content", {})

    for stub in stubs:
        stub_req = stub.get("request", {})
        if stub_req.get("method") != method or stub_req.get("url") != path:
            continue

        stub_body_raw = stub.get("response", {}).get("body", "{}")
        try:
            stub_body = json.loads(stub_body_raw) if isinstance(stub_body_raw, str) else stub_body_raw
        except json.JSONDecodeError:
            return False, f"stub body is not valid JSON: {stub_body_raw!r}"

        missing = [k for k in expected_body if k not in stub_body]
        if missing:
            return False, f"stub is missing fields expected by consumer: {missing}"

        mismatched = []
        for k, v in expected_body.items():
            if stub_body.get(k) != v:
                mismatched.append(f"{k}: expected={v!r}, actual={stub_body.get(k)!r}")
        if mismatched:
            return False, "field value mismatch — " + "; ".join(mismatched)

        return True, "OK"

    return False, f"no stub matched {method} {path}"


def main() -> int:
    if not PACTS_DIR.exists() or not any(PACTS_DIR.glob("*.json")):
        print("ERROR: No pact files found in pacts/. Run consumer tests first.")
        print("       pytest tests/pact/test_payment_gateway_consumer.py")
        print("       pytest tests/pact/test_inventory_service_consumer.py")
        return 1

    all_passed = True

    for pact_file in sorted(PACTS_DIR.glob("*.json")):
        pact = json.loads(pact_file.read_text())
        consumer = pact["consumer"]["name"]
        provider = pact["provider"]["name"]
        interactions = pact.get("interactions", [])

        print(f"\n{'='*60}")
        print(f"Pact: {consumer} → {provider}")
        print(f"File: {pact_file.name}")
        print(f"Interactions: {len(interactions)}")
        print(f"{'='*60}")

        mappings_dir = PROVIDER_MAPPING_DIRS.get(provider)
        if not mappings_dir:
            print(f"  SKIP — no mapping dir registered for provider '{provider}'")
            continue

        stubs = load_stubs(mappings_dir)

        for interaction in interactions:
            description = interaction.get("description", "(no description)")
            states = [s["name"] for s in interaction.get("providerStates", [])]
            state_str = f" [{states[0]}]" if states else ""

            if not stub_covers_interaction(stubs, interaction):
                print(f"  FAIL  {description}{state_str}")
                print(f"        No stub matches this interaction's request")
                all_passed = False
                continue

            ok, detail = check_response_body(stubs, interaction)
            if ok:
                print(f"  PASS  {description}{state_str}")
            else:
                print(f"  FAIL  {description}{state_str}")
                print(f"        {detail}")
                all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("RESULT: ALL CONTRACTS VERIFIED — safe to deploy")
        print(f"{'='*60}")
        return 0
    else:
        print("RESULT: CONTRACT VIOLATIONS DETECTED — do not deploy")
        print(f"{'='*60}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
