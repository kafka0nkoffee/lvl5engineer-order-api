# Skill: Gherkin Scenario Quality (v2 — Agent-Safe)

**Tier:** 2 — Domain methodology
**Version:** 2.0
**Last updated:** 2026-06-15 (Issue #11)
**Project:** lvl5engineer-order-api
**Supersedes:** `docs/skills/tier2/gherkin-scenario-quality.md` (v1.1)

> **Why v2 exists:** v1.1 was designed for human use. Stress testing in Issue #11
> found four failure modes that are safe when a human corrects them but dangerous
> at agent scale: no idempotency check, no domain check, no contradiction halt,
> and no self-reference guard. v2 adds all four, plus explicit termination conditions
> that cause the skill to fail loudly rather than produce plausible-wrong output.

---

## Description

Evaluate and produce well-formed Gherkin scenarios for the order-api project using the five-question debt diagnostic, four pre-flight guards, and a minimal-change output contract.

---

## When to use this skill

Use this skill when:
- You are about to write a new Gherkin scenario for an endpoint that has no existing feature file coverage
- You have been given a user story or endpoint description and need to produce the Gherkin before implementation begins
- You are reviewing an existing scenario in `tests/features/` and need to assess whether it is well-formed
- A step definition author has asked why a step is hard to implement — the scenario is likely the root cause
- You are auditing a feature file for spec debt before a major implementation session

Do NOT use this skill when:
- You are writing pytest step definitions in `tests/steps/` — this skill produces Gherkin, not Python
- You are reviewing implementation code for correctness — use a code review skill instead
- The task is to run or fix failing tests — go to the implementation, not the spec
- The input is `order_status_bad.feature` — this is a pedagogical artifact kept intentionally as a bad spec

---

## Pre-flight guards (run BEFORE the five-question diagnostic)

These four checks must run before any diagnostic or rewrite. If any guard triggers, halt and return the specified output. Do not proceed to the diagnostic or produce a rewrite.

### Guard 1 — Empty input

**Condition:** The input scenario contains no steps (no Given, When, or Then clauses).

**Return:**
```
# SKILL FAILURE: Empty scenario — no steps provided.
# A Gherkin scenario requires at minimum one Given, one When, and one Then.
# Provide preconditions, trigger, and expected outcome before this skill can evaluate it.
```

Do not produce steps. Do not guess at what the scenario might describe.

### Guard 2 — Domain check

**Condition:** The input scenario contains any of the following patterns indicating UI behavior rather than HTTP API behavior:
- References to browser actions: "opens the browser", "clicks", "navigates to", "sees the page", "the page loads", "the form shows", "the dashboard displays"
- References to user interface elements: "button", "dropdown", "modal", "form", "field" (as a UI element, not a response body field)
- References to visual state: "is visible", "appears", "shows", "displays" (when not describing a response body)

**Return:**
```
# SKILL FAILURE: This scenario describes UI behaviour, not an HTTP API contract.
# This skill applies to API-level specifications only (HTTP requests, response bodies, status codes).
# To spec this behavior, use a UI testing skill or write a separate UI feature file.
# Identified UI patterns: [list the specific phrases that triggered this guard]
```

Do not translate the scenario into an API equivalent. Do not guess at what API the UI behavior implies.

### Guard 3 — Contradiction detection

**Condition:** The input scenario contains logically incompatible constraints on the same action. Common patterns:
- "exactly N" and "no more than M" for the same action where N > M, or where both apply to the same call count
- "always" and "never" applied to the same condition
- A Given that establishes a state that the When clause contradicts (e.g., "Given payment has already been captured" + "When the payment gateway processes the charge")

**Return:**
```
# SKILL WARNING: Contradicting constraints detected.
# Constraint 1: [quote the first constraint verbatim]
# Constraint 2: [quote the second constraint verbatim]
# These constraints are logically incompatible for the same action. Resolve the contradiction
# in the input before this skill can produce a well-formed scenario.
# A scenario with contradicting constraints produces a test that can never pass.
```

Do not produce a rewrite. Do not document the contradiction in an `# Assumption:` comment and proceed. The skill must halt.

### Guard 4 — Idempotency check

**Condition:** The input scenario satisfies all of the following (the output contract, applied to the input):
- All Then clauses assert a field name AND a value (not just presence)
- All counts use "exactly N" or "no more than N total"
- All external services are named explicitly in Given and Then clauses
- No step contains the UNDERSPECIFIED patterns from Q2 ("correct", "valid", "reasonable", "appropriate", "it should succeed", "is released", "is notified")
- An HTTP status code is asserted in the Then clause

**Return:**
```
# SKILL: No changes required — scenario satisfies output contract.
# Five-question diagnostic result: [list any minor observations, but do not rewrite]
```

If Guard 4 triggers, return the input scenario unchanged. Do not improve it. Do not change user IDs, field names, or phrasing. Do not add `# Assumption:` comments for decisions already made in the input.

**Why this guard exists:** A skill that always rewrites is dangerous at agent scale. Rewriting a scenario that already satisfies the output contract introduces unnecessary changes that a downstream agent cannot distinguish from necessary ones. Changed user IDs become changed step definition values. Removed assumption comments drop documented decisions. The idempotency check prevents these regressions.

**Self-reference guard:** If the input scenario is itself the output of a previous run of this skill (recognizable by the presence of `# Assumption:` comments in the original form, or by all five output contract conditions being satisfied), Guard 4 will trigger and return the input unchanged. This is the correct behavior. If Guard 4 does NOT trigger when fed a previous output — if the skill rewrites its own output — that is a routing signal failure. Investigate the Guard 4 condition rather than accepting the rewrite.

---

## Five-question diagnostic

(Unchanged from v1.1. Applied only after all four pre-flight guards pass.)

Apply these five questions to every scenario you write or review. Do not skip questions. Do not answer "no issues" without working through each one explicitly.

**Q1: Who owns this scenario?**
Can you name the single service this scenario belongs to? Every step in the scenario should describe behavior of that one service.

The order-api project has four feature files. Assign each scenario to exactly one:
- `order_creation.feature` — behavior of POST /orders
- `order_status_good.feature` — behavior of GET /orders/{id}/status (correct spec)
- `order_status_bad.feature` — pedagogical artifact, do not add new scenarios here
- `notification_service.feature` — behavior of the notification flow

If a new endpoint has no feature file, create one.

**Q2: What decisions does this scenario leave open?**

The following step patterns always leave decisions open and must be rewritten:
- `"correct"`, `"valid"`, `"appropriate"`, `"reasonable"` — replace with the exact value or format
- `"within N seconds"` — replace with `"within N seconds of [start anchor]"`
- `"is released"`, `"is notified"`, `"is confirmed"` — replace with the observable signal
- `"not retried more than N times"` — replace with `"receives no more than N [request type] total"`
- `"the response includes a [X]"` — replace with `"the response body contains a [field name] field with value [concrete value]"`
- `"it should succeed"`, `"it works"`, `"the operation completes"` — always UNDERSPECIFIED; replace with HTTP status + response body

**Q3: Are all terms defined within the file?**

Every noun that is not an HTTP primitive or language primitive must be defined in the scenario itself. Concrete IDs win over references. Named services win over "the external service."

**Q4: Does this scenario describe behavior or implementation?**

Specific leaks to catch in this project:
- `db_status` → use `status`
- `order_created_at` or `populated from the order record` → use `placed_at` in ISO 8601 format
- `the inventory flag is set` → use `the inventory service receives a [request type] request`
- `order_record_id` → use `order_id`
- Any reference to "the database", "the cache", "the queue", "the background thread"

**Q5: What does this scenario NOT say that it should?**

For every success scenario:
- HTTP status code in the Then clause
- Full response body shape (all required fields, names, values or formats)
- All side effects on external services asserted

For every failure scenario:
- Error response body (not just status code)
- Named error constant (not `"some error"`)
- Assertion that side effects did NOT occur

For every decision point (if/else in the implementation):
- Separate scenario for each path

---

## Output contract

### Minimal change principle (new in v2)

Produce the minimum changes necessary to satisfy the output contract. Do not rewrite steps that already comply. If a step is well-formed, copy it to the output unchanged — same wording, same ID values, same phrasing. The goal is a scenario that satisfies the contract, not a scenario that looks maximally clean.

**Annotation for minimal-change output:**
When returning a partially-fixed scenario (some steps changed, some unchanged), add a single comment at the top of the scenario:
```
# SKILL: Minimal fix applied — [N] debt item(s) corrected. [unchanged steps left as-is.]
```

### Standard output requirements

- **One or more complete Gherkin scenarios** in `Given/When/Then` format, ready to paste into a `.feature` file
- **Each scenario title** must explicitly name the decision point
- **All Then clauses** must assert a field name AND a value
- **All counts** must use `"exactly N"` or `"no more than N total"`
- **All time bounds** must include a start anchor
- **All Given clauses referencing external services** must name the service explicitly
- **Assumptions** — any decision not in the input must appear as a `# Assumption:` comment immediately below the step
- **No internal field names**

### What the output must NOT contain:
- Prose explanation of what was found
- Inline comments explaining step logic
- `Scenario Outline:` unless the input explicitly requires parametric scenarios
- References to implementation details
- Changes to steps that already satisfy the output contract (minimal change principle)

---

## Quality criteria

Before returning output, ask:

1. **Guard pass confirmation**: Did all four pre-flight guards pass without triggering? If any triggered, did you return the specified guard output and halt?

2. **Minimal change compliance**: For each step you changed, can you name the specific output contract requirement it violated? If you changed a step without being able to name the violation, revert the change.

3. **Compatibility**: Would a second agent produce scenarios with the same field names, status codes, and assertion values? If not, find the step that introduces ambiguity.

4. **Contract completeness**: Does every scenario fully specify precondition state, triggering action with parameters, response HTTP status, response body shape, and external service side effects?

5. **Decision visibility**: Every decision not in the input must appear as a `# Assumption:` comment. Decisions already in the input must NOT be re-documented as assumptions (that is an unnecessary change).

6. **Ownership**: Can you name the feature file without consulting any other document?

---

## Edge cases and failure modes (updated in v2)

**When the input is already well-formed:** Guard 4 triggers. Return input unchanged with the `# SKILL: No changes required` annotation. Do not improve it.

**When the input is a UI scenario:** Guard 2 triggers. Return the domain failure signal. Do not translate to API.

**When the input has contradicting constraints:** Guard 3 triggers. Return the contradiction warning. Do not produce a rewrite.

**When the input is the output of a previous run of this skill:** Guard 4 should trigger. If it does not — if the skill rewrites its own prior output — the Guard 4 condition has a gap. Do not accept the rewrite as correct. Investigate the guard.

**When the product requirement is itself ambiguous:** Do not invent semantics. Return: "The input is ambiguous about [specific decision]. Please specify [concrete options] before this skill can produce a well-formed scenario."

**When the input describes multiple decision paths:** Produce a scenario for each path. A single scenario for a multi-path operation is incomplete output.

**When `order_status_bad.feature` is the input:** Return immediately: "# SKILL: This is a pedagogical artifact kept as a bad-spec example. Do not apply quality criteria to it."

---

## Version history

| Version | Change | Issue |
|---------|--------|-------|
| 1.0 | Initial skill from Issues #5–#8 methodology | #9 |
| 1.1 | Added IMPLICIT FLOW to methodology; added "do not return a single scenario" failure mode | #9 |
| 2.0 | Added four pre-flight guards (empty, domain, contradiction, idempotency); added minimal change principle; added self-reference guard documentation | #11 |

---

## What changed from v1.1 to v2.0

| v1.1 behavior | v2.0 behavior |
|---------------|---------------|
| Always produces a full rewrite | Produces minimal changes; returns input unchanged when it satisfies contract (Guard 4) |
| Translates UI scenarios into API scenarios | Fails explicitly with domain check (Guard 2) |
| Documents contradictions in `# Assumption:` comments and continues | Halts before rewrite with contradiction warning (Guard 3) |
| Self-referential input produces plausible-wrong rewrite | Guard 4 triggers; returns input unchanged |
| Empty input: produced explicit failure | Empty input: still produces explicit failure (unchanged) |

---

## Reference

This skill formalizes the methodology developed across:
- `findings/issue-05-the-spec-that-doesnt-lie.md`
- `findings/issue-07-scope-problem.md`
- `findings/issue-08-spec-audit.md`
- `findings/issue-11-non-human-callers.md` — stress test that produced the four guards
- `docs/spec-audit-framework.md` — detailed reference

The v1.1 skill remains at `docs/skills/tier2/gherkin-scenario-quality.md` for reference and article comparison.

For output formatting, apply `docs/skills/tier1/output-formatting-standard.md`.
