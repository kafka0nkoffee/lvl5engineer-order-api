# Order Management API — Level 5 Engineer, [See Substack here](https://level5engineer.substack.com/p/the-level-5-engineer-the-map-i-didnt)
_Repo up to date with Issue #2_
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
│   └── inventory-mappings/             # Stub definitions for inventory service
│       ├── inventory-all-available.json
│       ├── inventory-out-of-stock.json
│       └── inventory-partial.json
├── tests/
│   ├── features/
│   │   └── order_creation.feature      # Gherkin scenarios (the spec)
│   └── steps/
│       └── test_order_creation.py      # pytest-bdd step definitions
└── pytest.ini
```

### Quick start (macOS)
```bash
# 1. Install dependencies
pip install fastapi uvicorn httpx pytest pytest-bdd requests

# 2. For real WireMock (Java required):
#    Download: https://repo1.maven.org/maven2/org/wiremock/wiremock-standalone/3.3.1/wiremock-standalone-3.3.1.jar
#    Run payment mock:   java -jar wiremock.jar --port 8081 --root-dir wiremock/payment-mappings
#    Run inventory mock: java -jar wiremock.jar --port 8082 --root-dir wiremock/inventory-mappings
#    Run API:            uvicorn app.main:app --port 8090
#
#    OR use the built-in Python mock server (no Java needed) — the tests use this by default.

# 3. Run the full test suite
pytest tests/steps/test_order_creation.py -v
```

### Switching to real WireMock
The stub JSON files in `wiremock/payment-mappings/` and `wiremock/inventory-mappings/`
are 100% real WireMock mapping format. Drop them into a running WireMock instance
and they work with zero changes.

### The 5 Gherkin scenarios
1. Happy path — payment accepted, all items in stock → CONFIRMED
2. Payment declined → PAYMENT_FAILED, inventory released
3. Out of stock → UNAVAILABLE, payment gateway never called
4. Partial availability → PARTIAL_UNAVAILABLE, no auto-confirm, payment never called
5. Payment timeout → PAYMENT_PENDING (202), inventory held 15 mins, max 2 retries
