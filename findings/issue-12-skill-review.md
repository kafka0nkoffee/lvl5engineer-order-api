# Issue #12 — Skill Review: Reading the Skill Before Running It

> Written in real time during the session.

---

## Phase 1 — Skill Review Framework

**Date:** 2026-06-16
**Status:** ✅ Complete

This session builds the review process that should have preceded the v2.0 Gherkin quality
skill. The framework lives in two documents created at the start of the session:

- `docs/skill-review-checklist.md` — five-dimension checklist for reviewing any skill artifact
- `docs/skill-pr-template.md` — PR template for version-controlled skill repositories

The checklist covers five dimensions: routing signal, output contract, methodology,
idempotency and stability, and failure modes. Each dimension contains numbered questions the
reviewer must answer explicitly before approving a version bump. A reviewer who reads a skill
and asks "does this look reasonable?" is not doing a skill review. A reviewer who works
through this checklist is.

The framework was then applied retrospectively to both v1.1 and v2.0 — in the order they
should have been reviewed, not the order they were built.

---

## Review: gherkin-scenario-quality v1.1

**Date:** 2026-06-16
**Status:** ✅ Complete — CHANGES REQUESTED

Target: `docs/skills/tier2/gherkin-scenario-quality.md`

### Dimension 1: Routing signal review

**1.1 Is the description on a single line and under 120 characters?**

Description text:

```text
Evaluate and produce well-formed Gherkin scenarios for the order-api
project using the five-question debt diagnostic and output contract.
```

Character count: 137. **FAIL — exceeds 120-character limit by 17 characters.**

The description is a single line, satisfying the first condition. At 137 characters it
exceeds the 120-character threshold above which many agent routing frameworks truncate or
deprioritize the signal. The excess 17 characters carry "and output contract" — meaningful
to the skill author but invisible to an agent routing on a 120-character budget.

**1.2 Does the description name the artifact type the skill produces?**

Yes. "well-formed Gherkin scenarios" names the artifact type explicitly. An agent routing
for "write Gherkin" would match.

**1.3 Does the description name the domain or project scope?**

Yes. "for the order-api project" scopes the skill. An agent working in a different project
context should not route here.

**1.4 Does the description name the methodology used?**

Yes. "five-question debt diagnostic" names the methodology and distinguishes this skill from
a generic Gherkin-writing skill. However, "and output contract" in the description names the
output format, not the methodology. The output contract is not a methodology — naming it here
may confuse a routing agent that distinguishes on methodology terms.

**1.5 Routing test — three SHOULD and three SHOULD NOT**

Prompts that SHOULD route to this skill:

1. "Write a Gherkin scenario for the POST /orders timeout case"
2. "Review order_creation.feature for spec debt before the next implementation session"
3. "I'm about to implement order cancellation — give me the Gherkin first"

Prompts that SHOULD NOT route to this skill:

1. "Write pytest step definitions for the payment gateway mock" — should not route;
   description says "Gherkin scenarios," not Python.
2. "Review app/main.py for implementation correctness" — should not route; description
   says Gherkin, not code.
3. "Write acceptance tests for the user profile service" — **MISROUTE FOUND.** An agent
   working on a different service using Gherkin acceptance tests could route here based on
   "produce well-formed Gherkin scenarios." The "order-api project" guard depends on the
   routing agent understanding it as a scoping constraint, not as context. This is not
   guaranteed across agent frameworks.

---

### Dimension 2: Output contract review

**2.1 Is the output contract explicit and enumerable?**

Six of the seven presence requirements are enumerable yes/no checks:

- "All Then clauses must assert a field name AND a value" — enumerable: check each Then
- "All counts must use 'exactly N' or 'no more than N total'" — enumerable: check each count
- "All time bounds must include a start anchor" — enumerable: check each time bound
- "All Given clauses referencing external services must name the service explicitly" —
  enumerable: check each Given that references an external dependency

One requirement is not enumerable: "Each scenario title must explicitly name the decision
point." Whether a title "explicitly names the decision point" requires judgment. "Successful
order creation" vs. "Order is confirmed when payment succeeds and stock is available" — both
could be argued to name the decision point. No guidance is given on what "explicit" means.

**2.2 Could two agents produce different outputs that both satisfy the contract?**

Yes, in three ways:

1. The contract requires Then clauses to assert field+value but does not specify WHICH fields
   must be present. Two agents could assert different field sets and both pass.
2. The contract does not enumerate HTTP status codes per outcome type. An agent could produce
   200 or 204 for successful cancellation; both satisfy "the HTTP status code is specified."
3. The contract does not specify which external services must appear per scenario type.
   An agent asserting payment gateway behavior but omitting inventory service assertions
   would satisfy "All Given clauses referencing external services must name the service
   explicitly" — if no Given clause mentions inventory, condition 3 is vacuously satisfied.

Under-specified requirements: (a) scenario title "explicit" criterion, (b) required fields
per scenario type, (c) required HTTP status codes per outcome, (d) required external services
per scenario type.

**2.3 Does the contract specify what the skill must NOT produce?**

Yes. The "What the output must NOT contain" section lists four absence requirements: no prose
explanation, no inline logic comments, no Scenario Outline unless required, no implementation
details. These are well-defined and checkable.

Missing absence requirement: The contract does not say what to return when the skill CANNOT
satisfy the contract (ambiguous input). The "edge cases" section handles this, but a caller
reading only the contract section does not know that a refusal message is a valid output.

**2.4 Is there a downstream consumer identified?**

Partially. "Ready to paste into a `.feature` file" identifies the immediate destination but
not what happens next. The feature file is consumed by pytest-bdd step definitions, which are
consumed by the test runner. If the downstream consumer had been identified explicitly, the
output contract would have included: "Each Then clause must be implementable as a single
pytest-bdd step matcher." This would have caught Q2 ambiguity earlier — an ambiguous step is
not just spec debt, it is a step definition that cannot be written deterministically.

**2.5 Is the output contract testable without running the skill?**

Yes for six of the seven presence requirements and all four absence requirements. The
exception is the scenario title requirement — "explicitly names the decision point" requires
judgment and cannot be verified mechanically without a precise definition of "explicit."

---

### Dimension 3: Methodology review

**3.1 Does the methodology describe reasoning, not procedure?**

Mixed. Q1 and Q3 describe reasoning: "Can you name the single service this scenario belongs
to? Every step in the scenario should describe behavior of that one service." This gives the
agent WHY to check ownership, not just a rule to apply.

Q2 is procedural: it lists patterns that "must be rewritten" without explaining WHY each
pattern creates spec debt. An agent encountering a new underspecified pattern not on the list
has no principle to apply — only the list.

Q4 is reasoning-adjacent: it explains the caller-vs-implementation distinction, giving an
agent a principle that extends beyond the listed substitutions. Better than Q2.

Q5 is a checklist: "For every success scenario, check: [list]." This is pure procedure. An
agent encountering a scenario type not covered by "success," "failure," or "decision point"
has no reasoning to apply.

**3.2 Does the methodology generalize to edge cases?**

Three edge cases not covered by the methodology examples:

*Edge case A: A scenario with no Given clause*

```gherkin
Scenario: Payment timeout results in pending status
  When the payment gateway times out
  Then the response HTTP status is 202
  And the response body contains a "status" field with value "PAYMENT_PENDING"
```

Q1: ownership → order_creation.feature. OK.
Q2: "times out" — not on the UNDERSPECIFIED list but is underspecified (no timeout duration,
    no anchor). The methodology lists "within N seconds" but not "times out" with no duration.
    A methodical agent would miss this as a Q2 violation.
Q3: No precondition state is established — what is the initial order state? Q3 checks if
    terms are defined, but does not check whether the PRECONDITION STATE is defined. Gap.
Q4: No implementation leaks.
Q5: Missing inventory status side effect, retry count assertion.

Result: Q5 catches the missing side effects. Q3 does NOT catch the missing Given clause.
This is a genuine methodology gap.

*Edge case B: A scenario asserting absence (negative assertion)*

```gherkin
Scenario: Payment gateway is not called when stock is unavailable
  Given the inventory service reports SHOE-RED-42 as out of stock
  When the user submits an order for SHOE-RED-42
  Then the payment gateway receives no requests
  And the response HTTP status is 409
```

Q5: "Does the scenario assert that side effects did NOT occur?" — Yes, this is exactly
    what Q5 asks for failure scenarios. Correctly handled.

Result: Methodology handles negative assertions via Q5. No gap.

*Edge case C: A scenario with two When clauses (multi-step action)*

```gherkin
Scenario: Retry succeeds on second attempt
  Given the payment gateway fails on the first request
  And the payment gateway succeeds on the second request
  When the order is submitted
  And the system retries the payment
  Then the order status is "CONFIRMED"
```

Q3: "the system" is not defined — violates Q3 ("every noun that is not an HTTP primitive
    or language primitive must be defined"). Q3 catches this.
Q5: Missing HTTP status code, inventory side effects.

Result: Q3 catches the undefined term; Q5 catches the missing assertions. Methodology
handles this case correctly.

Summary: The methodology has one genuine gap (Edge case A: missing Given clause not
caught by Q3). The gap does not appear in the listed failure modes.

**3.3 Is there domain knowledge in the methodology that requires documentation?**

Yes, two items:

1. The Q4 field name substitutions (`db_status → status`, `order_created_at → placed_at`)
   are this project's specific leaky abstractions. They are documented, correctly. But their
   origin (the spec audit in Issue #8) is not referenced. An agent reading v1.1 without prior
   context cannot know whether the list is definitive or partial. New leaky abstractions added
   to the implementation would not automatically appear in Q4.

2. The four feature files in Q1 are domain knowledge. The methodology says "If a new endpoint
   has no feature file, create one" but gives no naming convention. Two agents creating a
   cancellation feature file could produce `orders_cancel.feature` and
   `order_cancellation.feature` — both satisfy Q1 without violating the methodology.

**3.4 Does the methodology handle the failure cases in "Edge cases and failure modes"?**

For each listed case:

- `order_status_bad.feature` — handled: named explicitly, do not fix it
- Step definitions — handled: "this skill's scope ends at the .feature file"
- Ambiguous product requirement — handled: explicit refusal format provided
- Non-order-api projects — handled: "do not apply Q4 substitutions"
- Multiple decision paths — handled: "do not return a single scenario"

Missing: No handling for UI scenarios (Selenium/Playwright/Cucumber UI-layer Gherkin). An
agent given a UI scenario applies Q1–Q5 and produces what looks like an API scenario. The
output passes the quality checks but describes the wrong interface layer. This is the
PLAUSIBLE WRONG failure mode that the Issue #11 stress tests later found.

---

### Dimension 4: Idempotency and stability review

**4.1 Three framings, structurally identical output?**

Testing conceptually: input is "Write a Gherkin scenario for cancelling an order when the
payment has not yet been captured."

Framing 1: Direct instruction.
Framing 2: User story form ("As an admin, I want to cancel an unconfirmed order...").
Framing 3: Audit form ("What scenarios are missing for order cancellation?").

v1.1 has no idempotency guard. All three framings go through Q1–Q5 and produce a scenario.
Structural elements that could vary across framings:

- The scenario title (agent might phrase differently for framing 3 vs. framing 1)
- The concrete order_id value (no constraint; "order-123" vs. "order-cancel-001")
- The HTTP status code for cancellation (200 vs. 204 — not specified by the methodology)
- Whether `# Assumption:` comments are added for decisions already in the input

**4.2 Apply to an already-correct input**

v1.1 has no Guard 4. Given an already-correct scenario (all Then clauses have field+value,
concrete IDs, named services, HTTP status), the skill would run Q1–Q5, find no violations,
and then produce output. The output contract says "produce one or more complete Gherkin
scenarios" — implying a scenario is always produced. The skill has no "return unchanged"
path. It would produce a rewrite, possibly with different phrasing, different concrete IDs,
or added assumption comments for decisions already made in the input.

**4.3 Self-referential test**

Confirmed by Issue #11 stress testing: v1.1 applied to its own prior output produces a third
version. The skill does not recognize its own output as already-correct; it rewrites. This is
the UNSTABLE idempotency behavior that the Issue #11 stress test found and that v2.0's
Guard 4 was built to prevent.

**4.4 Idempotency verdict: UNSTABLE**

v1.1 has no mechanism to detect already-correct input. It will rewrite any scenario it
receives, including its own output. Structural elements (IDs, phrasing, assumption comment
placement) vary across repeated applications.

---

### Dimension 5: Failure mode review

**5.1 Out-of-scope input — domain test**

Test input:

```gherkin
Scenario: User sees confirmation on order submit
  Given the user is on the order form
  When the user clicks Submit
  Then the page shows "Order confirmed"
```

v1.1 behavior: The skill applies Q1–Q5. Q1 cannot name a service. Q3 finds "the order form"
undefined. Q5 finds no HTTP status code. The skill would attempt to translate this into an
API scenario. The output looks well-formed but describes the wrong interface layer.

Classification: **PLAUSIBLE WRONG** — output looks correct but contains an error invisible
to the quality criteria (wrong interface layer, UI behavior translated to API behavior).

**5.2 Contradictory input**

Test input:

```gherkin
Scenario: Payment gateway retry behavior
  Given the payment gateway fails on the first attempt
  When the order is submitted
  Then the system retries the payment exactly 2 times
  And the system retries the payment no more than 1 time total
```

v1.1 behavior: Q2 would catch "exactly 2 times" (missing "total"). Q2 would also note the
limit in "no more than 1 time total." But the LOGICAL CONTRADICTION between "exactly 2" and
"no more than 1" is not addressed anywhere. v1.1 would likely document both as `# Assumption:`
comments and proceed — producing a scenario that can never pass.

Classification: **PLAUSIBLE WRONG** — output looks well-formed but has logically
incompatible constraints. Tests from this scenario can never be green.

**5.3 Empty input**

v1.1 edge cases say "Do not use this skill when the product requirement is itself ambiguous"
and provide an explicit refusal format. An empty input would likely trigger this path.

Classification: **CORRECT REFUSAL (implicit)** — the handling is inferential, not stated.
A scenario with a title but no steps would not clearly trigger the ambiguity path.

**5.4 Failure mode classification summary**

| Failure mode | v1.1 output | Classification |
|---|---|---|
| UI scenario | Translates to API scenario | PLAUSIBLE WRONG |
| Contradictory constraints | Documents both as assumptions, proceeds | PLAUSIBLE WRONG |
| Empty input | Likely refuses via ambiguity path | CORRECT REFUSAL (implicit) |
| Multiple decision paths | Returns multiple scenarios | CORRECT (explicit) |
| Ambiguous requirement | Returns explicit refusal | CORRECT REFUSAL (explicit) |

**5.5 Are all PLAUSIBLE WRONG outcomes eliminated?**

No. Two remain:

1. UI scenarios → translated silently to API scenarios
2. Contradictory constraints → documented as assumptions, scenario produced anyway

These are exactly the two behavioral failures that the Issue #11 stress tests found and that
v2.0's Guards 2 and 3 address. A pre-v2.0 review using this checklist would have required
explicit termination for both cases, identified the fix, and potentially prevented the stress
test failures from being required at all.

---

### v1.1 Review Verdict: CHANGES REQUESTED

**Issues that would have prevented the specific v2.0 failures:**

1. **Dimension 5.1 — UI scenario produces PLAUSIBLE WRONG output.** The review would have
   required explicit domain termination, leading directly to what became Guard 2.

2. **Dimension 5.2 — Contradictory constraints produce PLAUSIBLE WRONG output.** The review
   would have required explicit contradiction halting, leading directly to what became Guard 3.

3. **Dimension 4.4 — UNSTABLE idempotency verdict.** The review would have flagged the
   absence of an idempotency mechanism, leading directly to what became Guard 4.

**Issues the review catches that the stress tests did NOT find:**

1. **Dimension 1.1 — Routing signal is 137 characters (limit: 120).** The stress tests
   tested the skill's behavior when invoked. They never tested whether the routing signal
   would correctly select this skill in the first place. This finding is structurally
   unreachable by behavioral stress tests.

2. **Dimension 2.2 — Under-specified output contract allows agent divergence.** The contract
   permits two agents to produce different HTTP status codes, field sets, and side-effect
   assertions while both satisfying it. Stress tests verify one agent's output against one
   expected scenario; they cannot reveal the latitude available to a second agent.

3. **Dimension 3.2, Edge case A — Missing Given clause not caught by Q1–Q5.** The Q3 check
   asks whether terms are defined, but does not check whether a precondition state is
   established. Well-formed stress test inputs would not exercise this gap.

---

## Review: gherkin-scenario-quality v2.0

**Date:** 2026-06-16
**Status:** ✅ Complete — APPROVED WITH COMMENTS

Target: `docs/skills/tier2/gherkin-scenario-quality-v2.md`

### Dimension 1: Routing signal review

**1.1 Is the description on a single line and under 120 characters?**

Description text:

```text
Evaluate and produce well-formed Gherkin scenarios for the order-api
project using the five-question debt diagnostic, four pre-flight
guards, and a minimal-change output contract.
```

Character count: 179. **FAIL — exceeds 120-character limit by 59 characters.**

v2.0 made this worse. The addition of ", four pre-flight guards, and a minimal-change" adds
42 characters to an already over-limit description. The routing signal now describes internal
implementation mechanisms ("four pre-flight guards") that are irrelevant to a caller routing
to this skill. The character count increased by 42 from v1.1's already-failing signal.

**1.2 Does the description name the artifact type?**

Yes. "well-formed Gherkin scenarios" is preserved from v1.1.

However, a new gap exists in v2.0: the description says the skill "Evaluate and produce
well-formed Gherkin scenarios," establishing Gherkin scenarios as the artifact type. But v2.0
Guards 1, 2, and 3 can each return outputs that contain NO Gherkin — only comment-only blocks
(`# SKILL FAILURE:`, `# SKILL WARNING:`). The artifact type in the description does not match
the full output space.

**1.3 Does the description name the domain or project scope?**

Yes. "for the order-api project" is preserved from v1.1.

**1.4 Does the description name the methodology?**

Yes, but over-specifies it. "five-question debt diagnostic, four pre-flight guards, and a
minimal-change output contract" describes three methodology components. Naming the pre-flight
guards in the description is an internal implementation detail that does not help routing
accuracy. It lengthens the signal without distinguishing this skill from a caller's
perspective.

**1.5 Routing test — three SHOULD and three SHOULD NOT**

The same three SHOULD prompts from v1.1 apply. The same misroute risk for non-order-api
Gherkin projects applies. The longer description increases truncation risk in frameworks with
strict character limits without improving routing discrimination.

Additional routing concern: the description's "evaluate and produce" implies two modes —
evaluation only, and production (rewrite). An agent routing for "just tell me what's wrong,
don't rewrite" would match the description. But v2.0 may rewrite (if the scenario violates
the contract) even for evaluation-only intent. The description does not distinguish modes.

---

### Dimension 2: Output contract review

**2.1 Is the output contract explicit and enumerable?**

v2.0 adds the minimal change principle: "Produce the minimum changes necessary to satisfy
the output contract." This is a judgment call, not an enumerable check. Two agents applying
the same principle to the same input can produce different change sets — each believing
theirs is minimum.

The Guard 4 idempotency check is enumerable (five yes/no conditions). This is a significant
improvement. But the "minimal fix applied" annotation format requires the agent to count debt
items — and two agents may count differently if a single step has multiple violations
(no field name AND no value in one Then clause: one item or two?).

**2.2 Could two agents produce different outputs that both satisfy the contract?**

Yes. The same under-specified areas from v1.1 remain (scenario title "explicit" criterion,
required fields per scenario type, required status codes per outcome type, required external
services per scenario type). Additionally, "minimum changes necessary" permits two agents to
produce different change sets, each satisfying the contract.

The annotation format is also ambiguous: the "SKILL: Minimal fix applied — [N] debt item(s)
corrected" leaves N agent-determined.

**2.3 Does the contract specify what the skill must NOT produce?**

Yes — same as v1.1 plus "changes to steps that already satisfy the output contract."

Missing absence requirement: The output contract section does not document guard outputs as
valid return values. A caller reading the contract section expects Gherkin scenarios as
output. v2.0 can also return `# SKILL FAILURE:` blocks, `# SKILL WARNING:` blocks, and
`# SKILL: No changes required` blocks. None of these appear in the output contract section.
This creates a downstream handling gap: a caller that reads the contract, implements a
handler for Gherkin output, and receives a guard failure block has no specification for
how to handle that response.

**2.4 Is there a downstream consumer identified?**

The same gap as v1.1 with an additional wrinkle: v2.0 has TWO downstream consumers, not
one, and neither is identified:

1. Feature file (for normal output — the Gherkin scenario that gets pasted)
2. Human reviewer or orchestrating agent (for guard outputs — the failure/refusal signal
   that requires human action, not pasting)

An automated pipeline that takes all skill output and writes it to a feature file would write
`# SKILL FAILURE:` blocks into the feature file as Gherkin comments. The test runner would
ignore them (Gherkin comments are valid syntax), but the feature file accumulates
skill-internal metadata silently. The caller never knows a guard fired.

**2.5 Is the output contract testable without running the skill?**

The Guard 4 trigger conditions (five yes/no checks) are testable without running the skill.
"Minimum changes necessary" remains a judgment call and is not mechanically testable.

---

### Dimension 3: Methodology review

**3.1 Does the methodology describe reasoning, not procedure?**

v2.0 adds four guards, which are procedural by design. Unconditional halting is correct for
guards — making them procedural is intentional and right.

However, Guards 1, 2, and 3 lack the inline reasoning that Guard 4 has. Guard 4 explains
WHY halting is correct ("A skill that always rewrites is dangerous at agent scale..."). Guards
1, 2, and 3 state conditions but do not explain why halting is the correct response (vs.
scaffolding an empty scenario, translating the UI step, or documenting the contradiction as
an assumption and proceeding).

Guard 2 lists UI patterns without explaining WHY these patterns indicate out-of-scope input.
The word "button" triggers Guard 2 as a UI element. But "field" in "the response body
contains a 'status' field" does NOT trigger Guard 2 (and correctly so). An agent that
encounters a new pattern not on the list ("the modal appears", "the toast notification shows")
has no reasoning to apply — only the list.

**3.2 Does the methodology generalize to edge cases?**

Three edge cases not covered by the v2.0 methodology examples:

*Edge case A: Mixed UI/API scenario (one UI step, three API steps)*

```gherkin
Scenario: Order placed via the submit button
  Given the user clicks the Submit button
  When POST /orders is called with the order payload
  Then the response HTTP status is 201
  And the response body contains an "order_id" field with value "order-123"
```

Guard 2 condition: "contains any of the following patterns indicating UI behavior." The step
"the user clicks the Submit button" matches "clicks." Guard 2 TRIGGERS. The skill halts
entirely and returns a domain failure signal.

The three API steps are well-formed. An alternative correct behavior would be: flag the UI
step and apply the five-question diagnostic to the API-layer steps. Guard 2's "halt entirely"
response may be too aggressive for mixed scenarios.

Classification: **PLAUSIBLE WRONG in the refusal direction** — the skill rejects a scenario
that contains both UI and API steps, when partial assistance is possible.

*Edge case B: Guard 4 with inventory service assertions absent*

```gherkin
Scenario: Order is confirmed when payment succeeds
  Given the payment gateway will accept the charge
  When the user submits an order for SHOE-RED-42
  Then the response HTTP status is 201
  And the response body contains an "order_id" field with value "order-123"
  And the response body contains a "status" field with value "CONFIRMED"
```

Guard 4 conditions applied:
1. All Then clauses assert field+value: 201 (HTTP status value), order_id+value, status+value
   — YES
2. All counts use exact or total form: no counts present — N/A, passes
3. All external services named explicitly: "payment gateway" in Given — YES
4. No UNDERSPECIFIED patterns from Q2: none present — YES
5. HTTP status code in Then clause: "the response HTTP status is 201" — YES

Guard 4 TRIGGERS. The skill returns input unchanged: "# SKILL: No changes required."

But the inventory service is never mentioned. Q5 would require an inventory service assertion
for a happy-path order creation scenario. Guard 4 runs BEFORE the diagnostic and prevents Q5
from running. The skill incorrectly signals "no changes required" for a scenario with a
missing required side-effect assertion.

Classification: **PLAUSIBLE WRONG** — Guard 4 returns a "no changes required" signal for a
scenario that has a structural omission. This is the most significant behavioral finding in
the v2.0 review.

*Edge case C: v1.1 output fed to v2.0 (cross-version input)*

A v1.1 output contains `# Assumption:` comments. Guard 4 condition 4 checks that "no step
contains the UNDERSPECIFIED patterns from Q2." The `# Assumption:` comments are comments, not
steps. Condition 4 checks steps. Guard 4 can trigger even if `# Assumption:` comments are
present, provided the steps themselves are well-formed.

Guard 4 TRIGGERS correctly. The skill returns v1.1 output unchanged. This is correct
behavior: v1.1 output with well-formed steps satisfies all five Guard 4 conditions.

**3.3 Is there domain knowledge in the methodology that requires documentation?**

Guard 2's UI pattern list is not documented as non-exhaustive. The listed patterns cover
common Selenium/Cucumber patterns ("clicks", "navigates to", "the page loads") but not all
UI test frameworks. An agent processing a scenario with `await page.locator('#submit').click()`
would not match any listed Guard 2 pattern and would bypass the domain check.

The phrase "any of the following patterns" implies the list may not be exhaustive, but the
instruction to "Identified UI patterns: [list the specific phrases that triggered this guard]"
in the Guard 2 return template implies an agent should match only listed patterns. The list
needs "including but not limited to" or the methodology needs a principle the agent can apply
to unlisted patterns.

**3.4 Does the methodology handle the failure cases in "Edge cases and failure modes"?**

v2.0's edge cases section is significantly more complete than v1.1:

- Already well-formed → Guard 4 ✅
- UI scenario → Guard 2 ✅
- Contradicting constraints → Guard 3 ✅
- Self-referential input → Guard 4 ✅
- Ambiguous product requirement → explicit refusal ✅
- Multiple decision paths → one scenario per path ✅
- `order_status_bad.feature` → explicit early return ✅

Gap: The mixed UI/API scenario (Edge case A above) is not listed in "Edge cases and failure
modes." The Guard 2 halt for this case is undocumented and potentially wrong. A v2.1 should
document this case and decide whether to halt entirely or flag only the UI steps.

---

### Dimension 4: Idempotency and stability review

**4.1 Three framings, structurally identical output?**

For inputs that trigger Guard 4 (already-correct scenarios): all three framings trigger
Guard 4 and return the input unchanged. STABLE.

For inputs that require fixes: the minimal change principle means the change set is
determined by the contract violations in the scenario, not the framing. STABLE for the
changes themselves. Annotation phrasing ("N debt item(s) corrected") depends on how the
agent counts items — could vary slightly.

**4.2 Apply to an already-correct input**

Guard 4 catches this. Returns input unchanged with `# SKILL: No changes required`
annotation.

However, the Guard 4 return specification has an internal ambiguity. The "Return:" block
shows:

```text
# SKILL: No changes required — scenario satisfies output contract.
# Five-question diagnostic result: [list any minor observations, but do not rewrite]
```

The text also says: "If Guard 4 triggers, return the input scenario unchanged." These two
instructions are in tension. Is the return value:
(a) only the two-line comment block (as the "Return:" block implies),
(b) the comment block followed by the scenario, or
(c) the scenario with the comment prepended?

The minimal-fix annotation format (described later in the skill) says "add a single comment
at the top of the scenario" — implying format (c). But Guard 4's "Return:" block shows only
the comment. This is the ambiguity documented in Phase 4.

**4.3 Self-referential test**

Guard 4 prevents self-referential rewrites. If the skill's own prior output satisfies all
five Guard 4 conditions, feeding that output back returns it unchanged with the annotation.
STABLE for self-referential inputs.

Guard 4 is designed specifically for this case: the "Self-reference guard" paragraph
explicitly documents this behavior and names it a routing signal failure if Guard 4 does not
trigger. This is the correct design.

**4.4 Idempotency verdict: CONDITIONALLY STABLE**

- STABLE for already-correct inputs (Guard 4 triggers; returns unchanged)
- STABLE for self-referential inputs (Guard 4 triggers)
- STABLE for inputs requiring fixes (minimal change principle produces consistent fix set)
- UNSTABLE for Guard 4 output format (annotation-only vs. annotation+scenario ambiguity)
- PLAUSIBLE WRONG for scenarios missing Q5 side-effect assertions (Edge case B) — Guard 4
  triggers incorrectly, calling them "no changes required"

---

### Dimension 5: Failure mode review

**5.1 Out-of-scope input — domain test**

The same UI scenario used for v1.1:

```gherkin
Scenario: User sees confirmation on order submit
  Given the user is on the order form
  When the user clicks Submit
  Then the page shows "Order confirmed"
```

v2.0 behavior: Guard 2 triggers (matches "clicks" and "the page shows"). Returns:

```text
# SKILL FAILURE: This scenario describes UI behaviour, not an HTTP API contract.
# This skill applies to API-level specifications only.
# Identified UI patterns: "clicks", "the page shows"
```

Classification: **CORRECT REFUSAL** — explicit failure, no Gherkin produced, actionable
error message naming the specific patterns that triggered the guard.

**5.2 Contradictory input**

Same contradictory scenario used for v1.1:

v2.0 behavior: Guard 3 triggers. Returns:

```text
# SKILL WARNING: Contradicting constraints detected.
# Constraint 1: "retries the payment exactly 2 times"
# Constraint 2: "retries the payment no more than 1 time total"
# These constraints are logically incompatible for the same action.
```

Classification: **CORRECT REFUSAL** — explicit halt with both constraints quoted verbatim.

**5.3 Empty input**

v2.0 behavior: Guard 1 triggers. Returns:

```text
# SKILL FAILURE: Empty scenario — no steps provided.
# A Gherkin scenario requires at minimum one Given, one When, and one Then.
```

Classification: **CORRECT REFUSAL** — explicit failure with actionable guidance.

**5.4 Failure mode classification summary**

| Failure mode | v2.0 output | Classification |
|---|---|---|
| Empty input | Guard 1 explicit failure | CORRECT REFUSAL |
| UI scenario | Guard 2 explicit failure | CORRECT REFUSAL |
| Contradictory constraints | Guard 3 explicit halt | CORRECT REFUSAL |
| Already-correct input | Guard 4 returns unchanged | CORRECT PASS |
| Mixed UI/API scenario | Guard 2 halts entirely | CORRECT REFUSAL (over-broad) |
| Missing Q5 assertions | Guard 4 triggers — "no changes required" | PLAUSIBLE WRONG |
| Self-referential input | Guard 4 returns unchanged | CORRECT PASS |
| Ambiguous requirement | Explicit refusal | CORRECT REFUSAL |

**5.5 Are all PLAUSIBLE WRONG outcomes eliminated?**

The three v1.1 PLAUSIBLE WRONG outcomes are eliminated by the guards (UI translation,
contradiction-as-assumption, and UNSTABLE self-referential rewrite).

Two new issues are introduced:

1. **Guard 2 over-broad rejection** (Edge case A): mixed UI/API scenarios are halted when
   partial assistance is possible. This is a CORRECT REFUSAL by specification but may be
   wrong behavior.

2. **Guard 4 gap** (Edge case B): scenarios that pass all five Guard 4 format conditions
   but are missing Q5 side-effect assertions are returned as "no changes required." This is
   **PLAUSIBLE WRONG** — the skill signals completion for an incomplete scenario.

---

### v2.0 Review Verdict: APPROVED WITH COMMENTS

**Are all four v1.1 fixes correctly implemented?**

1. Guard 4 (idempotency) — Yes, with documented ambiguity in return value format.
2. Guard 2 (domain check) — Yes, with one over-broad edge case (mixed UI/API scenarios).
3. Guard 3 (contradiction halt) — Yes, correctly implemented.
4. Guard 4 self-reference — Yes, covered by the same Guard 4 mechanism and explicitly
   documented in the "Self-reference guard" paragraph.

**Did the fixes introduce any new failure modes?**

Yes, two:

1. Guard 2 rejects mixed UI/API scenarios entirely when partial assistance is possible.
2. Guard 4 has a gap: scenarios that pass all five format conditions but have missing Q5
   side-effect assertions are returned as "no changes required." This is PLAUSIBLE WRONG.

**Are there failure modes the stress tests missed that the review catches?**

Yes, three:

1. **Routing signal is 179 characters (limit: 120)** — not testable by behavioral stress
   tests, which test behavior when invoked, not whether the skill is invoked.
2. **Guard 4 return value format ambiguity** — stress tests check whether Guard 4 fires,
   not the exact format of its output for downstream consumers.
3. **Guard 4 gap (Edge case B)** — the stress tests in Issue #11 focused on the four
   failure modes that v2.0 was designed to fix. Edge case B (missing Q5 assertions passing
   Guard 4) was not a stress test input type.

**Issues to address in v2.1:**

- Shorten the description to under 120 characters
- Clarify Guard 4 return format (annotation + scenario structure, matching minimal-fix
  annotation pattern)
- Add Q5 side-effect assertion check to Guard 4 conditions (or document the gap as
  acceptable and explain why)
- Document mixed UI/API scenario handling in "Edge cases and failure modes"
- Add "including but not limited to" to Guard 2's UI pattern list, or add reasoning for
  unlisted patterns

**Is v2.0 ready to be the canonical version?**

Yes. The four major failure modes from v1.1 are addressed. The new issues found are not
blocking: Guard 4's gap (Edge case B) is the most significant, but it is a precision issue
(the guard passes scenarios with a specific class of omission) rather than a regression (it
does not introduce new PLAUSIBLE WRONG output for the cases the guard was designed to
address).

---

## The real review comment

**Date:** 2026-06-16
**Status:** ✅ Complete

> **PR:** `gherkin-scenario-quality-v2.md` — Agent-safe Gherkin quality skill  
> **File:** `docs/skills/tier2/gherkin-scenario-quality-v2.md`  
> **Section:** Pre-flight guards → Guard 4 (Idempotency check)  
> **Lines:** 95–112 (Return block and "return the input scenario unchanged" instruction)  

---

**Guard 4 has two return instructions that conflict, and the conflict matters at agent
scale.**

The "Return:" block at lines 104–107 shows only the annotation comment:

```text
# SKILL: No changes required — scenario satisfies output contract.
# Five-question diagnostic result: [observations, or "none"]
```

Then line 108 says: "If Guard 4 triggers, return the input scenario unchanged."

Together these read as: return the comment block, AND return the input scenario. But a skill
returns a single value. The two instructions imply three possible interpretations:
(a) the annotation only — the scenario is not in the output,
(b) the annotation prepended to the scenario (matching the minimal-fix annotation pattern at
    line 181), or
(c) the scenario with the annotation appended.

The rest of the skill uses format (b): "add a single comment at the top of the scenario."
Guard 4's "Return:" block uses format (a). The inconsistency is invisible when a human reads
the output and manually pastes the scenario into a feature file — the human would just ignore
the comment. But in an automated pipeline it is not invisible.

**Concrete impact:** A downstream agent that receives Guard 4 output and writes all skill
output to a feature file would write the `# SKILL: No changes required` annotation as a
Gherkin comment into the file. At pipeline scale across 50 feature files, that is 50
permanent skill-internal annotations committed to specs. If the agent uses interpretation (a)
and treats the "Return:" block as the complete output, the original scenario is silently
discarded — replaced by two comment lines.

**Suggested fix:** Align Guard 4's return spec with the minimal-fix annotation pattern used
elsewhere in the skill. Replace the Guard 4 "Return:" block and the "return unchanged" text
with:

```text
Return the input scenario with the following comment prepended:
  # SKILL: No changes required — scenario satisfies output contract.
  # Five-question diagnostic result: [any minor observations; "none" if Q1–Q5 find nothing]
[followed by the complete input scenario, unchanged]
```

Alternatively, if the intent is that the annotation is caller metadata and NOT part of the
Gherkin output, state this explicitly: "The guard annotation is caller metadata. Do not
include it in the feature file. Return it as a separate response block before the unchanged
scenario."

Either formulation eliminates the ambiguity. The current text requires the downstream agent
to guess.

---

**Why this is the most important finding from either review:**

The routing signal length (Dimension 1.1, both versions over 120 characters) is the
clearest finding that stress tests cannot reach — and it is documented in both reviews
because both versions fail it. But the Guard 4 return ambiguity is the finding most specific
to v2.0's stated purpose.

v2.0 was built explicitly to be safe at agent scale. The four guards exist because agent
pipelines create failure modes that human callers handle silently (a human skips a comment;
a pipeline writes it to a file). Guard 4's return value specification has the same class of
failure it was designed to prevent: a human reading the Guard 4 output knows which part is
the scenario and which part is metadata. An automated pipeline does not.

The stress tests verified that Guard 4 triggers correctly for the right inputs. What they
could not verify — because they test the skill in isolation — is whether Guard 4's output is
correctly specified for all downstream consumers. The review did. And found it isn't.

This is the practical boundary between stress testing and skill review: stress tests answer
"does the skill work when called?" Review answers "is the skill ready to be called in all
the contexts its description implies?" They are complementary, not substitutes. Running the
stress tests first and the review second, as happened in Issue #11, is the wrong order.

---

## Phase 5 — Test Suite Results

**Date:** 2026-06-16
**Status:** ✅ Complete

All review work is documentation-only and touches no implementation files.

```text
pytest tests/steps/ -v
→ 11 passed in 12.33s

pytest tests/pact/ -v
→ 4 passed in 9.50s

python3 scripts/can_i_deploy.py
→ ALL CONTRACTS VERIFIED — safe to deploy
```

15 of 15 tests passed. The pact module required installation (`pact-python 3.4.0`) — not
specific to this session's work. No implementation changes were made.

---

### Why this matters

The Guard 4 return value is unambiguous when a human reads it — the human knows which part
is the scenario and which part is metadata. The same text is ambiguous when a pipeline reads
it, because a pipeline does not have that context. v2.0 was built specifically for agent
pipelines, yet its most safety-critical guard produces output whose format is unspecified for
the consumption pattern it exists to serve. The broader principle: specifying output format
for a human reader and specifying it for an automated consumer are different tasks, and a
skill built for agent scale needs both. The failure mode without this distinction is silent:
the guard fires correctly, the pipeline writes the guard output to the feature file, the test
runner ignores the comments, all tests pass, and the skill's internal metadata is now
committed to every production spec that was already correct. The practical conclusion is to
treat guard output as a distinct output type with its own contract, separate from the Gherkin
output contract — and to verify the guard output contract against the pipeline's consumption
pattern before publishing the skill version.
