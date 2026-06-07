# Order Management API — Level 5 Engineer, [See Substack here](https://level5engineer.substack.com/)

![CI](https://github.com/kafka0nkoffee/lvl5engineer-order-api/actions/workflows/ci.yml/badge.svg)

_Repo up to date with Issue #8_

## WireMock + Gherkin BDD + Pact contract testing demo project

### Project structure

```
order-api/
├── app/
│   ├── main.py                          # FastAPI order service
│   └── notification_service.py          # Notification endpoint (Issue #7)
├── mock_server.py                       # WireMock-compatible mock server
├── wiremock/
│   ├── payment-mappings/                # Stub definitions for payment gateway
│   │   ├── payment-success.json
│   │   ├── payment-declined.json
│   │   └── payment-timeout.json
│   ├── inventory-mappings/              # Stub definitions for inventory service
│   │   ├── inventory-all-available.json
│   │   ├── inventory-out-of-stock.json
│   │   └── inventory-partial.json
│   └── notification-mappings/           # Stub definitions for notification service (Issue #7)
│       ├── notification-success.json
│       └── notification-unavailable.json
├── tests/
│   ├── features/
│   │   ├── order_creation.feature       # Gherkin scenarios — order creation only
│   │   ├── order_status_bad.feature     # Deliberately bad specs (Issue #5)
│   │   ├── order_status_good.feature    # Rewritten good specs (Issue #5)
│   │   └── notification_service.feature # Bounded notification spec (Issue #7)
│   ├── steps/
│   │   ├── conftest.py                  # Shared session-scoped server fixtures
│   │   ├── test_order_creation.py       # pytest-bdd step definitions
│   │   ├── test_order_status_bad.py     # Steps for bad spec (Issue #5)
│   │   ├── test_order_status_good.py    # Steps for good spec (Issue #5)
│   │   └── test_notification_service.py # Steps for notification spec (Issue #7)
│   └── pact/
│       ├── test_payment_gateway_consumer.py   # Pact consumer tests (payment)
│       ├── test_inventory_service_consumer.py # Pact consumer tests (inventory)
│       └── test_provider_verification.py      # Pact provider verification
├── scripts/
│   └── can_i_deploy.py                  # Local can-i-deploy simulation
├── pacts/                               # Generated .pact files (gitignored)
├── .github/
│   └── workflows/
│       └── ci.yml                       # GitHub Actions pipeline (Issue #6)
├── findings/
│   ├── README.md                        # Index of all findings by issue
│   ├── issue-02-wiremock-gherkin.md     # Findings from Issue #2
│   ├── issue-03-agent-fresh-implementation.md  # Findings from Issue #3
│   ├── issue-04-pact-contract-testing.md       # Findings from Issue #4
│   ├── issue-05-the-spec-that-doesnt-lie.md    # Findings from Issue #5
│   ├── issue-06-cicd-guardrails.md             # Findings from Issue #6
│   ├── issue-07-scope-problem.md               # Findings from Issue #7
│   └── issue-08-spec-audit.md                  # Findings from Issue #8
├── docs/
│   └── spec-audit-framework.md          # Paid-tier deliverable: spec audit framework
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

### Issue #8 — Spec audit: fixing debt and the framework

Fixed all seven spec debt items identified in Issue #7. Each fix was applied individually with tests run after each change. The seven fixes:

1. Timeout step anchored to client submission time: `"within 12 seconds of the order being submitted"`
2. Retry count made unambiguous: `"no more than 2 charge requests total"` (verifies mock call count, not response body field)
3. Inventory release step names the items explicitly: `"released for SHOE-RED-42 and BELT-BRN-M"`
4. Removed `"no order is confirmed without explicit user action"` — the confirmation flow it implies does not exist; the step was passing trivially
5. `order_status_bad.feature` timestamp step made explicit: `"the order_created_at timestamp is a non-empty string"`
6. `order_status_good.feature` Given specifies mechanism: `"created via POST /orders and confirmed with..."`
7. `notification_service.feature` notification_id checked for UUID format, not just presence — which caught a stub returning `"mock-notif-001"` (not a UUID) that had never been validated

The session also produced `docs/spec-audit-framework.md` — a standalone tool for auditing any feature file. It includes five diagnostic questions, a six-class debt taxonomy (UNDERSPECIFIED, MIXED CONCERN, UNDEFINED TERM, AMBIGUOUS COUNT, IMPLICIT FLOW, LEAKY ABSTRACTION), a fix rubric for each class, and a scorecard template. The framework was applied to all four feature files after the fixes; two debt items remain, both LEAKY ABSTRACTION at the step definition level rather than the feature file level.

The closing finding: in a project built carefully for eight issues, the residual debt density is 0.22 items per scenario — and both remaining items are documented gaps, not silent ones. The key distinction between manageable and dangerous spec debt is not quantity but visibility.

See [`findings/issue-08-spec-audit.md`](findings/issue-08-spec-audit.md) and [`docs/spec-audit-framework.md`](docs/spec-audit-framework.md).

### The 5 Gherkin scenarios

1. Happy path — payment accepted, all items in stock → `CONFIRMED`
2. Payment declined → `PAYMENT_FAILED` (402), inventory released
3. Out of stock → `UNAVAILABLE` (409), payment gateway never called
4. Partial availability → `PARTIAL_UNAVAILABLE` (207), no auto-confirm, payment never called
5. Payment timeout → `PAYMENT_PENDING` (202), inventory held 15 mins, max 2 retry attempts

### Issue #7 — The scope problem: spec files at service boundaries

Added a minimal notification service (`app/notification_service.py`, `POST /notifications/order-confirmed`) and wired the order service to call it after a confirmed payment — fire-and-forget, so notification failure never blocks order confirmation. Then deliberately demonstrated what goes wrong when notification scenarios are added to `order_creation.feature`, documented the four structural problems that emerge (mixed ownership, growing file, agent routing confusion, spec debt seed), and fixed them by creating a bounded `notification_service.feature`.

The session includes a full spec debt audit across all four feature files. Seven specific debt items are named and documented — not fixed, because the point is to show that spec debt forms in passing tests. The most striking item: `"the payment gateway is not retried more than 2 times"` is genuinely ambiguous about whether "2 times" means 2 total requests or 1 attempt + 2 retries. It has been in the codebase since Issue #2. It has passed every run. Every agent that reimplements from that step will resolve the ambiguity differently.

The session also surfaced a real infrastructure problem: when running `pytest tests/steps/` across multiple step files in the same process, each file's session fixture tried to bind the same ports. Fixed by moving server startup to `tests/steps/conftest.py` as shared session-scoped fixtures — a pattern that generalises cleanly as the test surface grows.

Final state: 11 Gherkin tests passing, 4 Pact tests passing, all contracts verified.

See [`findings/issue-07-scope-problem.md`](findings/issue-07-scope-problem.md) for the full session, including the spec debt audit.

### Issue #6 — CI/CD guardrails

Wired the full test suite into a four-job GitHub Actions pipeline: `test` (Gherkin) →
`pact-consumer` → `pact-verify` → `can-i-deploy`. Each job is a dependency of the next,
so a failing Gherkin suite skips Pact, and a broken consumer contract skips provider
verification. The pipeline runs on every push to any branch and every pull request to main.

The session included a deliberate breaking change test: renamed `status` to `result` in
`wiremock/payment-mappings/payment-success.json` on a separate branch, pushed it, and
confirmed locally that the `pact-verify` job fails with an exact diff while the Gherkin
`test` job passes. This is the core claim of the session: Gherkin tests prove the system
behaves correctly; Pact tests prove the contracts don't drift. The pipeline catches the
breaking change that Gherkin misses, which is the whole point of having both.

One pre-existing failure was fixed before writing any YAML: the bad-spec test from
Issue #5 was intentionally left failing at the end of that session (the failure was the
finding). That left main in a state where CI would have been red from day one without
any feature change. The fix added response aliases so both the bad-spec and good-spec
test suites pass against the same endpoint.

See [`findings/issue-06-cicd-guardrails.md`](findings/issue-06-cicd-guardrails.md)
for the full session walkthrough, the breaking change output, and "The honest part" — an
unfiltered account of what the setup cost actually was.

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

The finding: WireMock tests verify that your code _behaves correctly given the stub
you wrote_. Pact verification proves that the stub _matches what the real service
actually returns_. Only the second check catches provider-side drift before production.

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
