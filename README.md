# Order Management API — Level 5 Engineer, [See Substack here](https://level5engineer.substack.com/p/the-level-5-engineer-the-map-i-didnt)

_Repo up to date with Issue #5_

## WireMock + Gherkin BDD + Pact contract testing demo project

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
│   │   ├── order_creation.feature       # Gherkin scenarios (the spec)
│   │   ├── order_status_bad.feature     # Deliberately bad specs (Issue #5)
│   │   └── order_status_good.feature    # Rewritten good specs (Issue #5)
│   ├── steps/
│   │   ├── test_order_creation.py       # pytest-bdd step definitions
│   │   ├── test_order_status_bad.py     # Steps for bad spec (Issue #5)
│   │   └── test_order_status_good.py    # Steps for good spec (Issue #5)
│   └── pact/
│       ├── test_payment_gateway_consumer.py   # Pact consumer tests (payment)
│       ├── test_inventory_service_consumer.py # Pact consumer tests (inventory)
│       └── test_provider_verification.py      # Pact provider verification
├── scripts/
│   └── can_i_deploy.py                  # Local can-i-deploy simulation
├── pacts/                               # Generated .pact files (gitignored)
├── findings/
│   ├── README.md                        # Index of all findings by issue
│   ├── issue-02-wiremock-gherkin.md     # Findings from Issue #2
│   ├── issue-03-agent-fresh-implementation.md  # Findings from Issue #3
│   ├── issue-04-pact-contract-testing.md       # Findings from Issue #4
│   └── issue-05-the-spec-that-doesnt-lie.md    # Findings from Issue #5
├── CLAUDE.md                            # Agent standing orders
└── pytest.ini
```

### Quick start (macOS)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full Gherkin test suite (uses the built-in Python mock server)
pytest tests/steps/test_order_creation.py -v

# 3. Run Pact consumer tests (generates pacts/ directory)
pytest tests/pact/test_payment_gateway_consumer.py tests/pact/test_inventory_service_consumer.py -v

# 4. Run Pact provider verification
pytest tests/pact/test_provider_verification.py -v -s

# 5. Run the local can-i-deploy check
python scripts/can_i_deploy.py
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

### Issue #5 — The spec that doesn't lie

Added `GET /orders/{order_id}/status` twice — once from a bad spec, once from a good
one — to demonstrate that passing tests are a necessary condition for a good spec,
not a sufficient one.

The session runs in six phases: write bad Gherkin, implement from it, document the
silent assumptions, rewrite the Gherkin properly, implement again from scratch, then
cross-run each implementation against the other's test suite.

The centrepiece finding is the field name divergence. The bad spec referenced `db_status`
(a storage-layer name). The agent used it literally. The good spec specified `status`
(the caller's concept). When the good implementation was run against the bad spec's
tests, the `db_status` test failed — `KeyError: 'db_status'` — because the field name
was never part of the observable contract; it was an implementation detail that leaked
into the spec. The 404 body shape produced a similar divergence: the bad spec left it
unspecified, so the agent chose FastAPI's default `{"detail": "..."}` structure; the
good spec mandated `{"error": "..."}`, which is what a client actually checks.

Both implementations passed their own test suites. Only cross-running revealed the gap.

The two-spec pattern: write the scenario, then ask "does this describe what the caller
sees, or what the implementation does?" If the answer is the implementation, rewrite it.

See [`findings/issue-05-the-spec-that-doesnt-lie.md`](findings/issue-05-the-spec-that-doesnt-lie.md)
for the full six-phase walkthrough including both implementations side by side.

### Issue #4 — Pact contract testing

Added Pact consumer tests for both downstream dependencies (payment gateway and
inventory service), provider verification tests that run those contracts against
the WireMock-compatible stubs, and a local `can-i-deploy` simulation.

The centrepiece of this session is a deliberate breaking change experiment:

1. All Pact provider verification tests pass.
2. In `wiremock/payment-mappings/payment-success.json`, the `status` field was
   renamed to `result`.
3. Pact provider verification immediately failed with an exact diff showing the
   missing `status` key.
4. The existing Gherkin test suite ran the same stubs and reported **5/5 passing**.
   The breaking change was invisible to WireMock-based tests.
5. Reverted the change; verification went green again.

The finding: WireMock tests verify that your code *behaves correctly given the stub
you wrote*. Pact verification proves that the stub *matches what the real service
actually returns*. Only the second check catches provider-side drift before production.

See [`findings/issue-04-pact-contract-testing.md`](findings/issue-04-pact-contract-testing.md)
for full terminal output from each step.

### Issue #3 — Fresh implementation from spec

`app/main.py` was rebuilt from scratch by a Claude Code agent using only the Gherkin
scenarios as the contract. See [`findings/issue-03-agent-fresh-implementation.md`](findings/issue-03-agent-fresh-implementation.md)
for a full breakdown of the behavioural contract derived from the spec, timeout/retry
reasoning, and a portability bug found and fixed in the original test harness.

### Findings log

Each newsletter issue has a corresponding findings file documenting what the agent
tried, what failed, the root causes, and why it matters. See [`findings/README.md`](findings/README.md)
for the full index.
