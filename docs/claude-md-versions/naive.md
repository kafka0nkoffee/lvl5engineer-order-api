---
type: Reference
title: "CLAUDE.md — Naive Version"
description: "Pedagogical example of the CLAUDE.md most projects start with on day one, before operational experience shapes the failure modes."
tags: [reference, claude-md, pedagogical, issue-15]
timestamp: 2026-07-05
---

# CLAUDE.md — Naive version

> Reference document for Issue #15 newsletter article.
> This is the version most projects have on day one — the CLAUDE.md a competent engineer
> writes before operational experience teaches them what the failure modes are.
> It is NOT the active CLAUDE.md. See the root CLAUDE.md for the production-grade version.

---

## What this project is

An order management REST API built with FastAPI. It integrates with a payment gateway
and an inventory service to process customer orders. The API handles five order scenarios:
successful orders, payment failures, out-of-stock, partial availability, and payment timeouts.

---

## Directory structure

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
│   ├── features/                # Gherkin scenarios
│   ├── steps/                   # pytest-bdd step definitions
│   └── pact/                    # Pact contract tests
├── scripts/
│   └── can_i_deploy.py          # Local can-i-deploy check
└── .github/workflows/ci.yml     # GitHub Actions pipeline
```

---

## Running the tests

```bash
pip install -r requirements.txt

# Gherkin scenarios
pytest tests/steps/ -v

# Pact contract tests
pytest tests/pact/ -v

# Can-i-deploy check
python3 scripts/can_i_deploy.py
```

All tests must pass before committing.

---

## External services

The order API integrates with three external services simulated by the Python mock server:

| Service | Port | Stub directory |
|---|---|---|
| Payment gateway | 8091 | wiremock/payment-mappings/ |
| Inventory service | 8092 | wiremock/inventory-mappings/ |
| Notification service | 8094 | wiremock/notification-mappings/ |

The mock servers are started automatically by the test fixtures. Do not make real HTTP calls
to external services during testing.

---

## Do not modify

- `tests/features/*.feature` — these are the external behavioral spec written by the human
- `requirements.txt` — update only if you are adding a new dependency, document in commit message

---

## Commit conventions

```
feat: add new functionality
fix: correct broken behaviour
test: new or updated test
docs: documentation only
chore: maintenance
```

Use the imperative present tense: "add" not "added", "fix" not "fixed."

---

## What you can modify

- `app/main.py` and `app/notification_service.py`
- `mock_server.py`
- Stub files in `wiremock/`
- Step definitions in `tests/steps/`
- New source files in `app/`
- `requirements.txt` (with documentation)
