# CLAUDE.md — Better version

> Reference document for Issue #15 newsletter article.
> This is the version most thoughtful engineers write after reading CLAUDE.md best practices —
> it adds permissions modeling, architectural decision references, and service descriptions.
> It is NOT the active CLAUDE.md. See the root CLAUDE.md for the production-grade version.

---

## What this project is

An order management REST API (FastAPI, port 8093) that integrates with a payment gateway
and an inventory service to process customer orders. The five core scenarios are defined in
`tests/features/order_creation.feature` — these scenarios are the authoritative spec for
all order creation behavior.

This service owns the order creation and order status flows. It does not own payment
processing logic or inventory management — it calls those services but does not control them.

---

## Architecture overview

```
order-api/
├── app/
│   ├── main.py                  # FastAPI order service
│   └── notification_service.py  # Notification endpoint
├── mock_server.py               # WireMock-compatible mock server
├── wiremock/
│   ├── payment-mappings/        # Payment gateway stubs
│   ├── inventory-mappings/      # Inventory service stubs
│   └── notification-mappings/   # Notification service stubs
├── tests/
│   ├── features/                # Gherkin scenarios — the external spec
│   ├── steps/                   # pytest-bdd step definitions
│   └── pact/                    # Pact contract tests
├── scripts/
│   └── can_i_deploy.py          # Local can-i-deploy check
└── .github/workflows/ci.yml     # GitHub Actions pipeline (four jobs)
```

---

## Permissions model

### May modify freely
- `app/main.py` and `app/notification_service.py`
- `mock_server.py`
- Step definitions in `tests/steps/`
- New source files in `app/`
- New stub files in `wiremock/`
- New Pact test files in `tests/pact/`

### May modify with care
- Existing stub files in `wiremock/` — run the full Pact test suite after any stub change to
  confirm the consumer contract is not broken. The Pact consumer tests define which response
  fields are load-bearing.
- `requirements.txt` — update only when adding a new dependency; document the dependency and
  its purpose in the commit message.
- `.github/workflows/ci.yml` — the four-job pipeline (test → pact-consumer → pact-verify →
  can-i-deploy) is a required merge gate. Modify only if you understand the full dependency
  chain between jobs. Any change that weakens the gate requires explicit justification.

### May not modify
- `tests/features/*.feature` — these are the external behavioral spec written by the human.
  The agent's job is to satisfy them, not rewrite them.
- `CLAUDE.md` — do not modify unless explicitly instructed.

---

## Key architectural decisions

Before modifying the order creation flow in `app/main.py`, check whether your change
affects any of the five Gherkin scenarios in `tests/features/order_creation.feature`.
The scenarios are the authoritative contract for order creation behavior.

Before modifying the notification flow, note: the notification service call is currently
implemented as fire-and-forget. The order service does not wait for notification delivery
before returning the order confirmation. This is the current implementation.

Before modifying stub response shapes in `wiremock/`, run the Pact consumer tests first:
```bash
pytest tests/pact/test_payment_gateway_consumer.py tests/pact/test_inventory_service_consumer.py -v
```
If the Pact consumer tests fail after a stub change, the stub must be reverted.

---

## External services

| Service | Port | What it does |
|---|---|---|
| Payment gateway | 8091 | Processes charge requests; returns ACCEPTED, DECLINED, or times out |
| Inventory service | 8092 | Checks item availability; returns ALL_AVAILABLE, OUT_OF_STOCK, or PARTIAL |
| Notification service | 8094 | Receives order confirmation events; fire-and-forget |

The Pact consumer tests in `tests/pact/` define the exact response shapes the order service
expects from the payment gateway and inventory service. Do not change stub response shapes
without running the Pact suite first.

---

## Running the tests

```bash
pip install -r requirements.txt

# Gherkin scenarios — all 11 must pass
pytest tests/steps/ -v

# Pact consumer and provider tests — all 4 must pass
pytest tests/pact/ -v

# Can-i-deploy check
python3 scripts/can_i_deploy.py
```

All 15 tests must pass before any session is considered complete.

---

## Commit conventions

```
feat: add new functionality
fix: correct broken behaviour
test: new or updated test
docs: documentation only
chore: maintenance
refactor: implementation change with no functional change
```

Format: `{type}: {imperative description} — Issue #{N}`

Use the imperative present tense. Include the issue number suffix.
