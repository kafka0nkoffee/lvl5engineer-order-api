# Issue #16 — Architecture Decision Records: Making Decisions Agent-Readable

> Written in real time during the session.

---

## Phase 1 — The ADR format for agents

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Researched and documented the specific gap between a human-facing ADR and an agent-readable ADR — what each format prevents, what the agent-readable format adds, and why each addition is necessary.

### What happened

A human-facing ADR is written for a reader who can infer implications. The reader encounters the ADR before working in the codebase, reads the context and consequences, and brings their own engineering judgment to bear when those consequences are relevant. When the document says "if payment is checked first, every out-of-stock order results in a payment charge requiring reversal," the human reader knows what a reversal flow requires, understands the operational complexity, and recognises the warning.

An agent does not make inferences of that kind from a consequences section. It reads the ADR once, at session start, and then acts on incoming task descriptions. When the task says "parallelize the inventory and payment calls to reduce p99 latency," the agent does not automatically re-read the ADR to check whether parallelisation violates the documented decision. It needs to be told, explicitly, which actions to check against which ADRs — and it needs the check to be executable (yes/no questions, not judgment calls).

---

**What a human-facing ADR prevents (in the context of agent-assisted development):**

A human-facing ADR prevents informed humans from forgetting the reasons for a decision. It is a memory aid for people who were present or can understand context. In a fully human team, this is sufficient — engineers who are about to refactor a critical flow look up the relevant ADR. The barrier to doing this is low because the engineer already knows the ADR exists, knows which codebase area it covers, and knows why it matters.

In an agent-assisted context, a human-facing ADR prevents approximately nothing. The agent does not know which ADRs exist (unless told), does not know which code paths they cover (unless mapped), and does not know to check them before acting (unless instructed). A well-written human-facing ADR sitting in `docs/ADR/` is invisible to an agent that has not been told it exists and what it covers.

---

**What an agent-readable ADR adds and why each addition is necessary:**

**Invariant statement:** A single-sentence statement of the property that must remain true across all implementations. Human ADRs embed invariants in the consequences section where they compete for attention with context and rationale. An agent-readable ADR surfaces the invariant as a named, findable section. The agent can be instructed "read the invariant section of any ADR covering this code path before modifying it."

**Dangerous improvements:** An explicit list of changes that look like improvements but violate the decision. This section is the most novel addition and the most important one. The human reader who encounters "run inventory check and payment charge concurrently using asyncio.gather()" does not need to be told that this is dangerous — they can reason from the context. The agent might not. Without a dangerous improvements list, the agent has no prior basis for recognising that a common performance optimisation pattern is a specific violation of a specific decision. The dangerous improvements list is the ADR's pre-emptive strike against the most plausible misapplications.

**Agent check questions:** Three yes/no questions the agent must answer before modifying any code path covered by the ADR. The questions are designed to be answerable from the code without judgment — "did my change allow the payment gateway to be called before inventory confirmation?" is answerable by tracing the control flow. "Does my change violate the spirit of the invariant?" is not answerable by an agent that doesn't know what spirit means in this context.

**Consequence table:** A mapping from specific observable outcomes (test failures, log entries, measurement increases) to the specific violation they indicate. Without this table, an agent that observes a test failure after a change has to diagnose which invariant was violated. The consequence table pre-diagnoses: "if Scenario 3 fails, the payment gateway was called for an out-of-stock order, which is an ADR-001 violation." This lets the agent recognise a violation without reasoning backward from first principles.

---

**Which failure mode from Issue #14's taxonomy each section addresses:**

| ADR section | Failure mode addressed |
|---|---|
| Invariant statement | Invariant blindness — names what must remain true |
| Dangerous improvements | Invariant blindness + historical amnesia — names what was decided against |
| Agent check questions | All four — explicit pre-flight before any modification |
| Consequence table | Production blindness + invariant blindness — maps observable signals to violations |

---

### Why this matters

The gap between a human-facing ADR and an agent-readable ADR is the gap between "a record of a decision" and "a constraint that prevents a decision from being undone." A human ADR documents the past. An agent-readable ADR constrains the future. The dangerous improvements section is the structural difference: it does not just say "this is what we decided" — it says "here is what you might do that looks correct but isn't, and here is how you would know." That is not documentation; it is a pre-emptive specification of failure modes.

---

## Phase 2 — ADR-001: Inventory before payment

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/ADR/ADR-001-inventory-before-payment.md` formalising the design decision established in Issue #2. The ADR covers the standard human-facing sections (context, decision, consequences) plus the four agent-specific sections.

### What happened

The most important section was the dangerous improvements list. Three improvements were identified and documented:

1. Concurrent inventory and payment using `asyncio.gather()` or `ThreadPoolExecutor` — the exact implementation that Phase 4 demonstrates
2. Payment-first optimisation for the happy path — the "obvious" optimisation that creates a reversal liability
3. Cached inventory with pre-emptive payment — a time-delayed violation where the invariant is preserved on average but violated whenever inventory state changes

The third dangerous improvement is the hardest to catch with tests because the mock server always returns consistent inventory state within a test run. A cached inventory implementation might pass all tests in a test environment where the mock never changes state between calls, and only fail in production where inventory changes between the cache population and the payment call.

The consequence table links three specific test failures to ADR-001 violations. The most important entry: "If Scenario 3 passes but the step 'And the payment gateway is never called' was removed or rewritten — the test no longer verifies the invariant." This entry prevents the worst-case response to a failing invariant test: modifying the spec rather than fixing the implementation.

---

## Phase 3 — ADR-002: Fire-and-forget notification

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/ADR/ADR-002-fire-and-forget-notification.md` formalising the design decision established in Issue #7. The notification ADR is structurally similar to ADR-001 but covers a different failure mode: synchronous coupling.

### What happened

The dangerous improvements list for ADR-002 required thinking through four distinct patterns, not three. The fourth — adding a notification delivery check as a polling step before returning CONFIRMED — is the most subtle and the most likely to pass all tests while violating the invariant. A polling check that completes in < 100ms locally (because the test mock responds immediately) would not affect the test pass rate, but in production with a real notification service that takes seconds, it would add latency to every order confirmation.

This is a harder failure mode to test than ADR-001's violation, which is why the consequence table for ADR-002 includes an observable measurement, not just a test failure: "If the order confirmation response time increases when the notification service is slow → this ADR is violated." This measurement is not expressible as a Gherkin assertion in the current test suite — it requires a load test or latency profile against a slow notification mock.

---

## Phase 4 — The dangerous improvement demonstration

**Date:** 2026-07-05
**Status:** ✅ Worked — violation caught, reverted, correct implementation documented

---

### The dangerous improvement experiment

**Part A — The implementation**

Implemented the concurrent refactor of `create_order()` in `app/main.py`:

```python
import concurrent.futures

def _check_inventory():
    return httpx.post(
        f"{inventory_url}/inventory/check/{req.inventory_scenario}",
        json={"items": items_payload},
        timeout=10.0,
    )

def _charge_payment():
    try:
        resp = httpx.post(
            f"{payment_url}/payments/charge/{req.payment_scenario}",
            json={"user_id": req.user_id, "items": items_payload},
            timeout=payment_timeout,
        )
        return resp, None
    except httpx.TimeoutException:
        return None, "timeout"

# Run inventory check and payment charge concurrently to reduce p99 latency
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    inv_future = executor.submit(_check_inventory)
    pay_future = executor.submit(_charge_payment)
    inv_resp = inv_future.result()
    pay_resp, pay_err = pay_future.result()
```

The implementation is functionally complete. It handles all five scenarios. The response shapes are correct. No exceptions are thrown. An agent running a quick smoke test would see correct output for the happy path.

**Gherkin test results with dangerous improvement in place:**

```text
PASSED  test_order_is_successfully_created_when_payment_succeeds_and_all_items_are_in_stock
PASSED  test_order_is_rejected_when_payment_is_declined
FAILED  test_order_is_rejected_when_an_item_is_out_of_stock
FAILED  test_order_surfaces_partial_unavailability_without_autoconfirming
PASSED  test_order_handling_is_graceful_when_the_payment_gateway_times_out
```

Failure message for Scenario 3:
```text
AssertionError: Expected no payment calls, got:
[{'method': 'POST', 'path': '/payments/charge/success',
  'body': '{"user_id":"user-789","items":[{"sku":"SHOE-RED-42",...}]}'}]
```

**Part B — The ADR check**

Reading ADR-001's Agent check questions after implementing the concurrent version:

**Q1: Does the concurrent implementation ensure inventory confirmation completes before any payment gateway call is initiated?**

Answer: **NO.** Both calls are submitted to the ThreadPoolExecutor simultaneously. `executor.submit(_check_inventory)` and `executor.submit(_charge_payment)` are called on consecutive lines. Both threads start executing immediately. The payment HTTP request is sent to the gateway before the inventory result is available. There is no point in the implementation where the inventory result is checked before the payment call is initiated.

**Q2: Does the implementation handle the case where inventory returns out-of-stock after a payment call has already started?**

Answer: **YES — but incorrectly.** The implementation ignores the payment result when inventory reports out-of-stock. The response returned to the client is UNAVAILABLE. However, the payment HTTP request was already sent to the gateway and the gateway processed it. The payment transaction was initiated. The mock server logged it. In a real payment gateway, this would mean a charge attempt was made (and possibly accepted) for an order that will be rejected. The implementation "handles" the case by discarding the payment result, which is not the same as preventing the payment from occurring.

**Q3: Does Scenario 3 still pass without modification?**

Answer: **NO.** Scenario 3 fails on the step "And the payment gateway is never called." The step definition checks the mock server's call log. The log contains the payment call made during the concurrent execution. The assertion fails deterministically.

The ADR check would have prevented Part A from being committed. Q1 answer is NO → stop and reconsider before writing code.

**The critical finding: would an agent without the ADR have known something was wrong based on test output alone?**

Yes — but only because the spec contains the assertion "And the payment gateway is never called." If that step had not been written (or had been written as "And the order status is UNAVAILABLE" without the payment gateway assertion), the concurrent implementation would have passed all five Gherkin scenarios. The order status would be correct. The response shapes would be correct. The tests would be green.

The test catches the violation because the spec was written in Issue #2 with explicit awareness that the payment gateway must never be called for out-of-stock orders. That intent was encoded as a testable assertion. An agent without the ADR depends entirely on that assertion existing in the spec. An agent with the ADR knows, before writing a single line, that the payment-gateway-never-called assertion is the behavioral test for ADR-001 Invariant 1 — and that a concurrent implementation violates the invariant even when the assertion passes (in hypothetical scenarios where the test runs fast enough that the payment call is initiated but not yet logged before the test assertion runs).

**Part C — The revert and the correct implementation**

Reverted the dangerous improvement with `git revert HEAD --no-edit`. All 11 tests pass after revert.

A constraint-satisfying "concurrent optimisation" for this flow:

```python
# Pre-compute payment payload while the inventory call is in flight — no I/O, no violation
items_payload = [i.model_dump() for i in req.items]  # CPU-bound, completes in microseconds

# Step 1: Inventory check — must complete first (ADR-001)
inv_resp = httpx.post(
    f"{inventory_url}/inventory/check/{req.inventory_scenario}",
    json={"items": items_payload},
    timeout=10.0,
)
# ... check inventory result ...

# Step 2: Payment — only initiated after inventory confirms availability
# Payment payload already pre-computed; no additional setup latency
pay_resp = httpx.post(
    f"{payment_url}/payments/charge/{req.payment_scenario}",
    json={"user_id": req.user_id, "items": items_payload},
    timeout=payment_timeout,
)
```

This is the original implementation with an explicit comment. The "optimisation" — pre-computing the payload — reduces latency by approximately zero milliseconds because `model_dump()` is a nanosecond-scale operation. The honest conclusion: **there is no meaningful latency optimisation available between the inventory check and the payment call that satisfies ADR-001.** The calls must be sequential. The minimum latency is the sum of inventory latency plus payment latency. Reducing that sum requires faster individual services, not different call scheduling.

This is not a failure of the implementation; it is an accurate consequence of the design decision. The decision was made because the alternative (paying for unfulfillable orders) is worse than sequential latency. ADR-001 documents that trade-off. An agent that reads ADR-001 before attempting the optimisation reaches this conclusion before writing any code.

**Would the ADR's dangerous improvements section have prevented Part A's implementation?**

Yes. Dangerous Improvement 1 in ADR-001 names exactly what was implemented: "Running inventory check and payment call concurrently using `asyncio.gather()` or `concurrent.futures.ThreadPoolExecutor`." The agent check Q1 — "Does my change ensure inventory confirmation completes before any payment gateway call is initiated?" — is answerable in one sentence and the answer is NO for any concurrent implementation. The pre-flight check would have stopped the implementation before a line of code was written.

---

### Why this matters

The Gherkin test caught this violation. That is the correct outcome, and it happened because Issue #2 was deliberate about encoding not just the expected behavior but the explicit constraint on gateway calls. The more important finding is narrower: the test caught it because the spec was written well enough to catch it. The spec could easily have been written to check only the response status — "Then the order status is UNAVAILABLE" — without the payment gateway assertion. In that case, the concurrent implementation would have passed all five scenarios, produced correct response bodies, and made it to production. The failing test is a product of good specification, not of tests being generally sufficient to catch invariant violations. Tests catch what the spec was written to express. ADRs constrain what the spec cannot express: the ordering of actions, the synchrony of calls, the reason a guard exists. The production failure that ADR-001 prevents is the one where a customer is charged for an out-of-stock item because no test existed to check whether the payment call was made before the inventory result was available.

---

## Phase 5 — CLAUDE.md decision index update

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Updated the CLAUDE.md decision index to link ADR-001 and ADR-002 to their actual files in `docs/ADR/`, updated Invariant 1 and Invariant 2 references from "(planned — Issue #16)" to actual paths, and added the "Before modifying covered code paths" pre-flight protocol section.

### What happened

The decision index now has full links. The pre-flight protocol section makes explicit what was previously implicit: the ADR check is a precondition, not a postreview. The four steps — read the ADR in full, answer all agent check questions, verify the consequence table, stop and flag if any answer is NO — convert the ADR from a reference document into a workflow step.

The most important sentence in the new protocol: "Running it after implementation and then reverting is more expensive than running it before." This is the honest accounting of Phase 4. The dangerous improvement was implemented, committed, and reverted — three git operations and a full test run — because the ADR check was not performed first. The protocol makes the correct order explicit.

---

## Phase 6 — Full suite verification

**Date:** 2026-07-05
**Status:** ✅ Worked

```text
pytest tests/steps/ -v
→ 11 passed (confirmed after revert)

pytest tests/pact/ -v
→ 4 passed

python3 scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

All 15 tests pass. The dangerous improvement commit (`3734c15`) is in the git history for reference. The revert commit (`122213f`) restores the correct implementation. `main` contains the original sequential implementation plus the two ADRs and the updated CLAUDE.md.

---

### Why this matters

The dangerous improvement demonstration produces a specific answer to the question that frames Issue #16: "If an agent had been running this session without the ADR, at what point would it have known something was wrong?" The answer is: when Scenarios 3 and 4 failed — after the implementation was complete, committed, and tested. The test failure is loud and clear: `AssertionError: Expected no payment calls, got: [{'path': '/payments/charge/success', ...}]`. An agent without the ADR would revert the change, document a "latency optimisation attempted and reverted due to test failures," and move on. What it would not know — what the ADR makes explicit — is why the optimisation was wrong, which patterns to avoid the next time a latency task is requested, and that the only valid latency improvements for this flow are improvements to individual call performance rather than call scheduling. Without the ADR, the same violation will be attempted in every session where the task is framed as a performance improvement. With the ADR, Q1 of the agent check catches it in zero lines of code.
