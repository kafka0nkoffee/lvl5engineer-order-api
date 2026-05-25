# Issue #4 — Pact Contract Testing

**Session date:** 2026-05-25
**Scope:** Add Pact consumer tests, provider verification, a deliberate breaking change experiment, and a local can-i-deploy simulation to the order-api project.

---

## [Installing pact-python and the v3 FFI surprise]

**Date:** 2026-05-25
**Status:** ⚠️ Partial — installed successfully, but the API is not what the docs imply

### What I tried

Installed `pact-python` via pip into a fresh virtualenv, then wrote consumer tests
following the "module-scoped fixture, one test per scenario" pattern that every
pact-python v2 tutorial shows.

### What happened

```
FAILED tests/pact/test_inventory_service_consumer.py::TestInventoryServiceConsumer::test_item_out_of_stock
RuntimeError: The provider state could not be specified.
.venv/lib/python3.14/site-packages/pact_ffi/__init__.py:5624: RuntimeError
```

The first test in each class passed. Every subsequent test failed with a cryptic
RuntimeError from deep inside the Rust FFI layer.

### Root cause

`pact-python` 3.x is a complete rewrite backed by `pact-python-ffi` (a Rust binary).
The Rust FFI library does not support adding new interactions to a Pact handle after
`serve()` has been called on that handle. The module-scoped fixture pattern — create
the pact once, run multiple tests, write at the end — violates this constraint.
The error manifests as a "provider state could not be specified" failure on the
second `.given()` call because the first `serve()` call consumed the handle's
internal state machine.

### The fix

Restructured the consumer tests so that all interactions are defined upfront on a
single Pact handle, then a single `serve()` context manager exercises all of them
in sequence, then `write_file()` is called once. Two tests became two functions,
each building their full interaction set before touching the mock server.

### Why this matters

The pact-python documentation still shows v2-style patterns in many places, and
the error message gives you no hint that the issue is handle lifecycle rather than
a duplicate provider state. If you're migrating from pact-python v2 to v3 and
your tests start failing on the second scenario in a test class, this is why:
the underlying library changed from a stateful Python object to a Rust FFI handle
with a stricter lifecycle, and the documentation hasn't fully caught up.

---

## [Provider verification API friction: transport configuration]

**Date:** 2026-05-25
**Status:** ⚠️ Partial — required non-obvious configuration to get working

### What I tried

Wrote provider verification tests using `Verifier("PaymentGateway", "http://localhost:8291")`,
which is the pattern shown in the pact-python v3 README.

### What happened

```
RuntimeError: No transports have been set
```

Added `.add_transport(url="http://localhost:8291")` as the docs suggest. Got:

```
ValueError: Host mismatch: localhost != http://localhost:8291
```

The Verifier constructor stores the full URL string as `self._host`.
The `add_transport(url=...)` path then parses the URL to extract just the
hostname (`localhost`) and compares it to `self._host` (`http://localhost:8291`).
They don't match.

### Root cause

The Verifier in pact-python v3 separates the concept of "host" from "transport
configuration". The constructor expects just a hostname, not a full URL. Passing
a full URL to the constructor causes the host mismatch when you later try to
configure the transport using the `url=` shorthand.

### The fix

Pass just the hostname to the constructor and configure the transport with explicit
`protocol`, `port`, and `scheme` parameters:

```python
Verifier("PaymentGateway", "localhost")
    .add_transport(protocol="http", port=8291, scheme="http")
    .add_source(pact_file)
```

One additional issue: the payment-timeout stub has a `fixedDelayMilliseconds: 6000`
delay. The verifier's default request timeout is 5 seconds, so the timeout
interaction failed verification with a connection error. Fixed with
`.set_request_timeout(10000)`.

### Why this matters

Two pieces of configuration that seem redundant — passing a full URL to the
constructor, then separately calling `add_transport` — turn out to conflict
with each other. The error message does not explain why. This is the kind of
friction that takes an hour to debug when you're working from the documentation
rather than the source code.

---

## [Breaking change experiment — Pact catches what WireMock misses]

**Date:** 2026-05-25
**Status:** ✅ Worked — experiment completed exactly as designed

### What I tried

Ran the full breaking change experiment in five ordered steps.

### What happened

**Step 1: Provider verification baseline — all contracts pass**

```
pytest tests/pact/test_provider_verification.py -v -s

Verifying a pact between OrderService and PaymentGateway

  a declined payment charge (0s loading, 187ms verification)
     Given the payment gateway will decline the charge
    returns a response which
      has status code 402 (OK)
      includes headers
        "Content-Type" with value "application/json" (OK)
      has a matching body (OK)

  a successful payment charge (0s loading, 170ms verification)
     Given the payment gateway will accept the charge
    returns a response which
      has status code 200 (OK)
      includes headers
        "Content-Type" with value "application/json" (OK)
      has a matching body (OK)

  a timed-out payment charge (0s loading, 6s 182ms verification)
     Given the payment gateway will not respond within the timeout window
    returns a response which
      has status code 504 (OK)
      includes headers
        "Content-Type" with value "application/json" (OK)
      has a matching body (OK)

PASSED

Verifying a pact between OrderService and InventoryService
  [3 interactions — all OK]
PASSED

2 passed in 8.19s
```

**Step 2: Breaking change introduced**

In `wiremock/payment-mappings/payment-success.json`, changed:
```json
{"status": "ACCEPTED", "transaction_id": "txn-abc-123", "amount": 134.97}
```
to:
```json
{"result": "ACCEPTED", "transaction_id": "txn-abc-123", "amount": 134.97}
```

**Step 3: Provider verification after breaking change — Pact fails**

```
pytest tests/pact/test_provider_verification.py::test_payment_gateway_provider_verification -v -s

Verifying a pact between OrderService and PaymentGateway

  a declined payment charge (0s loading, 194ms verification)
     Given the payment gateway will decline the charge
    returns a response which
      has status code 402 (OK)
      has a matching body (OK)

  a successful payment charge (0s loading, 182ms verification)
     Given the payment gateway will accept the charge
    returns a response which
      has status code 200 (OK)
      has a matching body (FAILED)

  a timed-out payment charge (0s loading, 6s 196ms verification)
     Given the payment gateway will not respond within the timeout window
    returns a response which
      has status code 504 (OK)
      has a matching body (OK)


Failures:

1) Verifying a pact between OrderService and PaymentGateway Given the payment gateway
   will accept the charge - a successful payment charge
    1.1) has a matching body
           $ -> Actual map is missing the following keys: status
    {
      "amount": 134.97,
    -  "status": "ACCEPTED",
    +  "result": "ACCEPTED",
       "transaction_id": "txn-abc-123"
    }

There were 1 pact failures

FAILED
1 failed in 7.22s
```

**Step 4: Existing WireMock-based test suite with breaking change still in place**

```
pytest tests/steps/test_order_creation.py -v

tests/steps/test_order_creation.py::test_order_is_successfully_created_when_payment_succeeds_and_all_items_are_in_stock PASSED
tests/steps/test_order_creation.py::test_order_is_rejected_when_payment_is_declined PASSED
tests/steps/test_order_creation.py::test_order_is_rejected_when_an_item_is_out_of_stock PASSED
tests/steps/test_order_creation.py::test_order_surfaces_partial_unavailability_without_autoconfirming PASSED
tests/steps/test_order_creation.py::test_order_handling_is_graceful_when_the_payment_gateway_times_out PASSED

5 passed in 13.01s
```

**The Gherkin test suite passes. The breaking change is invisible to it.**

**Step 5: Revert and confirm provider verification passes again**

```
pytest tests/pact/test_provider_verification.py -v -s

[all 6 interactions — OK]

2 passed in 8.19s
```

### Root cause

The Gherkin scenarios test the order service's *behaviour*, not the shape of the
upstream response. When `app/main.py` receives the payment gateway response it
checks `pay_resp.status_code == 200` and then returns `{"status": "CONFIRMED"}` —
it never reads the `status` field from the payment gateway body. So from the
WireMock test harness's perspective, nothing broke: the right HTTP status code
came back and the order was confirmed. The `status → result` rename was completely
invisible.

Pact caught it because the consumer test had explicitly declared that the order
service *expects* a `status` field. The pact file encodes that expectation as a
machine-readable contract. When the provider verification ran against the modified
stub, the Rust verifier compared the actual response body against the contract
and found the key missing.

### Why this matters

This is the core argument for contract testing, and it is subtle enough that
many experienced teams miss it entirely. A WireMock stub is a *behavioural double*
— it makes your integration tests pass by simulating the service. But the stub is
maintained by you, the consumer team. You can change it whenever you like, and
your tests will still pass. The real service — owned by a different team, deployed
independently — can diverge silently. When it does, the first you'll know is a
production incident.

The rename from `status` to `result` in this experiment is not a contrived scenario.
It is exactly the kind of change that happens in real APIs: a provider team cleans
up an inconsistently-named field, ships it, and never thinks to tell every consumer.
Their tests pass. Your tests pass. Production breaks.

Pact inverts the trust relationship. The consumer defines what it needs. The
provider proves it delivers that before it ships. A mock that can drift is a
confidence trap — it makes you feel safe right up until production proves you
weren't.

---

## [can-i-deploy local simulation]

**Date:** 2026-05-25
**Status:** ✅ Worked

### What I tried

Wrote `scripts/can_i_deploy.py` — a script that reads the generated pact files,
checks each interaction's request path and expected response body against the
WireMock stub mappings, and exits 0 (safe) or 1 (blocked).

### What happened

With contracts intact:

```
python scripts/can_i_deploy.py

============================================================
Pact: OrderService → InventoryService
  PASS  an inventory check when all items are in stock
  PASS  an inventory check when an item is out of stock
  PASS  an inventory check with partial availability

============================================================
Pact: OrderService → PaymentGateway
  PASS  a declined payment charge
  PASS  a successful payment charge
  PASS  a timed-out payment charge

============================================================
RESULT: ALL CONTRACTS VERIFIED — safe to deploy
============================================================
Exit: 0
```

With the `status → result` breaking change in place:

```
python scripts/can_i_deploy.py

  FAIL  a successful payment charge [the payment gateway will accept the charge]
        stub is missing fields expected by consumer: ['status']

RESULT: CONTRACT VIOLATIONS DETECTED — do not deploy
Exit: 1
```

### Root cause

No bugs. The script works as designed.

### The fix

N/A.

### Why this matters

The `can-i-deploy` check in a real Pact Broker pipeline queries a central record
of which consumer versions have verified which provider versions. This local
simulation does something simpler but teaches the same pattern: before you deploy,
prove the contract is still satisfied. The exit code is what a CI gate reads. A
non-zero exit stops the merge. This is what turns a test result into a deployment
decision, and it is the link between the contract and the pipeline.

---

## [pact-python v3 FFI constraint summary]

**Date:** 2026-05-25
**Status:** ⚠️ Documented — not a bug, but a significant API difference from v2

### What I tried

Attempted to reuse the standard v2 pattern of module-scoped Pact fixtures.

### What happened

See the "Installing pact-python" finding above.

### Root cause

pact-python v3 uses a Rust FFI binary (`pact-python-ffi`) under the hood. The
handle lifecycle is stricter than the old Python-only v2 library. Specifically:
- You cannot add interactions to a handle after `serve()` has been called on it
- The `Verifier` constructor takes a hostname, not a full URL
- The `add_transport` call is required even for plain HTTP — the verifier does
  not infer a transport from the constructor URL

### The fix

Structure consumer tests with all interactions added before any `serve()` call.
Use `Verifier("provider-name", "localhost").add_transport(protocol="http", port=N, scheme="http")`.

### Why this matters

If your team is upgrading from pact-python 1.x/2.x to 3.x, expect to rewrite
your test fixtures. The API change is not just syntax — it reflects a different
mental model of how the mock server lifecycle works. The v3 handle is consumed
by `serve()`; the v2 object was reusable. Neither the changelog nor the README
makes this clear. The only way to discover it is to run the tests and read the
Rust error message, which doesn't point to the real cause.
