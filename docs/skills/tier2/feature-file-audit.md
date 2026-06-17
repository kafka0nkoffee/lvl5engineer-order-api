# Skill: Feature File Audit

**Tier:** 2 — Domain methodology
**Version:** 1.0
**Last updated:** 2026-06-16 (Issue #13)
**Project:** lvl5engineer-order-api

---

## Description

Audit a Gherkin feature file for spec debt using the six-class taxonomy and return a scored report.

---

## When to use this skill

Use this skill when:
- You are about to fix scenarios in a feature file and need to find all debt items first
- You have been asked to audit a feature file for spec debt
- A feature file has not been audited since new scenarios were added
- You are assessing debt density before a major implementation session

Do NOT use this skill when:
- You need to fix a specific scenario — use gherkin-scenario-quality-v2.md for that
- You need to write new scenarios — use gherkin-scenario-quality-v2.md for that
- The target file is `order_status_bad.feature` — this is a pedagogical artifact kept
  intentionally as a bad spec. Do not audit it; return:
  ```text
  # SKILL HALT: order_status_bad.feature is a pedagogical artifact.
  # Its debt items are intentional. Do not audit or fix it.
  ```
- You are auditing step definitions in `tests/steps/` — this skill applies to `.feature`
  files only; step definitions are implementation code

---

## Methodology

### The five-question diagnostic

For every scenario in the target file, apply each question in sequence. Do not skip
questions. Do not answer "no debt" without working through each one explicitly.

**Q1: Who owns this scenario?**
Can you name the single service this scenario belongs to? If the scenario asserts behavior
of a second service in a Then clause, it has MIXED CONCERN debt. The order-api project has
four feature files; each scenario belongs to exactly one. A scenario covering behavior that
straddles two files is in the wrong file.

**Q2: What decisions does this scenario leave open?**
For each step, ask: what would a second agent build from this step that is different from
what the first agent built, and would both pass? Patterns that always leave decisions open:
- Vague qualifiers: "correct", "valid", "appropriate", "reasonable"
- Unanchored time bounds: "within N seconds" (without "of [event]")
- Ambiguous counts: "not retried more than N times" (total or additional?)
- Mechanism claims: "is released", "is notified", "is confirmed" (what is the observable signal?)

**Q3: Are all terms defined within the file?**
Every noun that is not an HTTP primitive (request, response, status code) or language
primitive (string, integer, boolean, UUID) must be defined in the scenario itself or in a
Background clause. Concrete values win over references; named services win over "the external
service."

**Q4: Does this scenario describe behavior or implementation?**
Steps should describe what the system does from the caller's perspective. Leaky abstractions
to catch in this project:
- `db_status` → use `status`
- `order_created_at` or "populated from the order record" → use `placed_at` in ISO 8601
- `the inventory flag is set` → use `the inventory service receives a [request type]`
- `order_record_id` → use `order_id`
- Any reference to "the database", "the cache", "the queue", "the background thread"

**Q5: What does this scenario NOT say that it should?**
For every success scenario: is the HTTP status code specified? Is the full response body
shape specified? Are all side effects on external services asserted?
For every failure scenario: is the error response body specified (not just the status code)?
Is there an assertion that side effects did NOT occur?
For every decision point: is there a separate scenario for each path?

### Debt classification

For each debt item found, classify it using the six-class taxonomy:

| Class | Definition |
|---|---|
| UNDERSPECIFIED | Step present but leaves a decision open; two implementations could pass |
| MIXED CONCERN | Scenario covers more than one service domain |
| UNDEFINED TERM | Noun used without definition anywhere in the file |
| AMBIGUOUS COUNT | Quantity expressed with two valid English interpretations |
| IMPLICIT FLOW | Scenario implies a follow-up flow that is not specced anywhere |
| LEAKY ABSTRACTION | Step references implementation details: internal field names, storage layer semantics, infrastructure concepts |

### Priority assessment

AMBIGUOUS COUNT and IMPLICIT FLOW have the highest production risk:
- AMBIGUOUS COUNT: incompatible implementations that both pass tests; surfaces in
  production when two systems integrate
- IMPLICIT FLOW: invented features; an agent that reads "no order is confirmed without
  explicit user action" builds an unspecced API endpoint

Fix these first. LEAKY ABSTRACTION and UNDEFINED TERM erode maintainability over time.
MIXED CONCERN requires a restructuring session (moving scenarios between files) — schedule
separately.

---

## Output contract

What this skill must produce:

- A completed audit scorecard for the target feature file:

```text
Feature file: [filename]
Total scenarios: ___
Scenarios with at least one debt item: ___

Debt items by class:
  UNDERSPECIFIED:    ___
  MIXED CONCERN:     ___
  UNDEFINED TERM:    ___
  AMBIGUOUS COUNT:   ___
  IMPLICIT FLOW:     ___
  LEAKY ABSTRACTION: ___

Total debt items: ___
Debt density (items/scenario): ___

Priority fixes (AMBIGUOUS COUNT and IMPLICIT FLOW first):
  1.
  2.
  3.
```

- For each debt item, one entry specifying:
  - Scenario name
  - Clause (Given/When/Then + the step text)
  - Class
  - Detail: one sentence explaining why this is debt and what it leaves open

What this skill must NOT produce:

- A corrected or rewritten version of the feature file (use gherkin-scenario-quality-v2.md)
- Prose recommendations that are not anchored to a specific scenario and clause
- Debt items classified as "possible" or "maybe" — every item must be a yes/no classification

---

## Quality criteria

Before returning the audit report:

1. **Completeness**: Every scenario in the file has been assessed against Q1–Q5.
2. **Classification specificity**: Each debt item has exactly one class from the six-class
   taxonomy. If a step has two debt classes, list it twice.
3. **Debt density**: Verify the calculation (total items ÷ total scenarios). Flag anything
   above 1.0 as high density requiring immediate attention.
4. **Priority section**: At least one item in the priority section if any AMBIGUOUS COUNT or
   IMPLICIT FLOW items were found.
5. **No rewrites**: Verify that the output contains no corrected Gherkin scenarios.

---

## Edge cases and failure modes

**order_status_bad.feature:** SKILL HALT — pedagogical artifact, do not audit.

**Empty feature file (no scenarios):** Return scorecard with all zeros and note: "No
scenarios found in this file. If this is a new file, add scenarios before auditing."

**Feature file for a new service not in the project's four named files:** Proceed with the
audit. Q1 should classify ownership as "requires new feature file" for scenarios that don't
fit the existing four files.

**Step definition gap (spec says X, step definition asserts Y):** Note the gap in the debt
item's Detail field as "spec-implementation gap" — this is a special case of LEAKY
ABSTRACTION where the gap is in the step definition, not the spec text. Do not modify the
step definition; document the discrepancy.

---

## Version history

| Version | Change | Issue |
|---------|--------|-------|
| 1.0 | Initial skill — converts spec-audit-framework.md to a routable skill | #13 |

---

## Reference

This skill is the callable interface for the methodology documented in full at:
`docs/spec-audit-framework.md`

For fixing individual debt items after the audit, use:
`docs/skills/tier2/gherkin-scenario-quality-v2.md`

The framework was applied to all four feature files in Issue #8. Results are in:
`docs/spec-audit-framework.md §"Section 5 — Framework Applied: This Project"`
