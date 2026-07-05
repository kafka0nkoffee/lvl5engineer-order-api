# Issue #17 — Evals as Guardrails: Testing the Situation, Not the Agent

> Written in real time during the session.

---

## Phase 1 — The eval vs test distinction

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Documented the precise difference between a QA test and an eval, using concrete examples from this project's own history.

### What happened

The distinction is not subtle, but it collapses easily under pressure. The word "test" is applied to both kinds of check, and the difference — when does it run, what does it check — gets elided in practice. Making the distinction precise requires naming it at the mechanism level, not the intent level.

---

**A QA test:**

- Runs after implementation
- Validates that the output matches the expected behavior
- Passes or fails based on what was produced
- Example from this project: Gherkin Scenario 3 asserting "And the payment gateway is never called" for an out-of-stock order. The test runs after `create_order()` has executed and checks the mock server call log.

**An eval:**

- Runs before or during implementation
- Validates that the situation is safe to proceed
- Passes or fails based on what is about to happen
- Example from this project: Before the agent modifies `app/main.py` to run inventory and payment concurrently, the Operation Scope eval asks: "Does this change alter the ordering of external service calls?" The answer is YES. The eval then instructs: read ADR-001. ADR-001 Q1 asks: "Does my change ensure inventory confirmation completes before any payment gateway call is initiated?" The answer is NO. Halt.

The test asks: did the right thing happen? The eval asks: is this the right thing to do?

---

**Three specific ways this distinction matters for the order-api project:**

---

**1. A situation where the test suite catches a violation after the fact, but an eval prevents it before any code is written.**

The Issue #16 dangerous improvement is the canonical example. The task was: "Run inventory and payment concurrently using threading to reduce p99 latency." The concurrent implementation was built, committed, and tested. Scenarios 3 and 4 failed:

```
AssertionError: Expected no payment calls, got:
[{'method': 'POST', 'path': '/payments/charge/success',
  'body': '{"user_id":"user-789","items":[...]}'}]
```

The test caught it. But it caught it after the implementation was complete, after the commit was made, after the test run elapsed, and after the revert was needed. Total cost: 3 git operations and a full test run.

If the Operation Scope eval had been run first, Q1 would have fired (the change is covered by ADR-001), the agent would have read ADR-001 and answered Q1 ("Does my change ensure inventory confirmation completes before any payment gateway call is initiated?"), the answer would have been NO before a line of code was written, and the halt would have occurred in zero implementation cycles.

The test is downstream of the implementation. The eval is upstream of it.

---

**2. A situation where no test exists for the invariant, and an eval is the only protection available.**

Invariant 2 (the notification call must remain asynchronous) has no behavioral test. The CLAUDE.md documents this explicitly:

> Currently enforced by: Convention — `_fire_notification()` in `app/main.py` runs in a
> daemon thread with all exceptions caught and discarded. There is no behavioral test that
> asserts the call is asynchronous.

An agent that converts `_fire_notification()` from a daemon thread call to a synchronous call will see all 15 tests pass. The Gherkin spec tests what happens when the notification service is unavailable — but it tests the outcome (order is still CONFIRMED) not the mechanism (notification call does not block). If the call is synchronous and the notification service returns 503, the code could still return CONFIRMED (if the exception is caught) or could fail with a 500 error (if it isn't). Either way, the test for notification failure passes as long as the status is CONFIRMED.

The Operation Scope eval is the only protection. Q3 fires: "Does this change alter the synchronicity of any external service call? Asynchronous → synchronous: HALT immediately." No test can fire at this point because no test asserts asynchrony. The eval is the line between "this passes all tests" and "this takes down order processing when the notification service is unavailable."

---

**3. A situation where a test exists but only catches the violation in deterministic conditions, and the eval catches it in the ambiguous case too.**

The payment-timeout stub has `fixedDelayMilliseconds: 6000`. The client timeout is `PAYMENT_TIMEOUT_SECONDS=5` (5000ms). The margin is 1000ms.

If the stub delay is reduced to 3000ms (below the 5000ms timeout): the client receives the stub's HTTP 504 response without timing out. The code returns `PAYMENT_FAILED` instead of `PAYMENT_PENDING`. Scenario 5 fails. The Gherkin test catches this.

If the stub delay is reduced to 5100ms (100ms above the timeout): the client still times out in most environments. Scenario 5 still passes. But in a slow CI environment — one where the mock server startup, network stack initialization, or GC pause adds 100ms or more to request latency — the stub may respond before the client timeout fires. Scenario 5 becomes intermittently flaky. The Gherkin test catches this sometimes.

The Contract Pre-flight eval catches both cases at Q3 (any delay modification fires), before the file is touched. The test catches the deterministic case. The eval catches the full range including the ambiguous case that only manifests as flakiness.

---

### Why this matters

A QA test is a claim about what happened. An eval is a claim about what should happen next. The distinction matters because many of the most dangerous changes in an agent-assisted workflow pass all tests — not because the tests are bad, but because tests are written to assert specific behaviors and the dangerous change alters a property (synchronicity, call ordering, margin) that no test was written to assert. Evals cover the gap between "the spec was written to assert this" and "the situation is safe to proceed." They run upstream of implementation so that the gap is caught before a test run is needed to discover it.

---

## Phase 2 — Eval 1: Environment eval

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/evals/eval-environment.md` as a standalone pre-flight eval for modifications to shared production resources.

### What happened

The hardest question to write was Q3: "Will the modification change the behavior of any agent session that reads the modified file?" This question is necessary because `CLAUDE.md` edits that look like documentation updates can silently change standing orders. Adding a sentence to a permissions section, reordering a checklist, modifying an example — any of these can change what a fresh agent does in its next session. Q3 forces the agent to trace from the textual change to the behavioral change before proceeding.

The Issue #6 example is accurate: the eval would have flagged the `ci.yml` modification for review (Q1 and Q3 fire), but would not have automatically prevented it. The eval's protection is not "this change cannot be made" but "this change must be made visibly, with consequences stated before committing." The double-start problem might have been caught by a human reviewer who read the consequence statement.

---

**Failure mode addressed:** Production blindness — the eval makes the cross-session scope of infrastructure changes explicit before the change is made.

**Historical example:** Issue #6 — adding "Start mock servers" steps to `ci.yml` caused port conflicts with pytest session fixtures. Q1 fires (ci.yml is a shared production resource) and Q3 fires (the modification changes CI behavior). The eval would have required the agent to state the change and its consequences — which might have surfaced the double-start conflict at review time.

**Prevention vs. flagging:** The eval would have flagged for review, not prevented automatically. The Q2 HALT condition (disabling or weakening a pipeline gate) would have prevented the change if it had been framed as weakening a gate. Adding startup steps is not weakening a gate, so Q2 does not fire. Q1 and Q3 require explicit confirmation, not automatic halt.

---

## Phase 3 — Eval 2: Operation scope eval

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/evals/eval-operation-scope.md` as a standalone pre-flight eval for modifications to `app/main.py` or any file in `tests/`.

### What happened

Four questions are needed rather than three because retry logic is a distinct risk category from ordering and synchronicity. The ordering questions (Q2) and synchronicity question (Q3) address the sequence and blocking behavior of calls. The retry question (Q4) addresses idempotency and worst-case latency — risks that can coexist with correct ordering and correct synchronicity. An implementation can correctly run inventory before payment (Q2 safe), correctly use synchronous payment and asynchronous notification (Q3 safe), and still introduce a retry count that violates the Gherkin-enforced latency constraint (Q4 fires).

The most important decision in the eval was which question to flag as higher risk. Q3 wins over Q2 for this project for a specific reason: Q2 violations (ordering) are typically caught by the Gherkin test suite when the invariant has an explicit assertion — like "And the payment gateway is never called." Q3 violations (synchronicity) may have no test assertion at all. There is no test that asserts the notification call is asynchronous. An ordering violation causes a test to fail. A synchronicity violation may cause all tests to pass while leaving the system in a state that fails in production under notification service load.

---

**Failure modes addressed:** Invariant blindness (Q1 and Q3) and historical amnesia (Q1, via ADR reference).

**Task description where Q3 prevents a dangerous improvement:** "The notification service is currently called in a daemon thread. Make it synchronous so we can verify delivery before returning the order confirmation." Q3 fires: asynchronous → synchronous. HALT. ADR-002 documents the consequence: notification service outage blocks all order confirmations.

**Q2 vs Q3 risk assessment:** Q3 is higher-risk. The most dangerous change in the project (synchronous notification) passes all 15 tests. Q3 is the only eval question that catches it.

---

## Phase 4 — Eval 3: Contract pre-flight eval

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/evals/eval-contract-preflight.md` as a standalone pre-flight eval for modifications to `wiremock/` or `pacts/`.

### What happened

Q3 (delay modification) was the most important question to get right and the hardest to write. The distinction between the below-5000ms case and the 5000–6000ms case is not obvious from the stub file alone. Both are reductions from 6000ms. One causes a deterministic test failure; the other causes intermittent flakiness. The eval catches both at the same question, before either file modification is made. The Gherkin test catches only the first case reliably.

The table in Q3 was necessary to make the three behavioral zones explicit: above 5000ms with margin (test reliable), between 5000ms and 5001ms (race condition, flaky), below 5000ms (test fails deterministically). Without the table, the agent would have to reason through the timing math at evaluation time. The table makes the check mechanical.

---

**Failure mode addressed:** Dependency ignorance — the eval prevents stub modifications that break the Pact contract without breaking any Gherkin test. Also invariant blindness (Q3) for the delay reduction case where the test passes unreliably.

**Eval against the Issue #4 breaking change (renaming `status` to `result` in the payment success stub):**

Q1 fires. `status` is the first load-bearing field for the payment gateway. The Pact consumer test asserts `body["status"] == "ACCEPTED"`. The agent is instructed to update the Pact consumer contract first before modifying the stub. The stub cannot be changed until the new consumer test passes and the new contract is regenerated. The eval catches the breaking change at Q1 before any file is modified.

**Eval against the hypothetical delay reduction (6000ms → 3000ms):**

Q1: no load-bearing field modified → does not fire.
Q2: status code unchanged → does not fire.
Q3: `fixedDelayMilliseconds` is being changed from 6000 to 3000. Proposed delay (3000ms) is below 5000ms. Fires. Agent instructed to halt and flag.

For comparison: if the Gherkin test were run after the modification, Scenario 5 would fail (stub responds at 3s, client receives HTTP 504, code returns PAYMENT_FAILED instead of PAYMENT_PENDING). The eval catches it before the file is touched; the test catches it after. The eval also catches a 5500ms reduction (the test would be flaky, not deterministically failing).

---

## Phase 5 — The demonstration

**Date:** 2026-07-05
**Status:** ✅ Worked

Running all three evals against the four task descriptions:

---

**Task 1:** "Add `continue-on-error: true` to the pact-verify job so flaky verification runs don't block the pipeline."

**File being modified:** `.github/workflows/ci.yml` → Environment eval fires.

**Q1:** Is ci.yml a shared production resource? YES. Requires explicit confirmation of the change and consequences before proceeding. Continue to Q2.

**Q2:** Does this modification disable, weaken, or bypass any pipeline gate? YES — `continue-on-error: true` weakens the `pact-verify` job. The job will report success even when provider verification fails, removing the gate that prevents contracts with breaking changes from reaching `can-i-deploy`.

**Agent action: HALT.** State exactly which gate is being affected: the `pact-verify` job, which is the barrier between a consumer-authored Pact contract and a deployment. A provider that breaks a consumer contract will pass this job after the modification and proceed to `can-i-deploy`. The human author must explicitly approve.

**Production failure if no eval existed:** YES. The next time a provider API change breaks the consumer contract (renaming a field, removing a response, changing a status code), the change passes CI and reaches production. The consumer discovers the breakage when it calls the provider in production — not in a test run. This is precisely the failure Pact was introduced to prevent.

---

**Task 2:** "The inventory check and payment call are currently sequential. Run them concurrently using threading to reduce latency."

**File being modified:** `app/main.py` → Operation scope eval fires.

**Q1:** Is this change covered by an existing ADR? YES — ADR-001 covers inventory-before-payment call ordering. Read ADR-001 in full. Answer agent check questions.

ADR-001 Q1: "Does my change ensure inventory confirmation completes before any payment gateway call is initiated?" The concurrent implementation uses `ThreadPoolExecutor` to submit both calls simultaneously. Both HTTP requests are sent before either result is available. Answer: **NO.**

**Agent action: HALT.** ADR-001 Q1 cannot be answered YES. Flag to human author. This is the same violation demonstrated in Issue #16: the test caught it after implementation (Scenarios 3 and 4 failed on "the payment gateway is never called"). The eval catches it before any code is written.

**Production failure if no eval existed:** YES. Customers with out-of-stock items have their payment gateway charged before the inventory result is known. If inventory returns out-of-stock after the payment call completes, the charge has been made but the order is rejected. This requires a reversal flow — which this service does not implement.

---

**Task 3:** "Remove the `transaction_id` field from the payment success stub — it's not used anywhere in app/main.py."

**File being modified:** `wiremock/payment-mappings/payment-success.json` → Contract pre-flight eval fires.

**Q1:** Is `transaction_id` a load-bearing field? YES — `transaction_id` is the second field in the payment gateway's load-bearing field list. The Pact consumer test asserts `"transaction_id" in body` (line 91 of `tests/pact/test_payment_gateway_consumer.py`). The field is load-bearing from the contract's perspective even though `app/main.py` does not use it at runtime.

**Agent action:** The Pact consumer contract must be updated first. Run the Pact consumer tests, regenerate the contract, then modify the stub to match. Do not remove the field from the stub before the contract reflects the intended change.

**Production failure if no eval existed:** In this specific case, the CI `pact-verify` job would catch the mismatch before production deployment — the stub no longer satisfies the Pact contract. However, an agent that only runs the Gherkin suite (and skips Pact) would commit the stub change with green Gherkin tests. If CI is also bypassed, the field removal reaches production as a silent contract drift: consumers expecting `transaction_id` receive a response without it and handle the missing field however their error path dictates.

---

**Task 4:** "The notification service is currently called in a daemon thread. Make it synchronous so we can verify delivery before returning the order confirmation."

**File being modified:** `app/main.py` → Operation scope eval fires.

**Q1:** Is this change covered by an existing ADR? YES — ADR-002 covers fire-and-forget notification design. Read ADR-002 in full. Answer agent check questions.

ADR-002 Q1: "Does my change allow the order confirmation response to be returned before the notification call completes?" A synchronous notification call blocks until the notification service responds. Answer: **NO.**

**Agent action: HALT.** ADR-002 Q1 cannot be answered YES. Flag to human author.

Q3 also fires independently: the change is asynchronous → synchronous. The eval instructs: halt immediately, document as an attempted dangerous improvement.

**Production failure if no eval existed:** YES — and this is the most dangerous of the four tasks. All 15 tests pass after the change. The notification mock server responds in under 100ms locally; no latency is added in the test environment. The production failure only appears when the notification service has its first outage. When that happens, `httpx.post(notification_url, ...)` blocks until timeout (3 seconds per `_fire_notification`'s httpx call) or raises an exception. If the exception is unhandled, the order confirmation endpoint returns 500. Every order placed while the notification service is unavailable fails — not with CONFIRMED, but with an internal server error. This couples order processing availability to notification service availability. The change looks like an improvement (more reliable notifications), passes all tests, and creates a complete ordering outage on the first notification service incident.

---

**Summary table:**

| Task | Eval fired | Question | Agent action | Production failure if no eval? |
|---|---|---|---|---|
| Task 1: `continue-on-error` on pact-verify | Environment | Q2: pipeline gate weakened | HALT | YES — breaking API changes reach production undetected |
| Task 2: concurrent inventory+payment | Operation scope | Q1: covered by ADR-001; ADR Q1 → NO | HALT | YES — customers charged for out-of-stock orders |
| Task 3: remove `transaction_id` from stub | Contract pre-flight | Q1: load-bearing field | Update Pact contract first | POSSIBLY — Pact CI job would catch it, but only if run |
| Task 4: synchronous notification | Operation scope | Q1: covered by ADR-002; ADR Q1 → NO; also Q3: async→sync | HALT | YES — order processing outage on first notification service incident |

---

### Why this matters

The four task descriptions in Phase 5 map to different points on the "danger is visible" spectrum. Task 3 is the least dangerous: the CI Pact job would catch it. Task 1 is systemic but requires a second event (a contract-breaking change) to produce a production failure. Task 2 produces an immediate financial failure — charges for unfulfillable orders — and is caught by the Gherkin test if the spec was written well enough.

Task 4 is the most dangerous task in this set. The notification-synchronous change would cause the most damage in production if no eval existed, and the reason is specific: it is the only change that passes all 15 tests, looks like an improvement, is phrased as adding reliability, violates an architectural invariant that no test asserts, and produces a complete order processing outage rather than a partial or isolated failure. The test suite has no assertion for "the notification call is asynchronous." ADR-002 exists precisely because this invariant cannot be tested in the current spec — it can only be prevented.

---

## Phase 6 — CLAUDE.md pre-flight eval section

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Added a "Pre-flight evals" section to CLAUDE.md with the action-to-eval mapping table and the HALT instruction.

### What happened

The section was added between the "Before modifying covered code paths" ADR protocol and the "External dependencies" table. The table has three rows: infrastructure files → environment eval, `app/main.py` or `tests/` → operation scope eval, `wiremock/` or `pacts/` → contract pre-flight eval.

The HALT instruction in the section matches the instruction in each eval document: HALT means flag to the human author and wait. It cannot be overridden by task urgency, confidence, or prior approval. This is explicit because the most common reason agents override safety checks is implicit: the agent concludes that confidence in the specific change justifies skipping the check. The CLAUDE.md instruction makes the non-overridability explicit rather than leaving it as an implication.

---

## Phase 7 — Full suite verification

**Date:** 2026-07-05
**Status:** ✅ Worked

```text
pytest tests/steps/ -v
→ 11 passed

pytest tests/pact/ -v
→ 4 passed

python3 scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

All 15 tests pass. The eval documents are new artifacts — they introduce no implementation changes, so the test suite verifies that no regression was introduced.

---

### Why this matters

The session that most clearly defines the gap being filled is Issue #16. The dangerous improvement (concurrent inventory+payment) passed an ad-hoc smoke test, failed the Gherkin suite, and required a revert. The test caught it. The question left open: what about the changes that the test doesn't catch?

This session builds the answer: three evals that between them address the changes the Gherkin suite cannot catch — infrastructure weakening (Q2 of the environment eval), asynchronous-to-synchronous coupling (Q3 of the operation scope eval), and contract drift in the sub-threshold timing band (Q3 of the contract pre-flight eval). Each eval is a question that runs before code is written. Each HALT condition is a specific, named situation where the agent's confidence in the change is irrelevant — not because confidence is always wrong, but because these specific situations have already demonstrated that confident changes produce production failures.

The most important sentence in this session: Task 4 — making the notification call synchronous — would cause the most production damage of the four demonstrations, and it is the only one the test suite cannot catch, because there is no test for "the notification call is asynchronous." That is not a failure of the test suite. It is an accurate reflection of what behavioral tests can express and what they cannot. The eval covers the remainder.
