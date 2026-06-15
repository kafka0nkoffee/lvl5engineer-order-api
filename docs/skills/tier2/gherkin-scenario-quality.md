# Skill: Gherkin Scenario Quality

**Tier:** 2 — Domain methodology
**Version:** 1.1
**Last updated:** 2026-06-13 (Issue #9)
**Project:** lvl5engineer-order-api

---

## Description

Evaluate and produce well-formed Gherkin scenarios for the order-api project using the five-question debt diagnostic and output contract.

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

---

## Methodology

### The five-question diagnostic

Apply these five questions to every scenario you write or review. Do not skip questions. Do not answer "no issues" without working through each one explicitly.

**Q1: Who owns this scenario?**
Can you name the single service this scenario belongs to? Every step in the scenario should describe behavior of that one service. If a Then clause asserts behavior of a second service (e.g., "the notification service sends an email" in an order creation scenario), the step belongs in the notification service's feature file.

The order-api project has four feature files. Assign each scenario to exactly one:
- `order_creation.feature` — behavior of POST /orders
- `order_status_good.feature` — behavior of GET /orders/{id}/status (correct spec)
- `order_status_bad.feature` — pedagogical artifact, do not add new scenarios here
- `notification_service.feature` — behavior of the notification flow

If a new endpoint has no feature file, create one. Do not add scenarios for a new endpoint to an existing feature file that covers a different endpoint.

**Q2: What decisions does this scenario leave open?**

For each step, ask: what would a second agent build from this step that is different from what the first agent builds, and would both pass?

The following step patterns always leave decisions open and must be rewritten:
- `"correct"`, `"valid"`, `"appropriate"`, `"reasonable"` — replace with the exact value or format
- `"within N seconds"` — replace with `"within N seconds of [start anchor]"`
- `"is released"`, `"is notified"`, `"is confirmed"` — replace with the observable signal (an HTTP request to a named service, a specific response field and value)
- `"not retried more than N times"` — replace with `"receives no more than N [request type] total"`
- `"the response includes a [X]"` — replace with `"the response body contains a [field name] field with value [concrete value]"`

**Q3: Are all terms defined within the file?**

Every noun that is not an HTTP primitive (request, response, status code, header, body) or a language primitive (string, integer, boolean, UUID) must be defined in the scenario itself or in a Background clause.

Check:
- Is the order ID defined as a concrete value (`"order-del-001"`) rather than a reference (`"the order"`)? Concrete values win over references every time.
- Is the external service named explicitly (`"the payment gateway"`, `"the inventory service"`)? Never `"the external service"` or `"the dependency"`.
- Is the state precondition named after the observable state, not the internal mechanism? (`"status CONFIRMED"` not `"the confirmed flag is set"`)

**Q4: Does this scenario describe behavior or implementation?**

Remove the implementation from your mind and read each step as the caller. Does the step still make sense? If a step requires knowing how the system is built internally to understand what it asserts, it is leaking implementation.

Specific leaks to catch in this project:
- `db_status` — this is the storage field name. Use `status`.
- `order_created_at` or `populated from the order record` — use `placed_at` in ISO 8601 format.
- `the inventory flag is set` — use `the inventory service receives a [request type] request`.
- `order_record_id` — use `order_id`.
- Any reference to "the database", "the cache", "the queue", "the background thread" — these are implementation details. Replace with the observable behavior at the API surface.

**Q5: What does this scenario NOT say that it should?**

For every success scenario, check:
- Is the full response body shape specified? (all required fields, their names, their values or formats)
- Is the HTTP status code specified?
- Are all side effects on external services asserted? (payment gateway calls, inventory service calls)

For every failure scenario, check:
- Is the error response body specified? (not just the status code)
- Is the error value a named constant from the domain? (not `"some error"` or `"an error message"`)
- Does the scenario assert that side effects did NOT occur when they should not have? (`"the payment gateway receives no requests"` in a stock-out scenario)

For every decision point (an if/else in the implementation), check:
- Is there a separate scenario for each path? Success case, failure case, edge case are each a separate scenario.

---

## Output contract

What this skill must return:

- **One or more complete Gherkin scenarios** in `Given/When/Then` format, ready to paste into a `.feature` file
- **Each scenario title** must explicitly name the decision point: not `"Successful cancellation"` but `"Confirmed order is cancelled when payment has not yet been captured"`
- **All Then clauses** must assert a field name AND a value — never just presence (`"contains an order_id"` is insufficient; `"contains an 'order_id' field with value 'order-del-001'"` is sufficient)
- **All counts** must use `"exactly N"` or `"no more than N total"` — never `"N times"` alone
- **All time bounds** must include a start anchor — never `"within N seconds"` alone
- **All Given clauses referencing external services** must name the service explicitly
- **Assumptions** — any decision not in the input (e.g., choosing 422 over 409 for a specific failure mode) must appear as a `# Assumption:` comment immediately below the step that embeds it, formatted as:
  ```
  # Assumption: 422 chosen over 409 — unprocessable entity fits better than conflict here.
  # Verify against product spec before committing.
  ```
- **No internal field names** — if in doubt, use the field name as a caller would name it, not as the database schema names it

### What the output must NOT contain:
- Prose explanation of what was found (save that for the findings file)
- Inline comments that explain the logic of a step — the step should be self-explanatory
- `Scenario Outline:` with Examples tables unless the input explicitly requires parametric scenarios
- References to implementation details (database, cache, background thread, internal flags)

---

## Quality criteria

Before returning output, ask:

1. **Compatibility**: Would a second agent, reading the same input, produce scenarios with the same field names, status codes, and assertion values? If not, find the step that introduces ambiguity and rewrite it.

2. **Contract completeness**: Does every scenario fully specify: the precondition state, the triggering action with its exact parameters, the response HTTP status, the response body shape, and any side effects on external services?

3. **Decision visibility**: List every decision you made that was not in the input. Each one must appear as a `# Assumption:` comment. If you cannot list them (because you made them implicitly), go back and find them.

4. **Ownership**: Can you name the feature file this scenario belongs to without consulting any other document? If not, the scenario's scope is wrong.

5. **Five-question pass**: Step through Q1–Q5 for the output you are about to return, not just for the input. The output can introduce new problems.

---

## Edge cases and failure modes

**Do not use this skill when the spec is intentionally bad.**
`order_status_bad.feature` is a pedagogical artifact — it is kept as an example of spec debt. Do not apply this skill's quality criteria to it; do not "fix" it. The file's debt is intentional and documented.

**Do not use this skill to evaluate step definitions.**
Step definitions in `tests/steps/` are implementation code. Their quality is assessed by whether they correctly implement the scenario, not by whether the scenario's wording is precise. A well-formed scenario can have a poorly-written step definition. The skill's scope ends at the `.feature` file.

**Do not use this skill when the product requirement is itself ambiguous.**
If the input says "implement cancellation for orders" without specifying what "cancelled" means, do not invent the semantics. Return: "The input is ambiguous about [specific decision]. Please specify [concrete options] before I can produce a well-formed scenario." Producing a scenario with invented semantics is worse than producing no scenario — it hides the ambiguity behind passing tests.

**Do not use this skill for non-order-api projects without adapting Section Q4.**
The specific field name substitutions in Q4 (`db_status` → `status`, `order_created_at` → `placed_at`) are specific to this project's known leaky abstractions. On a different project, apply the Q4 principle (caller perspective vs implementation perspective) but do not apply these specific substitutions.

**Do not return a single scenario when the input describes multiple decision paths.**
If the input describes an operation that can succeed or fail (e.g., "cancel an order — only possible if payment hasn't been captured"), the output must include at least one scenario per path. A single success-case scenario is incomplete output, not a first draft.

---

## Version history

| Version | Change | Issue |
|---------|--------|-------|
| 1.0 | Initial skill from Issues #5–#8 methodology | #9 |
| 1.1 | Added IMPLICIT FLOW to methodology; added "do not return a single scenario" failure mode | #9 |

---

## Reference

This skill formalizes the methodology developed across:
- `findings/issue-05-the-spec-that-doesnt-lie.md` — bad-vs-good spec demonstration
- `findings/issue-07-scope-problem.md` — spec at service boundaries
- `findings/issue-08-spec-audit.md` — full audit and fix session
- `docs/spec-audit-framework.md` — the full five-question framework (detailed reference)

The prompt version of this skill (before formalization) is at `docs/prompts/prompt-gherkin-scenario-quality.md`.

For output formatting of the scenarios this skill produces, apply `docs/skills/tier1/output-formatting-standard.md`.
