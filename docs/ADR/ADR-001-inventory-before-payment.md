# ADR-001: Inventory checked before payment attempted

**Status:** Accepted
**Date:** 2026-05-01 (Issue #2 — first established; invariant formalised Issue #16)
**Deciders:** Human author (newsletter)
**Covered code paths:** `app/main.py:create_order()` — the block from inventory check to payment charge

---

## Context

The order creation flow requires calling two external services: an inventory service
(to confirm items are available) and a payment gateway (to charge the customer). These
two calls could, in principle, run in any order or concurrently. The ordering is a
design decision with real consequences.

**If payment is checked first:** A customer is charged before it is confirmed that the
items are available. If inventory is out of stock, the payment has already been processed
and must be reversed. The order service then requires a refund/reversal flow — which is
not currently implemented. Every out-of-stock order creates a financial liability before
the failure is surfaced.

**If inventory and payment are checked concurrently:** The payment call is initiated before
the inventory result is available. In the time between initiating the payment call and
receiving the inventory result, it is possible to charge a customer for an unfulfillable
order. The probability of this failure depends on relative latency of the two services —
making the correctness of the system a function of network timing rather than logic.

**If inventory is checked first:** The payment gateway is only called when inventory has
confirmed availability. Out-of-stock orders never reach the payment gateway. Partial
availability orders never reach the payment gateway. The financial system is only
engaged when the order can actually be fulfilled.

---

## Decision

Inventory availability must be confirmed before any payment gateway call is initiated.

The implementation is sequential:
1. Call inventory service and wait for result
2. If any items are unavailable (partial or full out-of-stock): return immediately without calling payment
3. If all items are confirmed available: call payment gateway

This ordering is not an implementation detail — it is a system property. Any refactoring
that changes the relative timing of these two calls (concurrent execution, reordering,
pre-emptive payment attempts) violates this decision and must be reviewed against this ADR.

---

## Consequences

**Positive:**
- The payment gateway is never charged for unfulfillable orders
- The system does not require a payment reversal/refund path for inventory failures
- The correctness of the payment-never-called invariant is a function of code logic, not
  network timing
- Gherkin Scenarios 3 and 4 ("payment gateway is never called") can be tested as
  deterministic assertions, not probabilistic ones

**Negative:**
- Order creation latency is the sum of inventory latency + payment latency for the
  happy path — sequential calls cannot be faster than their sum
- There is no way to reduce p99 latency by parallelising the two calls (by design)
- Any latency optimisation must focus on individual call performance (caching, connection
  pooling) rather than call scheduling

---

## Invariant statement

**Inventory availability must be confirmed before any payment gateway call is initiated
for the same order. This must hold regardless of implementation approach — sequential,
concurrent, or async.**

A payment gateway call is "initiated" the moment an HTTP request is sent to the payment
endpoint. Pre-building the request payload does not violate the invariant; sending the
request does.

---

## Dangerous improvements

These are changes that appear to improve performance or reliability but violate this decision.
An agent encountering a task that resembles any of these must read this ADR before proceeding.

**1. Concurrent inventory check and payment charge using `asyncio.gather()` or
`concurrent.futures.ThreadPoolExecutor`**

Appears to reduce p99 latency by running both calls in parallel. Violates the invariant
because the payment call is sent before the inventory result is known. For out-of-stock
orders, the payment gateway receives a charge request that should never have been sent.
The Gherkin test "payment gateway is never called" will fail — but only if the test suite
is run after this change.

**2. Payment-first optimisation for the happy path**

Appears to improve common-case latency by checking payment before inventory, reasoning
that most orders are in stock. Violates the invariant completely: every out-of-stock order
results in a payment charge. Requires a refund/reversal flow that does not exist in this
service. Scenarios 3 and 4 will fail.

**3. Cached inventory with pre-emptive payment**

Appears to reduce latency by caching inventory results and initiating the payment call
before re-confirming inventory. Violates the invariant in a time-delayed way: if items
become out-of-stock between the cache population and the current order, the payment gateway
is charged for a now-unfulfillable order. The test suite will not catch this because the
test mock always returns consistent inventory state within a test run.

---

## Agent check

Answer all three questions before modifying `create_order()` in `app/main.py`:

**Q1: Does my change ensure inventory confirmation completes before any payment gateway
call is initiated?**

"Initiated" means an HTTP request has been sent to the payment endpoint. Pre-building
the request payload, establishing a connection, or computing values needed for the
request are not initiations. Calling `httpx.post()` or `requests.post()` to the payment
URL is an initiation.

Answer must be YES to proceed.

**Q2: Does my change handle the case where inventory returns out-of-stock after a payment
call has already started?**

If your change allows a payment call to start concurrently with the inventory check,
you must have an explicit mechanism for cancelling or ignoring the payment call if
inventory confirms unavailability. Note: in Python, an HTTP request that has been sent
cannot be cancelled — cancelling a future does not cancel a network request already in
flight.

Answer must be YES (mechanism exists) or "this situation cannot arise" (because the
invariant prevents it) to proceed.

**Q3: Does Scenario 3 ("Order is rejected when an item is out of stock") in
`order_creation.feature` still pass without modification?**

Specifically: does the step "And the payment gateway is never called" still pass? This
step checks the mock server's call log for the current test run. If the payment mock
received any call during the test, this step fails.

Answer must be YES to proceed.

---

## Consequence table

These test outcomes indicate an ADR-001 violation. If you observe any of the following,
review this ADR before committing:

| Observation | Violation indicated |
|---|---|
| Scenario 3 ("payment gateway is never called") fails | Payment was called for an out-of-stock order |
| Scenario 4 ("payment gateway is never called") fails | Payment was called for a partial-availability order |
| The payment mock receives calls during an out-of-stock or partial-stock test | Invariant violated — call ordering changed |
| Scenario 3 passes but requires modification to pass | The spec was changed to accommodate the violation |

If Scenario 3 passes but the step "And the payment gateway is never called" was removed
or rewritten: the test no longer verifies the invariant. This is a spec violation, not
a code fix. Do not modify Scenario 3 to make a concurrent implementation pass.
