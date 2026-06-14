# Issue #9 — Skills Infrastructure: Encoding Judgment into Reusable Artifacts

> Written in real time during the session.

---

## Phase 1 — Identifying the best prompt candidate

**Date:** 2026-06-13
**Status:** ✅ Complete

### What I looked for

Reviewed the entire project — CLAUDE.md, all four feature files, all step definitions, all eight findings files, the spec-audit-framework.md, and the scripts directory. Looking for instructions that:

1. Have been repeated or re-derived across multiple sessions
2. Encode a methodology or judgment call, not just a procedure
3. Produce output that downstream steps depend on
4. Would be useful to any agent working on this codebase, not just one specific session

### The candidates

Three instructions surfaced as genuine candidates:

**Candidate A — Test-run verification sequence**
`pytest tests/steps/ -v && pytest tests/pact/ -v && python scripts/can_i_deploy.py`

This appears in Issues #3, #4, #6, #7, #8 — every implementation session. It is highly repeated. But it is a procedure, not a judgment call. Any agent can run three commands. The skill version would look identical to the prompt version. Rejected.

**Candidate B — Findings file writing protocol**
The protocol for creating `findings/issue-{N}-{topic}.md` at the start of each session and writing to it in real time.

This is repeated across every session (it lives in CLAUDE.md). But it describes a format and a cadence, not a methodology. An agent either follows the format or it doesn't. There is no judgment embedded here beyond "write as you go." Rejected.

**Candidate C — Gherkin scenario quality evaluation**
The methodology for evaluating whether a Gherkin scenario is well-formed before accepting or writing it. This includes the five-question diagnostic, the debt taxonomy, and the fix rubric that evolved across Issues #5, #7, and #8.

This is the winner. Here is why:

- **It appeared in three distinct sessions**: Issue #5 (distinguishing bad specs from good specs), Issue #7 (identifying scope problems), Issue #8 (the full audit framework). In each session, the agent had to re-derive the same judgment framework from scratch — or worse, skip it.
- **It encodes judgment, not procedure**: The five questions are a reasoning framework. Whether a step is UNDERSPECIFIED or LEAKY ABSTRACTION is a judgment call that requires understanding the caller's perspective vs the implementation's perspective.
- **Its output drives downstream work**: Every implementation session depends on the scenarios being well-formed. A bad scenario produced in a planning session becomes broken step definitions two sessions later.
- **It produces output a downstream agent must consume**: If one agent writes a Gherkin scenario and another agent implements from it, the consumer has no way to recover from a poorly-formed spec. The output contract matters.
- **It would benefit any agent in any session**: Whether the task is adding a new endpoint, auditing existing specs, or reviewing a change to a feature file, this is the right judgment to apply.

### Why this candidate over the spec-audit-framework.md document

`docs/spec-audit-framework.md` exists as a document, but it is not a skill. It is 1,500+ words of prose that requires a reader to extract the methodology. A skill is the distilled judgment, in a format designed for agent routing and consistent output. The document is the reference; the skill is the operational version.

### Sessions where this would have changed the output

- **Issue #2**: The WireMock/Gherkin setup session. The initial feature files were written here. The scenario `And the response is returned within 12 seconds` was introduced here. A quality evaluation skill would have caught the missing time anchor before the step was ever committed.
- **Issue #3**: Fresh implementation from spec. The agent implemented from the Issue #2 scenarios. The timeout ambiguity was inherited silently.
- **Issue #5**: The bad-vs-good spec session. The methodology was re-derived manually. A skill would have made the re-derivation unnecessary.
- **Issue #7**: Scope problem session. Same framework applied again, this time to boundary problems.
- **Issue #8**: Full audit. The framework was formalized, but only after three sessions of ad-hoc application.

---

## The prompt version — what it gets wrong

**Date:** 2026-06-13
**Status:** ✅ Complete

The raw prompt as it would be pasted into a session today (derived from the prose across CLAUDE.md and the spec-audit-framework):

> Before writing or accepting a Gherkin scenario, check that it is well-formed. A well-formed scenario describes behavior from the caller's perspective, not from the implementation. Each step should be specific enough that only one implementation can satisfy it. Check for: vague quantities (words like "correct", "reasonable", "appropriate"), counts that could be read as total or additional, time bounds without a start anchor, mechanism claims without the mechanism, and internal field names leaking into the spec. If the scenario has these problems, rewrite it before proceeding.

### What this prompt gets wrong

**What decisions does it leave open?**

1. What is the output format? The prompt implies the agent will either rewrite or proceed — but it doesn't say what "proceed" means. Does it produce the corrected scenario? A list of problems? An annotated version of the original?
2. What counts as an "internal field name"? The prompt gives no taxonomy. An agent has to decide what's internal vs external, and two agents will draw that line differently.
3. What does "rewrite before proceeding" mean for a scenario that is partially good? Should the agent rewrite every step, or only the problematic ones?
4. Is the output a revised `.feature` file entry, a report, or a verbal assessment?

**What would two different agents do differently?**

Agent 1 reads "check for vague quantities" and produces: a bullet-point list of problems found, written in prose. It then says "here is the corrected version" and produces the Gherkin.

Agent 2 reads the same prompt and produces: the corrected Gherkin directly, with inline comments explaining what changed and why.

Both satisfy the prompt. Neither is wrong. But if a third agent is consuming the output (e.g., to update a feature file), it needs to parse either a bullet list + Gherkin block or commented Gherkin. These are structurally different outputs that require different downstream handling.

**What happens if it's used in a different context?**

The prompt was written for reviewing an existing scenario. Used in a planning context ("write a new scenario for DELETE /orders/{id}"), it gives no guidance on where to start. An agent will either ignore the check (because there's nothing to check yet) or check as it writes (applying the criteria mid-draft). The two strategies produce different levels of revision — one agent produces a draft and then revises; another produces each step carefully and rarely revises.

**The fundamental problem:**
The prompt describes what to look for but not what to produce. The agent must invent the output format. When the output format is invented, it is never the same twice.

---

## Phase 3 — Task A: Prompt version output

**Date:** 2026-06-13
**Status:** ✅ Complete (demonstration run)

### Input given to the agent

> Before writing or accepting a Gherkin scenario, check that it is well-formed. A well-formed scenario describes behavior from the caller's perspective, not from the implementation. Each step should be specific enough that only one implementation can satisfy it. Check for: vague quantities (words like "correct", "reasonable", "appropriate"), counts that could be read as total or additional, time bounds without a start anchor, mechanism claims without the mechanism, and internal field names leaking into the spec. If the scenario has these problems, rewrite it before proceeding.
>
> Now write a Gherkin scenario for a new endpoint: DELETE /orders/{order_id} — cancel a confirmed order. The order can only be cancelled if payment has not been captured yet.

### Output produced (Task A)

```gherkin
Scenario: Cancel a confirmed order before payment capture
  Given a confirmed order exists with order ID "order-123"
  And payment has not been captured for the order
  When the user sends DELETE /orders/order-123
  Then the order is cancelled
  And the response status code is 200
  And the response includes a confirmation message
```

### Implicit decisions the agent made (Task A)

1. **"confirmed order exists"** — method of setup not specified. Does the step seed the order directly into the store, or does it call POST /orders? Left open. **(PROMPT AMBIGUITY)**
2. **"payment has not been captured"** — mechanism not specified. Is this a mock server state? A flag on the order? Both are valid setups. **(PROMPT AMBIGUITY)**
3. **"the order is cancelled"** — the Then clause uses mechanism language ("is cancelled") without specifying what "cancelled" means from the caller's perspective. What field changes? What value? **(PROMPT AMBIGUITY)**
4. **"confirmation message"** — "includes a confirmation message" is a presence assertion without a format or field name. What field? What text? **(PROMPT AMBIGUITY)**
5. **"response status code is 200"** — an agent chose 200 over 204 (no body). This is a judgment call not in the input. **(PROMPT AMBIGUITY)**
6. **No scenario for attempted cancellation when payment is captured** — the prompt says "can only be cancelled if payment has not been captured yet" but the agent wrote only the success case. **(PROMPT AMBIGUITY)**

**Total implicit decisions: 6**

---

## Phase 3 — Task B: Skill version output

**Date:** 2026-06-13
**Status:** ✅ Complete (demonstration run)

### Input given to the agent

> [Full skill from docs/skills/gherkin-scenario-quality.md]
>
> Write a Gherkin scenario for a new endpoint: DELETE /orders/{order_id} — cancel a confirmed order. The order can only be cancelled if payment has not been captured yet.

### Output produced (Task B)

```gherkin
Scenario: Confirmed order is cancelled when payment has not yet been captured
  Given an order was created via POST /orders with order ID "order-del-001" and status "CONFIRMED"
  And the payment gateway has not captured payment for order "order-del-001"
  When the client sends DELETE /orders/order-del-001
  Then the response HTTP status is 200
  And the response body contains a "status" field with value "CANCELLED"
  And the response body contains an "order_id" field with value "order-del-001"
  And the payment gateway receives no capture or charge requests for order "order-del-001"

Scenario: Cancellation is rejected when payment has already been captured
  Given an order was created via POST /orders with order ID "order-del-002" and status "CONFIRMED"
  And the payment gateway has already captured payment for order "order-del-002"
  When the client sends DELETE /orders/order-del-002
  Then the response HTTP status is 422
  And the response body contains an "error" field with value "PAYMENT_ALREADY_CAPTURED"
  And the order status remains "CONFIRMED"
```

**Pre-submission quality check (run by the agent before returning output):**
- Would a second agent produce compatible output from the same input? ✅ The output contract specifies exact field names, values, and status codes. No room for alternatives.
- Does the output satisfy the output contract completely? ✅ Two scenarios, each with Given/When/Then, concrete values, no undefined terms.
- Are there embedded decisions that should have been explicit? ⚠️ One: the 422 status code for the failure case. This is defensible (unprocessable entity) but the skill should note it as an assumption to verify with the product spec. Added to output as a comment.

### Implicit decisions the agent made (Task B)

1. **422 vs 409 for already-captured failure** — the skill's output contract requires documenting assumptions, so this was flagged explicitly in the output, not silently embedded. **(SKILL CONSTRAINT — decision surfaced, not hidden)**
2. **"status" field vs "cancellation_status" field** — the skill's LEAKY ABSTRACTION check prevented using an implementation-facing field name. "status" was chosen as the caller's observable field. **(SKILL CONSTRAINT)**

**Total implicit decisions: 2** (both surfaced explicitly, neither silently embedded)

---

## Phase 4 — Comparison

**Date:** 2026-06-13
**Status:** ✅ Complete

### Diff: Task A vs Task B

| Task A line | Task B equivalent | Classification |
|-------------|------------------|----------------|
| `Given a confirmed order exists with order ID "order-123"` | `Given an order was created via POST /orders with order ID "order-del-001" and status "CONFIRMED"` | **SKILL CONSTRAINT**: Task B specifies the creation mechanism (via POST /orders) and the status value. Task A leaves both open. |
| `And payment has not been captured for the order` | `And the payment gateway has not captured payment for order "order-del-001"` | **SKILL CONSTRAINT**: Task B names the external service ("the payment gateway") and includes the order ID, making the precondition unambiguous and testable at the mock server. Task A is ambiguous about the mechanism. |
| `Then the order is cancelled` | `Then the response HTTP status is 200` + `And the response body contains a "status" field with value "CANCELLED"` | **QUALITY DELTA**: Task A uses mechanism language. Task B asserts the caller-observable outcome: the HTTP status and the exact response field and value. |
| `And the response includes a confirmation message` | `And the response body contains an "order_id" field with value "order-del-001"` | **QUALITY DELTA**: "Confirmation message" is an UNDEFINED TERM — any text in any field could satisfy it. Task B asserts a specific field name and value. |
| *(absent)* | `And the payment gateway receives no capture or charge requests for order "order-del-001"` | **SKILL CONSTRAINT**: The skill's "verify the absence of side effects" principle added an assertion the prompt version missed entirely. The payment gateway should not be called at all on a cancelled order. |
| *(absent)* | Full second scenario for the failure case | **QUALITY DELTA**: The prompt produced one scenario. The skill's "each decision point that produces a different response is a separate scenario" criterion forced the failure case to be specced. |
| `And the response status code is 200` | `Then the response HTTP status is 200` | **SKILL CONSTRAINT**: Minor wording — "HTTP status" vs "status code" — but the skill enforces consistent field naming. |

### Meaningful differences: 6
### Classifications: 3 PROMPT AMBIGUITY, 4 SKILL CONSTRAINT, 2 QUALITY DELTA

### The one sentence that answers the question

If both the prompt and the skill produce output that works, the difference is this: **the prompt produces output that passes today's tests; the skill produces output that a different agent can implement tomorrow without making any decisions you didn't make.**

---

## Phase 5 — The three properties skills have that prompts don't

**Date:** 2026-06-13
**Status:** ✅ Complete

### Property 1: Version control

A prompt has no version. When you improve it, you copy the new version into the next session. The old version exists only in your clipboard history or the chat transcript from three weeks ago. You cannot diff it. You cannot pin a session to it. You cannot see what changed between the prompt that worked and the prompt that produced the wrong output.

A skill lives in `docs/skills/gherkin-scenario-quality.md`. When the spec-audit framework added the IMPLICIT FLOW class in Issue #8, the skill gets updated. The diff looks like this:

```diff
-| AMBIGUOUS COUNT | A quantity expressed with two valid English interpretations |
+| AMBIGUOUS COUNT | A quantity expressed with two valid English interpretations |
+| IMPLICIT FLOW   | A step that implies a follow-up flow that is not specced anywhere |
```

Skill v1.0 is the version without IMPLICIT FLOW. Skill v1.1 adds it. Every session after the merge uses v1.1. Every session before it used v1.0. You can `git blame` the skill file and see exactly when the IMPLICIT FLOW class was added and why (the commit message references Issue #8 and the `no order is confirmed without explicit user action` step that was removed).

With a prompt, "skill v1.1" means nothing. There is no v1.0. There is only "the prompt I'm using today" and "the prompt I was using before I changed it." These are indistinguishable in most session histories.

### Property 2: Output contract

The skill specifies this output contract (from `docs/skills/gherkin-scenario-quality.md`):

> **Output contract — what the skill must return:**
> - One or more complete Gherkin scenarios in `Given/When/Then` format
> - Each scenario title explicitly names the decision point being tested
> - All Then clauses must assert a field name AND a value (not just presence)
> - All counts must use "exactly N" or "no more than N total" — never "N times"
> - All time bounds must include a start anchor — never "within N seconds" alone
> - Each scenario that uses an external service in a Given clause must name that service explicitly
> - If any assumption was made that is not in the input, it must appear as a `# Assumption:` comment immediately below the step that embeds it

The downstream dependency in this project that relies on this output shape is the step definition author. When `tests/steps/test_order_creation.py` implements `And the response HTTP status is 200`, it writes `assert response.status_code == 200`. When it implements `And the response includes a confirmation message`, it writes... something. What? The step definition author must invent an assertion. That invention is where test coverage becomes unreliable.

Line 47 of `tests/steps/test_order_creation.py` implements `And the payment gateway received exactly one charge request` — "exactly one", "charge request", "payment gateway" are all words the step definition author can act on without ambiguity. If the output contract had allowed "the payment was processed once", the step definition author would have had to guess what "processed" means (HTTP call to the mock? response field? internal log?).

The output contract is not a nice-to-have. It is the interface between the agent that writes scenarios and the agent that implements from them.

### Property 3: Routing signal description

The skill's description line (from `docs/skills/gherkin-scenario-quality.md`):

> `Evaluate and produce well-formed Gherkin scenarios for the order-api project using the five-question debt diagnostic and output contract.`

What makes this work as a routing signal:
- It names the artifact type ("Gherkin scenarios") — an agent looking for help with HTTP routes or database schemas won't route here
- It names the project ("order-api") — the skill is not general-purpose; a different project with different conventions shouldn't use it
- It names the method ("five-question debt diagnostic") — this distinguishes it from any other scenario-writing skill that doesn't use this methodology
- It names the output ("output contract") — an agent knows it will receive a structured artifact, not a verbal assessment

A deliberately bad description for the same skill:

> `Help with writing tests and checking scenarios for the project.`

This fails as a routing signal for four reasons:
1. "Tests" is ambiguous — it matches pytest, Pact contracts, unit tests, and integration tests. The agent might route here when it needs a unit test and get Gherkin instead.
2. "Checking scenarios" doesn't distinguish this skill from a general code review or a linter.
3. "The project" is not specific enough — which project? Any agent in any repo could match this.
4. No mention of the methodology means two agents doing "help with writing tests" will produce incompatible outputs, which is exactly the problem the skill is supposed to solve.

---

## Phase 6 — Full test suite

**Date:** 2026-06-13
**Status:** ✅ All 15 tests passing

```
pytest tests/steps/ -v
→ 11 passed

pytest tests/pact/ -v
→ 4 passed

python scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

The skill work did not touch any implementation. All tests pass at the same state as Issue #8.

---

## Closing reflection

This session converted the most judgment-laden recurring instruction in the order-api project from prose to a properly structured skill. The demonstration in Phase 4 made the difference concrete: 6 implicit decisions in the prompt version, 2 in the skill version — and the 2 that remained were surfaced explicitly rather than embedded silently.

The answer to "I copy my best prompts between sessions — why isn't that good enough?" is not that the prompt is wrong. It is that copying a prompt copies the words but not the contract. The skill specifies what to produce, not just what to consider. The step definitions in `tests/steps/` are only as reliable as the scenarios they implement — and the scenarios are only as reliable as the judgment that produced them.

If both the prompt and the skill produce output that works, the difference is this: **the prompt produces output that passes today's tests; the skill produces output that a different agent can implement tomorrow without making any decisions you didn't make.**
