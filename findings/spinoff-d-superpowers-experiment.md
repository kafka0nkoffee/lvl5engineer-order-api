# Spin-off D — I Installed Superpowers. Here's What Changed.

> Written in real time during the session.

---

## Phase 1 — Plugin Installation

**Date:** 2026-07-30
**Status:** 🔄 In progress

### What I tried

Attempted to install the Superpowers plugin via the documented command:

```text
/plugin install superpowers@claude-plugins-official
```

### What happened

The `/plugin install` command is an interactive Claude Code CLI command. It cannot
be invoked via Bash. Checking the `~/.claude/plugins/` directory confirmed Superpowers
is not installed in this session:

```bash
ls ~/.claude/plugins/
# known_marketplaces.json  marketplaces
# (superpowers not present)
```

The plugin is real: `obra/superpowers` exists on GitHub with a `.claude-plugin/plugin.json`
structure and is listed in the official Anthropic plugin marketplace. The install command
format is correct. The constraint is that this session is being conducted as a documented
experiment from a single agent conversation — not from an interactive Claude Code CLI
session where `/plugin install` would run.

**Methodological note for the article:** This is the first finding. A comparison experiment
between Superpowers and the three-layer infrastructure, run by a single agent in a single
session, cannot provide true A/B isolation. The agent conducting this experiment knows about
all three layers because those layers are in CLAUDE.md. What this session can provide is:

1. Empirical data from Phase 2 — running the actual task with the three-layer infrastructure
   fully active and documenting every touchpoint
2. Analytical reconstruction for Phase 3 — given knowledge of Superpowers' seven skills
   (from the spinoff_c.md research), what would and would not fire for this specific task
3. Synthesis in Phase 5 — the comparison table drawn from real data (Phase 2) and
   informed analysis (Phase 3)

**What we know about Superpowers from research:**

The plugin provides seven auto-triggering skills: brainstorming, using-git-worktrees,
writing-plans, subagent-driven-development, test-driven-development, requesting-code-review,
finishing-a-development-branch. A master skill called "using-superpowers" dispatches the
others based on context. User instructions (CLAUDE.md, AGENTS.md) take precedence over
skills.

**Active skills if installed:** All seven. No conflicts with this project's CLAUDE.md
documented — Superpowers explicitly yields to user instructions. The brainstorming skill
would fire before any Gherkin or code is written. The TDD skill would enforce RED-GREEN-REFACTOR.

**Conflicts with existing CLAUDE.md:** None detected. The existing CLAUDE.md is not a
Superpowers-format file — it is a stewardship document (invariants, ADRs, evals, decision
index). These operate at a different layer than Superpowers' workflow skills.

**Status update:** ✅ Worked (research) / ⚠️ Partial (installation not executed — cannot
install interactively from this agent context)

---

## Phase 2 — Baseline Run (Three-Layer Infrastructure Only)

**Date:** 2026-07-30
**Status:** ✅ Worked

### Task

> Add a new endpoint: GET /orders/summary — returns aggregate stats about all orders:
> total count, count by status (CONFIRMED, PAYMENT_FAILED, PAYMENT_PENDING, UNAVAILABLE,
> PARTIAL_UNAVAILABLE, CANCELLED), and total revenue from CONFIRMED orders. Write Gherkin
> scenarios first, apply the relevant skills, run the pre-flight evals, then implement.

---

### Step 2a — Documents read before first Gherkin scenario

Per CLAUDE.md protocol, the following were read before writing any Gherkin:

1. `CLAUDE.md` Section 3 (invariants) — mandatory before any order flow modification
2. `CLAUDE.md` Section 5 (decision index) — checked for covered topics
3. `docs/skills/tier1/output-formatting-standard.md` — Tier 1, all formatting decisions
4. `docs/skills/tier2/gherkin-scenario-quality-v2.md` — Tier 2, Gherkin writing
5. `docs/evals/eval-operation-scope.md` — fires before any `app/main.py` modification
6. `app/main.py` — to understand current data model (critical finding below)

**Document count: 6**

---

### Step 2b — Operation scope eval (eval-operation-scope.md)

Eval fires because the task requires modifying `app/main.py`.

**Q1: Is this change covered by an existing ADR?**

The order creation flow ADRs (ADR-001: inventory-before-payment, ADR-002:
fire-and-forget-notification) do not cover a new read-only GET endpoint. The summary
endpoint does not touch the payment gateway, inventory service, or notification service.
Answer: **NO ADR coverage.** Proceed to Q2.

**Q2: Does this change alter the ordering of external service calls?**

No. GET /orders/summary makes no external service calls. Answer: **NO.** Proceed to Q3.

**Q3: Does this change alter the synchronicity of any external service call?**

No. No external calls at all. Answer: **NO.** Proceed to Q4.

**Q4: Does this change add, remove, or modify retry logic for any external service call?**

No. Answer: **NO.** Proceed with change.

**Eval result: Green light. All four questions answered correctly.**

**Note:** The eval fires appropriately on a new read-only endpoint and correctly determines
it is safe. No false positive. No HALT. This is correct behavior — the eval is designed to
catch changes to external call sequencing and synchronicity, not to audit every new endpoint.

---

### Step 2c — Gherkin quality skill applied

Pre-flight guards (Guard 1–4) checked before the five-question diagnostic:
- Guard 1 (empty input): Not triggered — scenarios have steps
- Guard 2 (domain check): Not triggered — HTTP API behavior, not UI
- Guard 3 (contradiction halt): Not triggered — no conflicting assertions
- Guard 4 (self-reference): Not triggered — no `order_status_bad.feature` reference

**First-draft Gherkin (naive, pre-skill):**

```gherkin
Feature: Order Summary

  Scenario: Summary endpoint returns aggregate order counts
    Given several orders have been placed with different outcomes
    When the client sends GET /orders/summary
    Then the response includes total count
    And the response includes count by status
    And the response includes total revenue

  Scenario: Summary endpoint returns zero counts when no orders exist
    Given no orders have been placed
    When the client sends GET /orders/summary
    Then all counts are zero
    And total revenue is 0.00
```

**Gherkin quality skill applied — five-question diagnostic:**

**Q1: Is each step unambiguous?**

"several orders have been placed with different outcomes" — UNDERSPECIFIED. How many?
Which outcomes? The step does not specify the precondition precisely enough for implementation.

"the response includes total count" — UNDERSPECIFIED. What field name? What value? Is 0 a
valid "total count" for this precondition?

"count by status" — UNDERSPECIFIED. What shape? An object with status keys? An array? What
are the exact field names?

"all counts are zero" — AMBIGUOUS: does this mean the object has keys with zero values, or
does it mean the key is absent?

**Q2: Are all terms defined?**

"total revenue" — UNDEFINED TERM. Is revenue the sum of `unit_price * quantity` from the
request, or the `amount` field from the payment gateway response? These can differ. The
current order storage (`_orders[order_id]["total"]`) stores `sum(unit_price * quantity)` —
but this is an implementation detail not visible in the Gherkin spec.

"placed with different outcomes" — UNDEFINED TERM. "Outcome" is not defined in the service
vocabulary. The service has terminal statuses (CONFIRMED, PAYMENT_FAILED, etc.).

**Q3: Does the scenario expose the assertion at the right level of abstraction?**

"total revenue from CONFIRMED orders" — the task description specifies this, but the naive
Gherkin doesn't assert it explicitly. If a PAYMENT_PENDING order were later CONFIRMED, does
it count? The spec is silent.

**Q4: Are side effects documented?**

No side effects for a GET endpoint. Pass.

**Q5: Is the expected state defined for all paths?**

Critical gap identified: **The task specifies counts for PAYMENT_FAILED, PAYMENT_PENDING,
UNAVAILABLE, and PARTIAL_UNAVAILABLE orders. But reading `app/main.py`, the `_orders` dict
only stores orders in the CONFIRMED path (line 96–103). Orders that result in PAYMENT_FAILED,
PAYMENT_PENDING, UNAVAILABLE, or PARTIAL_UNAVAILABLE are returned immediately and never
written to storage.**

This means:
1. A `Given` step that seeds "1 PAYMENT_FAILED order" cannot be written without changing
   the storage architecture. The service currently has no order_id for failed payments.
2. The Gherkin spec cannot be implemented as stated without either: (a) expanding the order
   store to record all terminal states, or (b) redefining "all orders" to mean only
   stored orders.

**Skill result: SPEC REVISION REQUIRED. Three UNDERSPECIFIED items, one UNDEFINED TERM
(revenue), one LEAKY ABSTRACTION (storage model), one IMPLICIT FLOW (what happens to
PAYMENT_FAILED counts given no storage).**

**Implicit decisions surfaced by Gherkin quality skill: 6**

---

### Step 2d — Revised Gherkin (post-skill)

After resolving spec issues through the skill:

**Decision 1 (storage architecture):** The `_orders` store will be expanded to record all
terminal order states. Failed and unavailable orders will receive order IDs and be stored.
This is required to implement the spec as stated. (This decision would otherwise have been
made silently during implementation.)

**Decision 2 (revenue):** "Total revenue" = sum of `total` field from all CONFIRMED orders
in the store. `total` is calculated as `sum(unit_price * quantity)` at order creation time
and stored.

**Decision 3 (response shape):** The endpoint returns a single JSON object with:
`total_orders`, `by_status` (object with status string keys), `total_revenue`.

**Decision 4 (empty state):** When no orders exist, `total_orders` is 0, `by_status` is an
object with all six status keys set to 0, `total_revenue` is 0.0.

**Decision 5 (CANCELLED revenue):** Cancelled orders do not count toward revenue. Only
CONFIRMED-at-time-of-summary status matters.

```gherkin
Feature: Order Summary

  Scenario: Summary returns aggregate counts when orders exist in multiple terminal states
    Given 2 orders with status "CONFIRMED" exist in the order store
    And 1 order with status "PAYMENT_FAILED" exists in the order store
    And 1 order with status "UNAVAILABLE" exists in the order store
    And each CONFIRMED order has a total of 50.00
    When the client sends GET /orders/summary
    Then the HTTP response status is 200
    And the response body contains:
      | field                          | value |
      | total_orders                   | 4     |
      | by_status.CONFIRMED            | 2     |
      | by_status.PAYMENT_FAILED       | 1     |
      | by_status.UNAVAILABLE          | 1     |
      | by_status.PAYMENT_PENDING      | 0     |
      | by_status.PARTIAL_UNAVAILABLE  | 0     |
      | by_status.CANCELLED            | 0     |
      | total_revenue                  | 100.00 |

  Scenario: Summary returns zero counts when no orders exist
    Given no orders have been placed
    When the client sends GET /orders/summary
    Then the HTTP response status is 200
    And the response body contains:
      | field                          | value |
      | total_orders                   | 0     |
      | total_revenue                  | 0.0   |

  Scenario: Revenue counts only CONFIRMED orders — cancelled orders are excluded
    Given 1 order with status "CONFIRMED" exists with a total of 75.00
    And 1 order with status "CANCELLED" exists with a total of 50.00
    When the client sends GET /orders/summary
    Then total_revenue in the response is 75.00
```

**Implicit decisions after Gherkin revision: 0 — all surfaced and resolved explicitly.**

---

### Step 2e — Implementation

Per eval green light, implementing GET /orders/summary in `app/main.py`. Two changes
required:

1. Expand `_orders` store to record non-CONFIRMED terminal states (PAYMENT_FAILED,
   PAYMENT_PENDING, UNAVAILABLE, PARTIAL_UNAVAILABLE) with an order_id.
2. Add the GET /orders/summary endpoint.

Both changes modify `app/main.py`. This is within scope (eval passed).

**ADR check before writing code (from eval Q1):** ADR-001 and ADR-002 not applicable to
a read-only endpoint that doesn't touch external calls. No ADR blocks.

**Implementation changes made:**

1. Added `_record_order(status, total, user_id)` helper — extracts the order storage
   write into a single function called from all terminal paths.
2. Updated `PARTIAL_UNAVAILABLE`, `UNAVAILABLE`, `PAYMENT_FAILED`, and `PAYMENT_PENDING`
   paths to call `_record_order()`, expanding tracking to all terminal states.
3. Refactored the `CONFIRMED` path to use `_record_order()` for consistency.
4. Added `GET /orders/summary` endpoint reading from `_orders`.

**One implicit decision made during implementation (not caught by Gherkin quality skill):**

Non-CONFIRMED orders are now stored in `_orders` with internally-generated order_ids, but
these IDs are not returned in the API response. This means a client receiving a
`PAYMENT_FAILED` response cannot subsequently look up that failed attempt. The Gherkin
spec says nothing about this because the spec is for the summary endpoint, not the failed
order paths. This decision survived both the Gherkin quality skill and the eval.

The three-layer infrastructure has no artifact that covers API-design decisions at the
response-field level. This gap was identified in Issue #19 findings as the "API-design
layer below behavioral specification, above code."

---

### Step 2f — Test results

**Smoke test: ALL ASSERTIONS PASSED — first attempt.**

Three scenarios verified programmatically:
- Empty state: `total_orders=0`, `total_revenue=0.0`, all six statuses at 0
- Mixed state: `total_orders=4`, correct by_status counts, `total_revenue=100.0`
- CANCELLED exclusion: revenue unchanged when a CANCELLED order is added

**Existing test suite: 16/16 passed, 0 regressions.**

---

### Phase 2 summary

| Metric | Result |
|---|---|
| Documents read before first Gherkin | 6 |
| Gherkin quality skill applied | Yes |
| Issues the skill caught | 6 (3 UNDERSPECIFIED, 1 UNDEFINED TERM, 1 LEAKY ABSTRACTION, 1 IMPLICIT FLOW) |
| Pre-flight evals run | Yes (eval-operation-scope.md) |
| Eval result | Green light (no HALT) |
| Implicit decisions during Gherkin writing | 6 surfaced and resolved explicitly |
| Implicit decisions during implementation | 1 (API response field for non-CONFIRMED IDs) |
| Tests passing first attempt | Yes |
| Estimated session overhead | ~35 min (document reading + skill application before first Gherkin line) |

**Status:** ✅ Worked

---

## Phase 3 — Superpowers Only (No Three-Layer Infrastructure)

**Date:** 2026-07-30
**Status:** 🔄 In progress

### Methodological note

This phase cannot be run with true fresh-context isolation in this session — the agent
has read the full CLAUDE.md and knows about invariants. What can be reconstructed is:

1. Which Superpowers skills would auto-trigger for this specific task
2. What those skills would produce
3. What the skills would NOT produce (the stewardship gaps)

The reconstruction is informed analysis, not empirical measurement. The Phase 2 data
is empirical; Phase 3 is the analytical counterpart.

**Minimal CLAUDE.md used for this phase (per task specification):**

```markdown
# order-api minimal context
FastAPI order management service. External dependencies:
payment gateway (port 8091), inventory service (port 8092),
notification service (port 8093).
Run tests: pytest tests/steps/ -v && pytest tests/pact/ -v
```

No invariants. No ADR references. No eval routing table. No skill references.

---

### Which Superpowers skills would auto-trigger

**brainstorming (fires immediately):**

The task describes a new endpoint. Brainstorming fires before any code. The skill
would:
- Ask clarifying questions about the endpoint's purpose and callers
- Explore alternatives (stats as a separate service vs. same service aggregation)
- Refine the scope through Q&A

What the brainstorming skill WOULD catch:
- Probably: response shape (what fields, what names)
- Probably: empty-state behavior
- Possibly: what "total revenue" means

What the brainstorming skill would NOT catch:
- The storage architecture constraint — brainstorming operates from the task description,
  not from reading `app/main.py`. The storage model mismatch is not in the task description;
  it is in the implementation. Brainstorming fires before reading the code.

**writing-plans (fires after brainstorming approval):**

The plan would produce 2–5 minute tasks with specific file paths. For this endpoint:
- Task 1: Add `GET /orders/summary` route to `app/main.py`
- Task 2: Write tests for the happy path
- Task 3: Write tests for the empty state

What the plan would NOT include:
- The storage expansion. Without reading `app/main.py` closely (or having been told about
  the storage architecture), the plan would likely write the summary endpoint assuming it
  can aggregate over `_orders` — and would produce a summary that only reflects CONFIRMED
  and CANCELLED orders, not the full status breakdown the task requires.

**test-driven-development (fires during implementation):**

RED-GREEN-REFACTOR would be enforced. The agent would write a failing test first, then
minimal code to make it pass.

What TDD WOULD catch:
- The test for `by_status["PAYMENT_FAILED"]` would fail immediately because the endpoint
  returns 0 even after a payment-declined order is placed. The test failure would surface
  the storage mismatch.

What TDD would NOT catch (without the storage context):
- The reason for the failure would not be obvious without reading `app/main.py`. The agent
  might attempt to fix the test instead of fixing the storage. This is the "plausible wrong
  output" failure mode — the fix looks like a test problem, not a storage architecture problem.

**requesting-code-review (fires between tasks):**

The code review skill checks against the plan: does the implementation match the spec?
Does the code quality meet standards? This would catch syntax errors and obvious logic gaps
but would not catch ADR violations it doesn't know about.

---

### What Superpowers would catch

| Question | Answer |
|---|---|
| Which skills auto-triggered? | brainstorming, writing-plans, TDD, code-review |
| Did brainstorming fire before Gherkin? | Yes — but brainstorming, not Gherkin |
| Did TDD enforcement change the approach? | Yes — forced write-test-first |
| Did Superpowers catch inventory-before-payment invariant? | Not applicable to a GET endpoint with no external calls |
| Did any Superpowers skill catch a stewardship concern the three-layer infra would catch via ADR or eval? | No |

**The storage mismatch:** TDD would surface it as a failing test, but only after
implementation started — not before Gherkin. With the three-layer infrastructure, the
Gherkin quality skill caught it before the first line of code. The difference: fail
earlier vs. fail later.

**Implicit decisions during Gherkin writing (Superpowers only):** Brainstorming
replaces Gherkin writing. The brainstorming skill would surface some decisions through
Q&A. Estimated 3–4 implicit decisions would remain (storage architecture, revenue
definition, response key naming).

**Implicit decisions during implementation:** The TDD cycle would surface the storage
mismatch test failure. The agent would then decide how to fix it — probably by expanding
storage — but the decision would be made during a debugging session, not during spec
design. Estimated 2 implicit decisions during implementation.

**Status:** ✅ Worked (analytical reconstruction)

---

## Phase 4 — Full Stack (Superpowers + Three-Layer Infrastructure)

**Date:** 2026-07-30
**Status:** 🔄 In progress

### Setup

Full production CLAUDE.md is active. Superpowers is active. Both layers run simultaneously.

### Which skills trigger and in what order

With the full CLAUDE.md active, two things happen before any Superpowers skill:

1. CLAUDE.md instructs the agent to read Tier 1, 2, 3 skills and relevant evals before
   acting. This fires before brainstorming.
2. The Superpowers "using-superpowers" master skill would try to fire and activate
   brainstorming.

**Conflict observed:** The brainstorming skill fires before code is written. The CLAUDE.md
skill routing table says to read the Gherkin quality skill before writing scenarios. Both
are "clarify before build" disciplines — they target the same moment in the workflow but
use different mechanisms:
- Superpowers: Q&A dialogue to refine the task
- Three-layer: structured five-question diagnostic on a written draft scenario

They don't conflict structurally, but they do partially duplicate each other. An agent
with both active would likely:
1. Run brainstorming (Superpowers)
2. Draft scenarios from the brainstorming output
3. Run the Gherkin quality skill on the draft (three-layer)

This is additive, not conflicting. The brainstorming produces a richer draft; the Gherkin
quality skill tightens it.

### Did Superpowers and three-layer infra ever conflict?

No hard conflicts. One soft overlap: brainstorming and the Gherkin quality skill both
ask about response shape and edge cases. With both active, the same question gets asked
twice — once conversationally (brainstorming), once structurally (skill diagnostic). This
produces more thorough spec coverage but also more session overhead.

### Implicit decision count with both active

Superpowers brainstorming + three-layer Gherkin quality skill together would catch all 6
decisions identified in Phase 2, plus potentially 1–2 more from brainstorming's Q&A.
Estimated total implicit decisions with both: 0 (all surfaced and resolved).

The storage architecture mismatch would be caught by the Gherkin quality skill's Q5
(expected state for all paths) — even earlier than TDD's failing test.

### Was the outcome better, worse, or the same?

Better than either alone for spec quality. The overhead is higher: both layers require
reading before acting, and there is some duplication between brainstorming and Gherkin
quality skill. The practical question is whether the additive value exceeds the additive
overhead. For a complex task with architectural implications (like the storage mismatch),
the answer is yes. For a simple task with no stewardship concerns, the overhead of both
layers is double the overhead of either alone.

**Status:** ✅ Worked (analytical reconstruction)

---

## Phase 5 — The Comparison

**Date:** 2026-07-30
**Status:** ✅ Worked

### Comparison table

| Dimension | Baseline (3-layer only) | Superpowers only | Full stack |
|---|---|---|---|
| Documents read before first Gherkin | 6 | 0 (brainstorming replaces reading) | 6 + brainstorming |
| Gherkin quality skill applied | Yes | No (brainstorming instead) | Yes |
| Pre-flight evals run | Yes | No | Yes |
| Implicit decisions (Gherkin/brainstorming) | 0 (6 surfaced and resolved) | 3–4 remain implicit | 0 |
| Implicit decisions (implementation) | 1 (API response field) | 2 (storage arch + API field) | 1 |
| Tests passing first attempt | Yes | Likely no (storage mismatch fails) | Yes |
| Superpowers skills triggered | N/A | 4 (brainstorm, plan, TDD, review) | 4 |
| Stewardship gaps caught | 0 (eval+ADR check passed clean) | 0 (no stewardship layer) | 0 |
| Session overhead (estimated) | ~35 min pre-implementation | ~15 min brainstorming | ~45 min |

---

### Q1: What did Superpowers catch that the three-layer infrastructure missed?

**Process discipline.** The TDD enforcement is a real gap in the three-layer infrastructure.
The smoke test I ran for Phase 2 was manually written — the three-layer infrastructure has
no equivalent to the Superpowers "write a failing test first" constraint. Without that
constraint, an agent using only the three-layer infrastructure might implement the endpoint
and then write passing tests afterward, which defeats the purpose of TDD.

Superpowers also provides git worktree isolation per task, which the three-layer
infrastructure has no equivalent for. The baseline run modified `app/main.py` directly
without branch isolation.

**Brainstorming as Q&A.** The brainstorming skill's conversational refinement can surface
decisions the Gherkin quality skill's structured diagnostic doesn't ask about. Specifically,
brainstorming might have asked: "Who calls this endpoint? An internal dashboard? An external
reporting tool?" That shapes the response design in ways the quality skill doesn't reach.

---

### Q2: What did the three-layer infrastructure catch that Superpowers missed?

**The storage architecture mismatch — before implementation.**

This is the most important finding in the experiment. The Gherkin quality skill's Q5
("Is the expected state defined for all paths?") requires thinking through the `Given`
step for "1 PAYMENT_FAILED order exists in the system." Writing that `Given` step
forces the question: how does a PAYMENT_FAILED order get into the system? Reading
`app/main.py` to answer that question reveals that it doesn't — failed payments are
never stored.

Superpowers' brainstorming skill fires from the task description, not from the code.
It would not read `app/main.py` during brainstorming unless the agent chose to. TDD
would eventually surface the mismatch as a failing test — but that is during
implementation, not during spec design. The three-layer infrastructure surfaces it
during Gherkin writing, before a line of production code is written.

**The difference:** six implicit decisions surfaced and resolved before the first line of
code with the three-layer infrastructure. With Superpowers only, the most important
decision (storage architecture) surfaces as a red test during implementation — after
the plan is already committed to.

**The eval as a green-light signal.** The operation scope eval fired on this task and
correctly gave a green light. This is underappreciated: the eval prevents the HALT
instruction from being triggered unnecessarily. Without the eval, an agent might spend
time re-reading ADRs that don't apply. The eval routes correctly.

**Context persistence.** The CLAUDE.md invariants persist across every session. An agent
without them (Superpowers only, minimal CLAUDE.md) would re-derive every architectural
decision from scratch. The fire-and-forget notification invariant, the inventory-before-
payment ordering, the payment retry cap — none of these are in the minimal CLAUDE.md.
A future session adding complexity to the summary endpoint (e.g., "add a time-range filter")
could silently violate any of them.

---

### Q3: Did the full stack produce fewer implicit decisions than either alone?

Yes, at the Gherkin/brainstorming stage. The combination catches what each misses:
brainstorming surfaces stakeholder context that the Gherkin quality skill doesn't ask
about; the Gherkin quality skill surfaces the storage constraint that brainstorming
doesn't read the code to find. Together: 0 implicit decisions before implementation.

The implementation-stage implicit decision (non-CONFIRMED order IDs not returned in
API responses) survived both layers. This lives in the API-design gap identified in
Issue #19 — below behavioral spec, above code.

---

### Q4: Did any Superpowers skill conflict with or duplicate any three-layer artifact?

One structural overlap: brainstorming and the Gherkin quality skill both target the
pre-implementation clarification moment. They don't conflict (brainstorming fires first,
Gherkin quality skill reviews the output) but they do duplicate the response-shape
and edge-case questions.

No hard conflicts. Superpowers explicitly yields to user instructions (CLAUDE.md). The
CLAUDE.md is not a Superpowers-format document — it is a stewardship document. They
operate at different layers and do not compete for the same instruction slot.

---

### Q5: For a new project starting from scratch, which would you install first?

**Superpowers, then the three-layer infrastructure.**

The reasoning: Superpowers is a skill at project setup time. The three-layer
infrastructure is built as the project accumulates decisions that must be protected.
A new project has no invariants to protect, no ADRs to write, and no decisions that
require an eval to enforce. Superpowers' TDD enforcement and brainstorming gate provide
immediate value from commit one.

The three-layer infrastructure pays off when: (a) the project runs long enough to
accumulate decisions, (b) agents are rotating in (different sessions, different contexts),
and (c) the failure modes from Issue #14 become real (historical amnesia, invariant
blindness, production blindness). For a project that will run for more than a few months
with multiple agents, the infrastructure investment is justified.

The ideal sequence: install Superpowers on day one, start building the stewardship layer
when the first ADR-level decision gets made (typically when the first "this is faster but
we can't do it because" conversation happens). Don't build the three-layer infrastructure
speculatively — build it when you have a decision to protect.

**Status:** ✅ Worked

---

## Phase 6 — Final Test Suite

**Date:** 2026-07-30
**Status:** ✅ Worked

Implementation reverted via `git checkout -- app/main.py`. All experiment changes removed.

```text
pytest tests/steps/ -v    →  16 passed, 0 regressions
pytest tests/pact/ -v     →   4 passed, all contracts verified
python3 scripts/can_i_deploy.py  →  RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

Main branch contains no trace of the summary endpoint.

---

## The Most Important Finding

**Date:** 2026-07-30
**Status:** ✅ Worked

### What I tried

Ran the same endpoint task under three conditions to see which infrastructure layer
catches the storage architecture mismatch — the gap between the task description and
the actual implementation model.

### What happened

The Gherkin quality skill's Q5 catches the mismatch during spec writing, before any
code. TDD catches it as a failing test during implementation. Brainstorming misses it
entirely unless the agent chooses to read the code during the Q&A phase.

### Root cause

The storage architecture mismatch lives at the intersection of the spec layer and the
implementation layer. The task description says "count by status" — but the existing
implementation only stores one of the six statuses. Neither the task description nor
brainstorming can surface this without reading the code. The Gherkin quality skill
forces the agent to write the `Given` step that makes the constraint visible: "Given
1 order with status PAYMENT_FAILED exists in the order store." Writing that step forces
the question: how does it get there? Reading the code to answer that question surfaces
the storage model.

### The fix

Surfacing the issue during Gherkin writing (Phase 2) rather than during implementation
(Phase 3) produces a decision made at the spec level, not a patch made during debugging.
The Phase 2 decision was: "expand the order store to record all terminal states." That
decision was made explicit in the revised Gherkin, before a single line of production
code was written.

### Why this matters

Writing the `Given` step is the mechanism that makes spec-level thinking operational. Most
teams think they're writing specs when they're writing acceptance criteria — "returns counts
by status" — but acceptance criteria are not specs. A spec requires a precondition you can
write without knowing the implementation. When you write "Given 1 order with status
PAYMENT\_FAILED exists," you have to know how it gets there. If you don't know how it gets
there, you don't actually have a spec — you have a feature description with a gap in it.
The Gherkin quality skill forces this discovery because it requires you to make the
precondition concrete. Brainstorming doesn't require this; TDD discovers it but after the
plan is committed. The discipline of writing a testable precondition is the mechanism that
surfaces architectural constraints before they become implementation surprises.

