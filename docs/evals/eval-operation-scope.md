# Eval: Operation Scope

> This eval runs before any agent action that modifies `app/main.py` or any
> file in `tests/`.
>
> Answer all four questions before proceeding. A HALT instruction must not be
> overridden by task urgency, confidence in the change, or prior approval of
> similar changes. HALT means flag to the human author and wait.

---

## What this eval is for

`app/main.py` implements the order creation flow: inventory check, payment
charge, order confirmation, notification dispatch. Changes to this file have
three categories of risk that static code review does not automatically surface:

1. **Covered decisions** — ADRs exist for two specific design decisions in this
   file. Violating either requires no change to passing tests in some scenarios.
2. **Service call ordering** — The sequence of external calls (inventory →
   payment → notification) is load-bearing. Changes to call order or
   synchronicity have production consequences that do not appear in the happy
   path.
3. **Retry semantics** — The payment retry cap (2 total attempts) is a
   Gherkin-enforced constraint. Retry logic changes affect idempotency and
   worst-case latency.

Changes to `tests/` affect what the behavioral specification asserts. Test
modifications that weaken or remove assertions are equivalent to weakening the
specification itself — the test stops verifying the invariant it was written to
verify.

---

## Q1: Is this change covered by an existing ADR?

Check the decision index in `CLAUDE.md` (Section 5). If the code path being
modified appears in the index, read the full ADR before writing any code.

**ADRs currently active for `app/main.py`:**

| ADR | Covers |
|---|---|
| `docs/ADR/ADR-001-inventory-before-payment.md` | Inventory check must complete before any payment gateway call is initiated |
| `docs/ADR/ADR-002-fire-and-forget-notification.md` | Notification call must not block order confirmation response |

**How to answer the ADR agent check questions:**

Each ADR contains three agent check questions that are answerable YES or NO from
the code without judgment. Answer all three. If any answer is NO — or if the
question cannot be answered YES without interpretation — do not proceed.

**If an Agent check question cannot be answered YES — HALT.**

Flag to the human author. State which question cannot be answered YES and why.
Do not infer that the answer is "close enough to YES" or that the invariant is
"mostly preserved."

**If NO ADR covers this change:**

Proceed to Q2.

---

## Q2: Does this change alter the ordering of external service calls?

**External service calls in the order-api:**

| Call | Direction | Protocol |
|---|---|---|
| Inventory check | `POST /inventory/check/{scenario}` | Synchronous, blocking |
| Payment charge | `POST /payments/charge/{scenario}` | Synchronous, blocking, with retry |
| Notification | `POST /notifications/order-confirmed` | Asynchronous, daemon thread, fire-and-forget |

**Current call order:** Inventory → Payment → Notification (non-blocking)

The ordering of inventory and payment is constrained by ADR-001. The ordering
of notification is constrained by ADR-002. Any change that alters the sequence
— introducing a concurrent call, moving payment before inventory, starting the
notification before payment completes — must pass the relevant ADR agent check
questions before proceeding.

**If YES:**

Read ADR-001 and ADR-002. Answer all agent check questions for the applicable
ADR. If any answer is NO → HALT.

**If NO:**

Proceed to Q3.

---

## Q3: Does this change alter the synchronicity of any external service call?

**Synchronous → asynchronous:** The call currently blocks until a response is
received. The change makes it non-blocking — the response arrives later or is
discarded. Check whether the call was made synchronous for a reason before
assuming asynchrony is an improvement. For the notification call, ADR-002
documents why it is already asynchronous and why making it synchronous would
be a degradation.

**Asynchronous → synchronous — HALT immediately.** Making an asynchronous call
synchronous is a high-risk change that directly violates ADR-002 for the
notification call. A synchronous notification call couples order confirmation
latency to notification service availability: a notification service outage
blocks every order confirmation. No behavioral test currently asserts that the
notification call is asynchronous — the test suite would pass after this change,
and the production failure would only manifest when the notification service has
its first outage.

**If YES:**

For synchronous → asynchronous: read the relevant ADR and answer agent check
questions before proceeding.

For asynchronous → synchronous — HALT. Document the change as an attempted
dangerous improvement and flag to the human author.

**If NO:**

Proceed to Q4.

---

## Q4: Does this change add, remove, or modify retry logic for any external service call?

**Current retry configuration:**

| Call | Retry behavior |
|---|---|
| Inventory check | No retry. Failure propagates as unhandled exception. |
| Payment charge | 2 total attempts (1 original + 1 retry) on `httpx.TimeoutException`. `MAX_PAYMENT_RETRIES` env var. |
| Notification | No retry. Fire-and-forget; result discarded regardless. |

**Why retry changes are high-risk:**

1. **Idempotency:** The payment gateway may process a charge request that returns
   a timeout from the client's perspective. A second attempt may result in a
   duplicate charge if the gateway is not idempotent. Do not increase the retry
   cap without confirming the gateway's idempotency guarantees.

2. **Worst-case latency:** The Gherkin spec constrains worst-case response time
   to 12 seconds (Scenario 5). With 2 total attempts at 5s timeout each, the
   worst case is 10s. Increasing `MAX_PAYMENT_RETRIES` to 3 would make the
   worst case 15s — a Scenario 5 violation. Any retry cap change requires
   recalculating against `PAYMENT_TIMEOUT_SECONDS × MAX_PAYMENT_RETRIES ≤ 12`.

3. **Application-level vs gateway-level retry:** Adding application-level retry
   to the inventory call (which currently has none) would change the behavior
   for any inventory service outage scenario. Verify whether the inventory
   service has its own retry mechanism before adding a second retry layer.

**If YES:**

Document the retry change and its idempotency and latency implications before
implementing. If adding retry to payment, verify the worst-case latency formula.
If adding retry to inventory or notification, verify whether a second retry layer
is appropriate given the service's own retry behavior.

**If NO:**

Proceed with the change.

---

## Failure modes addressed

This eval addresses two of the four failure modes from Issue #14:

**Invariant blindness:** Q1 and Q3 catch changes that violate architectural
invariants that are not expressed in the behavioral test suite. The most
important case is ADR-002 (asynchronous notification): no Gherkin scenario
asserts that the notification call is asynchronous. An agent that removes the
daemon thread and makes the call synchronous passes all 15 tests. The eval
catches this at Q3 before a line of code is written.

**Historical amnesia:** Q1 links to ADR-001 and ADR-002, which document why
specific design decisions were made. Without the ADR reference, an agent that
receives a task like "run inventory and payment concurrently to reduce p99
latency" has no basis for recognising that concurrent calls were considered and
explicitly rejected. Q1's instruction to read the ADR before acting gives the
agent access to that history.

---

## Example: The Issue #16 dangerous improvement

In Issue #16, the task was to demonstrate the concurrent inventory+payment
refactor as an example of a dangerous improvement. The implementation used
`concurrent.futures.ThreadPoolExecutor` to submit both the inventory check and
the payment charge simultaneously.

**If the operation scope eval had been run before implementation:**

Q1 fires: The change touches `app/main.py`'s order creation flow, which is
covered by ADR-001. The agent reads ADR-001 and answers the agent check
questions.

ADR-001 Q1: "Does my change ensure inventory confirmation completes before any
payment gateway call is initiated?" Answer: **NO.** Both calls are submitted
simultaneously. The payment HTTP request is sent before the inventory result
is available.

Action: HALT. Flag to human author.

The implementation was not written. No test run needed. The concurrent pattern
was identified as an ADR-001 violation in zero lines of code.

**Which question is higher risk for this project: Q2 or Q3?**

Q3 is the higher-risk question. Q2 (ordering) violations are caught by the
Gherkin test suite when the invariant has an explicit assertion ("And the
payment gateway is never called"). Q3 (synchronicity) violations may not be
caught by any test. There is no behavioral test that asserts the notification
call is asynchronous. An agent that makes the notification call synchronous
will see all 15 tests pass — and the production failure will only appear when
the notification service has its first outage. Q3 catches this class of violation
before any test is run.
