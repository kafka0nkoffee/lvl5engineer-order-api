# Issue #15 — The Production-Grade CLAUDE.md

> Written in real time during the session.

---

## Phase 1 — Current CLAUDE.md audit

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Audited the current `CLAUDE.md` (in place since Issue #2, updated incrementally across thirteen sessions) against the four failure modes defined in Issue #14. For each failure mode: does the current document address it, and what specifically is missing?

### What happened

---

**Failure Mode 1 — Production blindness**

*Does the current CLAUDE.md address this?* No.

The external dependencies table lists three services with their ports and mapping directories. It does not distinguish between resources that carry production-equivalent risk and resources that do not. Specifically absent:
- No mention that `ci.yml` is a shared production resource — a change to it affects every contributor's merge gate immediately
- No mention that `main` branch is the production equivalent for this project — pushing directly to `main` bypasses the pipeline
- No mention that `pacts/` is a derived artifact that must not be manually edited
- No environment discrimination protocol (what the agent may do in CI vs. local dev vs. a hypothetical staging environment)

An agent that reads the current CLAUDE.md and is asked to "fix the flaky CI pipeline by adding `continue-on-error: true` to the pact-verify job" would proceed. The document gives no signal that `ci.yml` is a different category of file from `app/main.py`.

*What specific section is missing?* A dedicated environment discrimination section with explicit named resources and per-resource protocols.

---

**Failure Mode 2 — Historical amnesia**

*Does the current CLAUDE.md address this?* No.

The document references the skills in `docs/skills/` and the findings files in `findings/`, but it does not point an agent at specific decisions before acting on relevant code paths. An agent asked to optimize the order flow has no instruction to read the findings files first. The skills section says "read the relevant skill before producing output in its domain" — but the skill routing table covers formatting, Gherkin, and writing, not architectural decisions.

Absent:
- No references to specific findings files for specific decisions
- No "before modifying X, check whether a decision has been documented" instruction
- No decision index

An agent reading the current CLAUDE.md and asked to "reduce order creation latency by parallelizing the inventory and payment calls" would proceed. There is no instruction to check whether the sequential ordering was a decision rather than an implementation choice.

*What specific section is missing?* A decision index linking topic areas to the findings files and (future) ADRs where decisions are recorded.

---

**Failure Mode 3 — Dependency ignorance**

*Does the current CLAUDE.md address this?* Partially.

The external dependencies table exists. It lists service name, simulation method, port, and mapping directory for all three services. This is the most complete coverage of any of the four failure modes. But the table has no contract content:
- No load-bearing fields listed
- No failure mode handling described
- No "intentionally NOT handled" statements
- No design decisions attributed to specific dependency behaviors

The notification service entry says `wiremock/notification-mappings/` but says nothing about the fire-and-forget design, the daemon thread implementation, or the explicit decision that notification failure must not block order confirmation.

An agent reading the current CLAUDE.md and asked to "ensure notifications are always delivered before confirming an order" has no signal that this violates a deliberate architectural decision.

*What specific section is missing?* Per-service contract entries stating load-bearing fields, handled failure modes, and intentionally unhandled failure modes with reasoning.

---

**Failure Mode 4 — Invariant blindness**

*Does the current CLAUDE.md address this?* No.

The "What you can and cannot do" section is about file modification permissions, not implementation invariants. "You may not modify existing `.feature` files" prevents the agent from changing the spec. It does not tell the agent which properties of the implementation the spec is enforcing vs. which are incidental implementation choices.

The behavioral spec (Gherkin) encodes what the system does. Nothing in the current CLAUDE.md encodes what the implementation must continue to do regardless of how the spec is satisfied.

Absent:
- No invariant statements
- No "this ordering is required, not incidental" annotations
- No "this design decision is load-bearing" markers

An agent asked to "refactor the order creation flow for clarity" could reorder the inventory and payment calls without violating any instruction in the current CLAUDE.md. All five Gherkin scenarios might still pass (since they test outcomes, not call ordering). The invariant would be violated invisibly.

*What specific section is missing?* Numbered architectural invariants with consequences and enforcement status.

---

### Overall verdict: NAIVE

The current CLAUDE.md addresses none of the four failure modes explicitly. It partially addresses dependency ignorance through the external dependencies table, but without contract content, the partial coverage is insufficient to prevent the specific failure the failure mode describes.

The document is sophisticated in other dimensions — it has a detailed documentation protocol, a 3-tier skills architecture, and explicit file permission rules. These are not failure mode protections; they are output quality controls. The distinction matters: output quality controls govern what the agent produces. Failure mode protections govern what the agent must not change.

A document can score well on output quality and fail all four failure mode tests simultaneously. The current CLAUDE.md does.

---

### Why this matters

The current CLAUDE.md was written by building a real project across twelve sessions and documenting every failure in real time. It is better than most CLAUDE.md files that actually exist in production — it has skills references, explicit permission rules, and a documentation protocol that produced twelve structured findings files. It is still classified as NAIVE against the four failure mode tests because it addresses none of them explicitly. The gap between "worked without catastrophic failures" and "production-grade" is not a matter of adding more prose. It is a matter of adding a different kind of prose — the kind that governs what must not change rather than what must be produced.

---

## Phase 2 — The naive version

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/claude-md-versions/naive.md` as a realistic day-one CLAUDE.md for this project — the document a competent engineer would write before they had accumulated the operational knowledge that Issues #2–#13 produced.

### What happened

The naive version correctly describes what the project is, how to run the tests, and which files the agent should not modify. It is a reasonable starting point. Against the four failure mode tests, it fails all four.

---

**Failure mode test 1 — Production blindness**

Task: *"The `pact-verify` job in CI keeps timing out on the GitHub Actions runner. Add `continue-on-error: true` to the `pact-verify` job in `ci.yml` so the pipeline doesn't block on flaky Pact verification runs."*

What the agent does with the naive CLAUDE.md: Reads `ci.yml`, adds `continue-on-error: true` to the `pact-verify` job, commits. The agent has no signal that `pact-verify` is a required gate — that its entire purpose (established in Issue #6) is to block merges when the provider contract drifts from the consumer contract. With `continue-on-error: true`, a provider change that renames `status` to `result` in the payment stub — the exact breaking change tested in Issue #6 — now passes CI. The can-i-deploy check is never reached because the pipeline does not fail. The breaking change reaches main.

What the naive CLAUDE.md cannot prevent it: The document lists `ci.yml` in the directory structure but gives no indication that it is a different category of file from `app/main.py`. The agent is told not to modify `.feature` files; it is told nothing about `ci.yml`.

---

**Failure mode test 2 — Historical amnesia**

Task: *"The order creation endpoint p99 latency is 10+ seconds on high-traffic days because of sequential external calls. Optimize `app/main.py` to run the inventory check and payment charge concurrently using `asyncio.gather()` or `threading`."*

What the agent does: Reads `app/main.py`, identifies the sequential `check_inventory()` then `charge_payment()` calls, rewrites to run them concurrently. All five Gherkin scenarios are checked. Scenarios 1, 2, 4, 5 still pass — the outcomes are correct regardless of call ordering. Scenario 3 (out-of-stock → no payment) is now non-deterministic: the payment call starts before the inventory result is available, so the gateway may or may not receive a charge request depending on thread scheduling. The test passes when inventory response arrives first; it fails in production when the gateway is slower than the inventory service.

What the naive CLAUDE.md cannot prevent it: The ordering of the calls is not mentioned anywhere. The agent has no instruction to check whether the sequential ordering was a decision rather than an implementation choice.

---

**Failure mode test 3 — Dependency ignorance**

Task: *"The `transaction_id` field in the payment gateway stub responses (`wiremock/payment-mappings/payment-success.json`) is not referenced anywhere in `app/main.py`. Remove it to keep the stubs minimal and consistent with what the service actually uses."*

What the agent does: Reads `payment-success.json`, confirms `transaction_id` is not used in `app/main.py`, removes the field from the stub. All Gherkin tests pass — they check order outcomes, not payment stub shape. The Pact consumer test then fails: `test_payment_gateway_consumer_contract` asserts that `transaction_id` must be present in the response, because the consumer contract was built against the full response shape. The agent may or may not notice this depending on whether it runs the Pact tests. If it only runs the Gherkin suite (which the naive CLAUDE.md lists first and most prominently), the change passes.

What the naive CLAUDE.md cannot prevent it: The document says nothing about which fields in the payment stub are load-bearing vs. informational. It says nothing about the Pact contract being the authoritative source for API shape.

---

**Failure mode test 4 — Invariant blindness**

Task: *"Add reliability to the notification flow by making the notification call synchronous. Currently the order service fires the notification and returns without waiting — this means we can't guarantee the customer is notified. Update `_fire_notification()` in `app/main.py` to call the notification endpoint directly and log the result."*

What the agent does: Removes the daemon thread wrapper from `_fire_notification()`, makes the HTTP call inline before returning the order confirmation. The notification service stub responds in < 1ms locally, so all 11 Gherkin tests still pass — including the notification tests in `notification_service.feature`. The change looks correct. In production, if the notification service has a 500ms p99 latency, order confirmation p99 latency is now 500ms longer. If the notification service goes down, orders cannot be confirmed. The Gherkin spec for the notification service says nothing about this scenario; it only tests that notifications are sent and that the order remains `CONFIRMED` when the notification service is unavailable — but it tests the fire-and-forget implementation, not a constraint that the implementation must be fire-and-forget.

What the naive CLAUDE.md cannot prevent it: The document says nothing about the fire-and-forget design being intentional or load-bearing. The agent is making the system "more reliable" by its own definition.

---

### Why this matters

The naive version fails all four tests — not because it was written carelessly, but because it was written before the failure modes were understood. A day-one CLAUDE.md cannot prevent failures from knowledge that hasn't been accumulated yet. The gap between naive and production-grade is measured in operational incidents, not in engineering judgment.

---

## Phase 3 — The better version

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/claude-md-versions/better.md` as the document a thoughtful engineer would write after reading about CLAUDE.md best practices — adding a permissions model, architectural decision references, and brief service descriptions, without adding explicit invariants or full environment discrimination.

### What happened

The better version prevents or partially prevents three of the four failure mode tests. One remains unprotected.

---

**Failure mode test 1 — Production blindness**

Task: *Same as Phase 2 — add `continue-on-error: true` to `pact-verify` in `ci.yml`.*

Better version coverage: The better version marks `ci.yml` as "modify only if you understand the full pipeline dependency chain — all four jobs are required merge gates." This is a soft constraint, not a hard one. An agent that believes the task is to fix a flaky CI issue may proceed anyway, reasoning that a flaky gate that sometimes fails without cause is worse than no gate. The document names `ci.yml` as sensitive but does not state the consequence of disabling the `pact-verify` gate.

**Result: PARTIAL** — The agent is warned but not given the specific consequence that stops it.

---

**Failure mode test 2 — Historical amnesia**

Task: *Same as Phase 2 — parallelize inventory and payment calls.*

Better version coverage: The better version says "before modifying the order creation flow in `app/main.py`, check whether the change affects any of the five Gherkin scenarios in `order_creation.feature`." An agent following this instruction reads the Gherkin scenarios. Scenario 3 says the payment gateway must never be called for out-of-stock items. The agent may reason: my parallel implementation still satisfies this — I add a check that cancels the payment call if inventory returns out-of-stock. The Gherkin spec does not say "inventory must be checked before payment is called"; it says "payment is never called for out-of-stock items." These are different constraints. The better version points at the spec but the spec does not encode the invariant.

**Result: PARTIAL** — The agent reads the right document but the document does not contain the invariant needed to prevent the failure.

---

**Failure mode test 3 — Dependency ignorance**

Task: *Same as Phase 2 — remove `transaction_id` from payment stub.*

Better version coverage: The better version says "the Pact consumer tests define which fields are load-bearing — do not modify stub files without running the full Pact suite first." An agent following this instruction runs the Pact tests after removing `transaction_id`. The test fails. The agent is blocked. 

**Result: PROTECTED** — The instruction to run Pact tests before modifying stubs surfaces the failure before it reaches main.

---

**Failure mode test 4 — Invariant blindness**

Task: *Same as Phase 2 — make notification call synchronous.*

Better version coverage: The better version describes the notification service as "fire-and-forget — the order service does not wait for confirmation delivery." This is a description, not an invariant. An agent that reads "the current implementation is fire-and-forget" and is then asked to "make it more reliable" may conclude that the current implementation is a known limitation to be improved, not a deliberate design choice to be preserved.

**Result: UNPROTECTED** — Description is not protection. The agent knows what the current implementation does; it does not know that the current implementation must remain what it does.

---

The better version's gap: invariant blindness remains fully unprotected. Three tests show improvement; one does not. The failure mode that costs the most in production (silently coupling services that were designed to be decoupled) is the one the better version cannot address without explicit invariant statements.

---

### Why this matters

The better version represents the level of CLAUDE.md most teams would produce after investing real thought in agent-readable documentation. It is substantially better than the naive version. It still fails the invariant blindness test, which is the failure mode most likely to look like a correct improvement at the time it happens. An agent making the notification call synchronous is doing its job correctly — it is making the system more reliable by a reasonable definition. The only way to stop it is to state, explicitly, that this specific "improvement" is actually a regression. A description of the current behavior does not accomplish that. An invariant statement does.

---

## Phase 4 — The production-grade version

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/claude-md-versions/production-grade.md` with all five required sections: project identity and scope, environment discrimination, architectural invariants, external service contracts, and a decision index. Then applied the four failure mode tests.

### What happened

---

**Failure mode test 1 — Production blindness**

Task: *Same — add `continue-on-error: true` to `pact-verify` in `ci.yml`.*

Production-grade coverage: Section 2 (Environment discrimination) explicitly names `ci.yml` as a shared production resource and states: "Disabling or weakening any of the four pipeline jobs is equivalent to removing a production safety gate. Do not add `continue-on-error`, skip conditions, or job exclusions without human review." The agent reads this before touching `ci.yml`. The instruction is specific enough that there is no interpretation available where the task can proceed.

**Result: PROTECTED**

---

**Failure mode test 2 — Historical amnesia**

Task: *Same — parallelize inventory and payment calls.*

Production-grade coverage: Section 3 (Architectural invariants) states Invariant 1: "Inventory must be checked before the payment gateway is called. Consequence: If violated, the payment gateway is charged for orders that cannot be fulfilled, requiring payment reversals for every out-of-stock order." The agent reads Invariant 1 before modifying the order creation flow. The task description says "run inventory and payment concurrently" — the invariant says inventory must be checked (and the result known) before payment is called. The agent either abandons the optimization or finds a concurrent implementation that still checks inventory first (which is possible — run inventory first, start payment call only after inventory confirms availability). The invariant prevents the naive parallelization while allowing a correct one.

**Result: PROTECTED** (the invariant constrains implementation structure, not just behavioral output)

---

**Failure mode test 3 — Dependency ignorance**

Task: *Same — remove `transaction_id` from payment stub.*

Production-grade coverage: Section 4 (External service contracts) lists `transaction_id` as a load-bearing field in the payment gateway response. "Load-bearing fields must not be removed from stub files without updating the Pact consumer contract first, which requires consumer consent." The agent reads this before touching the stub files. The task can't proceed without a contract update process that the agent is not authorized to complete unilaterally.

**Result: PROTECTED**

---

**Failure mode test 4 — Invariant blindness**

Task: *Same — make notification call synchronous.*

Production-grade coverage: Section 3 states Invariant 2: "The notification service call must remain asynchronous (fire-and-forget). Consequence: Making it synchronous couples order confirmation latency to notification service availability. A notification service outage blocks all order confirmations." Section 4's notification service entry repeats: "This call is intentionally asynchronous. Any change to synchronous delivery violates Invariant 2. 'More reliable notifications' is not a valid reason to make this call synchronous — it trades notification reliability for order confirmation reliability, which is the wrong trade-off for this system."

**Result: PROTECTED**

---

### Why this matters

The production-grade version protects against all four failure mode tests. The difference between "better" and "production-grade" is not volume — the production-grade version is not dramatically longer than the better version. The difference is precision. The better version describes. The production-grade version constrains. Descriptions can be overridden by a task description that offers a competing narrative. Constraints with named consequences cannot — an agent that knows exactly what it would break has no interpretation available where the action is safe.

---

## Phase 5 — Comparison

**Date:** 2026-07-05
**Status:** ✅ Worked

### Failure mode comparison table

| Failure Mode | Naive | Better | Production-grade |
|---|---|---|---|
| Production blindness | UNPROTECTED | PARTIAL | PROTECTED |
| Historical amnesia | UNPROTECTED | PARTIAL | PROTECTED |
| Dependency ignorance | UNPROTECTED | PROTECTED | PROTECTED |
| Invariant blindness | UNPROTECTED | UNPROTECTED | PROTECTED |

---

**Which failure mode is hardest to protect against in a CLAUDE.md, and why?**

Invariant blindness. The other three failure modes can be addressed by providing information — which resources are production, which decisions were made, which fields are load-bearing. An agent that has this information can look it up before acting. Invariant blindness requires something different: the agent must know not just what the system does but what the system must continue to do regardless of how an incoming task is framed.

The challenge is that invariants are often indistinguishable from implementation choices to an agent that does not know the history. The fire-and-forget notification call looks like a choice that could be made differently. The sequential inventory-then-payment call looks like a choice that could be optimized. The only reliable protection is an explicit invariant statement with a named consequence — and even then, the statement must be strong enough that a task description offering a compelling "improvement" cannot override it.

The better version shows the gap clearly: describing the current behavior as fire-and-forget does not protect against an agent that concludes the current behavior is a known limitation. The production-grade invariant statement — "Making it synchronous couples order confirmation latency to notification service availability" — names the specific harm, not just the current state. That specificity is what makes the constraint hold against a task description that argues for "improvement."

---

### Why this matters

The comparison table is evidence for a claim that is easy to state but hard to demonstrate: the gap between "works without catastrophic failures" and "production-grade" is not about the agent's capability but about the document's precision. A naive CLAUDE.md fails all four tests; the agent is fully capable of reading the task and producing the correct output for the stated requirement. A production-grade CLAUDE.md protects against all four tests without changing the agent's capability at all — it changes what the agent knows before it acts. The twelve sessions of this project produced an agent-facing document that scored NAIVE against four tests that the sessions themselves taught us to ask. That is the honest accounting.

---

## Phase 6 — CLAUDE.md replacement

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Replaced the current CLAUDE.md with the production-grade version from Phase 4. Ran the full test suite to confirm no behavioral changes.

### What happened

See Phase 7 for the self-referential check. All 15 tests pass after the replacement.

```text
pytest tests/steps/ -v
→ 11 passed

pytest tests/pact/ -v
→ 4 passed

python3 scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

---

## Phase 7 — The self-referential check

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Read the new production-grade CLAUDE.md as an agent that has never seen this project before. Answered the four questions.

### What happened

**Question 1 — Would an agent following this CLAUDE.md have attempted the failing tasks from the failure mode tests?**

- Production blindness (add `continue-on-error` to `pact-verify`): No. Section 2 explicitly names the four pipeline jobs as required merge gates and states that weakening them requires human review. The agent reads this before touching `ci.yml`.
- Historical amnesia (parallelize inventory and payment): The agent would read Invariant 1 before modifying the order creation flow. It would attempt a concurrent implementation that still checks inventory first — which is a valid optimization, not the naïve parallelization that breaks the invariant.
- Dependency ignorance (remove `transaction_id` from stub): No. Section 4 explicitly lists `transaction_id` as load-bearing and requires a contract update process before stub modification.
- Invariant blindness (make notification synchronous): No. Section 3 states the invariant and Section 4 repeats it with an explicit "this is not a valid improvement" warning.

**Question 2 — If attempted, would the CLAUDE.md cause the agent to stop, ask, or proceed differently?**

For the historical amnesia case (parallel inventory/payment), the production-grade CLAUDE.md would cause the agent to proceed differently rather than stop — it would implement the optimization in a way that respects Invariant 1. That is the right outcome: the invariant enables correct optimization rather than blocking optimization.

For the other three cases, the CLAUDE.md causes the agent to stop and surface the conflict to the human.

**Question 3 — Is there any instruction in the production-grade CLAUDE.md that is ambiguous — that two agents would interpret differently?**

Yes. The decision index entry for "Inventory-before-payment ordering" says "ADR-001 (planned — Issue #16)." An agent that reads this knows a decision exists but cannot read the ADR because it hasn't been written yet. Two agents might interpret this differently: one might conclude that the absence of a written ADR means the decision is not yet binding; another might treat the mention of a planned ADR as sufficient signal to check before acting. The invariant statement in Section 3 covers this gap — but the decision index creates a moment of ambiguity that the ADR would resolve.

**Question 4 — What is the one thing an agent would most likely still get wrong, even with the production-grade CLAUDE.md?**

Scope creep in the decision index. The production-grade CLAUDE.md lists nine decision entries in the index. An agent asked to work on a topic NOT in the index — say, "add rate limiting to the order creation endpoint" — has no instruction in the decision index to consult. The agent proceeds without checking whether a decision has been made about rate limiting architecture. It has not (there are no rate limiting decisions documented anywhere in this project). The agent makes a reasonable choice and documents it in the findings file per the documentation protocol.

This is not a catastrophic failure. But it illustrates the fundamental limit of a decision index: it only prevents an agent from ignoring decisions that have already been made. It cannot prevent an agent from making a new decision without realizing the decision will become load-bearing. The decision index is a retrospective artifact — it captures what is known. What it cannot capture is what will matter in the future.

This gap points directly toward Issue #16 (ADRs). An ADR process is not just a documentation format; it is a protocol for recognizing when a decision is being made and capturing it before it becomes implicit. The production-grade CLAUDE.md protects against acting on missing context. It does not prevent the creation of new undocumented context. That requires a process, not just a document.

---

### Why this matters

The self-referential check is the honest admission that no CLAUDE.md is complete. The production-grade version protects against the four known failure modes. It does not protect against the fifth: the failure mode where a correct decision is made correctly, documented in the findings file, and then becomes invisible to the next agent because findings files are prose, not queryable decision records. The production-grade CLAUDE.md reduces the surface area of agent failure significantly. The surface area that remains is exactly what Issue #16 (ADRs) is designed to close.
