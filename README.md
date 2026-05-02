# Order Management API — Level 5 Engineer, [See Substack here](https://level5engineer.substack.com/p/the-level-5-engineer-the-map-i-didnt)

_Repo up to date with Issue #3_

## WireMock + Gherkin BDD demo project

### Project structure

```
order-api/
├── app/
│   └── main.py                          # FastAPI order service
├── mock_server.py                       # WireMock-compatible mock server
├── wiremock/
│   ├── payment-mappings/                # Stub definitions for payment gateway
│   │   ├── payment-success.json
│   │   ├── payment-declined.json
│   │   └── payment-timeout.json
│   └── inventory-mappings/              # Stub definitions for inventory service
│       ├── inventory-all-available.json
│       ├── inventory-out-of-stock.json
│       └── inventory-partial.json
├── tests/
│   ├── features/
│   │   └── order_creation.feature       # Gherkin scenarios (the spec)
│   └── steps/
│       └── test_order_creation.py       # pytest-bdd step definitions
├── findings/
│   ├── README.md                        # Index of all findings by issue
│   ├── issue-02-wiremock-gherkin.md     # Findings from Issue #2
│   └── issue-03-agent-fresh-implementation.md  # Findings from Issue #3
├── CLAUDE.md                            # Agent standing orders
└── pytest.ini
```

### Quick start (macOS)

```bash
# 1. Install dependencies
pip install fastapi uvicorn httpx pytest pytest-bdd requests

# 2. Run the full test suite (uses the built-in Python mock server — no Java required)
pytest tests/steps/test_order_creation.py -v
```

The test harness spins up the Python mock servers automatically on ports 8091/8092
and the FastAPI app on port 8093, so no manual setup is needed.

### Switching to real WireMock (optional)

The stub JSON files in `wiremock/payment-mappings/` and `wiremock/inventory-mappings/`
are standard WireMock mapping format. To use a real WireMock instance instead:

```bash
# Download: https://repo1.maven.org/maven2/org/wiremock/wiremock-standalone/3.3.1/wiremock-standalone-3.3.1.jar
java -jar wiremock.jar --port 8091 --root-dir wiremock/payment-mappings
java -jar wiremock.jar --port 8092 --root-dir wiremock/inventory-mappings
uvicorn app.main:app --port 8093
```

### The 5 Gherkin scenarios

1. Happy path — payment accepted, all items in stock → `CONFIRMED`
2. Payment declined → `PAYMENT_FAILED` (402), inventory released
3. Out of stock → `UNAVAILABLE` (409), payment gateway never called
4. Partial availability → `PARTIAL_UNAVAILABLE` (207), no auto-confirm, payment never called
5. Payment timeout → `PAYMENT_PENDING` (202), inventory held 15 mins, max 2 retry attempts

### Issue #3 — Fresh implementation from spec

`app/main.py` was rebuilt from scratch by a Claude Code agent using only the Gherkin
scenarios as the contract. See [`findings/issue-03-agent-fresh-implementation.md`](findings/issue-03-agent-fresh-implementation.md)
for a full breakdown of the behavioural contract derived from the spec, timeout/retry
reasoning, and a portability bug found and fixed in the original test harness.

### Findings log

Each newsletter issue has a corresponding findings file documenting what the agent
tried, what failed, the root causes, and why it matters. See [`findings/README.md`](findings/README.md)
for the full index.
