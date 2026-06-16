# Skill PR Template

**Version:** 1.0
**Last updated:** 2026-06-16 (Issue #12)

Use this template when opening a pull request to publish a new skill version. Fill in all
sections. A PR that leaves any section blank does not meet the review bar.

The checklist section maps to the five dimensions in `docs/skill-review-checklist.md`. The
reviewer should complete `docs/skill-review-checklist.md` in full before filling in the
checklist here.

---

## Summary

**Skill:** `[path/to/skill.md]`
**Version:** `[N.M]` (previous: `[N.M-1]`)
**Tier:** `[1 / 2 / 3]`
**Author:** `[name or agent ID]`

### What changed

[One to three sentences. What is different in this version? Be specific: "Added Guard 2 to
halt on UI scenario inputs" is a summary. "Made the skill better for edge cases" is not.]

### Why it changed

[One to three sentences. What triggered this change? A stress test finding? A production
misroute? A review comment? Link to the findings file or issue that motivated the change.]

---

## Behavioral diff

This section describes the behavioral difference between the previous version and this
version. This is NOT a git diff — it is a description of how the skill's outputs differ for
the same inputs.

For each changed behavior, fill in one row:

| Input type | Previous version behavior | This version behavior |
|---|---|---|
| [describe the input] | [what the previous version produced] | [what this version produces] |

If a behavior is unchanged, do not list it. Only list inputs where the output differs.

**Example rows (for reference — delete before submitting):**

| Input type | Previous version behavior | This version behavior |
|---|---|---|
| Already-correct scenario | Full rewrite produced | Input returned unchanged with annotation |
| UI scenario (Cypress-style) | Translated to API scenario | Guard fires; CORRECT REFUSAL returned |
| Contradictory constraint scenario | Contradiction documented as assumption; proceeds | Guard fires; CORRECT REFUSAL returned |

---

## Review checklist

The reviewer completes this section after working through `docs/skill-review-checklist.md`.
Each checkbox maps to a question in the checklist. Check the box when the question is
answered and the answer is "Pass." For any question that does not pass, leave it unchecked
and add a comment below the checkbox explaining the finding.

### Dimension 1: Routing signal

- [ ] **1.1** Description is a single line and ≤ 120 characters.
  > Character count: ___
  > Finding (if any):

- [ ] **1.2** Description names the artifact type the skill produces.
  > Finding (if any):

- [ ] **1.3** Description names the domain or project scope.
  > Finding (if any):

- [ ] **1.4** Description names the methodology used (not an internal mechanism).
  > Finding (if any):

- [ ] **1.5** Three SHOULD and three SHOULD NOT prompts verified. No misroutes found.
  > SHOULD prompts (list all three):
  > 1.
  > 2.
  > 3.
  >
  > SHOULD NOT prompts (list all three):
  > 1.
  > 2.
  > 3.
  >
  > Misroutes found (if any):

### Dimension 2: Output contract

- [ ] **2.1** Every contract requirement is an enumerable yes/no check.
  > Finding (if any):

- [ ] **2.2** No alternative valid outputs exist that differ structurally from the
  expected output.
  > Under-specified requirements (if any):

- [ ] **2.3** Absence requirements are listed and enumerable.
  > Finding (if any):

- [ ] **2.4** Downstream consumer is identified and the contract is sufficient for their
  consumption pattern. If the skill has multiple output types, all consumers are identified.
  > Consumer(s) identified:
  > Finding (if any):

- [ ] **2.5** All contract requirements are checkable by reading the output, without running
  the skill.
  > Finding (if any):

### Dimension 3: Methodology

- [ ] **3.1** Each methodology section explains why, not just what.
  > Sections lacking reasoning (if any):

- [ ] **3.2** Three edge cases applied manually. Methodology produces correct output for
  all three.
  > Edge case 1: [describe] — Result: Pass / Fail
  > Edge case 2: [describe] — Result: Pass / Fail
  > Edge case 3: [describe] — Result: Pass / Fail
  > Finding (if any):

- [ ] **3.3** All domain knowledge is documented explicitly.
  > Implied knowledge found (if any):

- [ ] **3.4** Every listed failure case has a corresponding divergence point in the
  methodology.
  > Unhandled failure cases (if any):

### Dimension 4: Idempotency and stability

- [ ] **4.1** Three framings of the same input produce structurally identical output.
  > Structural elements that varied (if any):

- [ ] **4.2** Already-correct input is returned unchanged (or with an explicit signal).
  > Finding (if any):

- [ ] **4.3** Skill applied to its own output returns it unchanged.
  > Finding (if any):

- [ ] **4.4** Idempotency verdict documented.
  > Verdict: STABLE / CONDITIONALLY STABLE / UNSTABLE
  > Condition for instability (if CONDITIONALLY STABLE):

### Dimension 5: Failure modes

- [ ] **5.1** Out-of-scope input produces FAIL SIGNAL or CORRECT REFUSAL (not PLAUSIBLE
  WRONG).
  > Test input used:
  > Classification:

- [ ] **5.2** Contradictory input produces FAIL SIGNAL or CORRECT REFUSAL (not PLAUSIBLE
  WRONG).
  > Test input used:
  > Classification:

- [ ] **5.3** Empty input produces FAIL SIGNAL or CORRECT REFUSAL (not PLAUSIBLE WRONG).
  > Classification:

- [ ] **5.4** All failure modes classified. Classification table documented.
  > Number of PLAUSIBLE WRONG outcomes:

- [ ] **5.5** All PLAUSIBLE WRONG outcomes are either eliminated or have documented
  exceptions.
  > Remaining PLAUSIBLE WRONG outcomes (if any):

---

## Findings

### What the review caught that behavioral testing did not find

[This is the primary value of the review. List findings that would not have been found by
running the skill against test inputs. Common categories: routing signal issues, output
contract ambiguity, methodology gaps for unlisted edge cases.]

### New failure modes introduced by this version

[List any failure modes that did not exist in the previous version and are introduced by the
changes in this PR. Include classification (FAIL SIGNAL / CORRECT REFUSAL / PLAUSIBLE WRONG)
for each.]

### Issues deferred to next version

[If any APPROVED WITH COMMENTS issues were found, list them here with the version that should
address them. Format: "v[N.M+1]: [description of what to fix]"]

---

## Sign-off

**Reviewer:** [name or agent ID]
**Review method:** [Manual (read-only) / Manual + behavioral test / Checklist only]
**Date:** YYYY-MM-DD

**Verdict:**
- [ ] APPROVED — No issues found.
- [ ] APPROVED WITH COMMENTS — Issues found, not blocking. See "Issues deferred" above.
- [ ] CHANGES REQUESTED — Issues found, blocking. See "Findings" above.

**Reviewer notes:**

[Any context the reviewer wants the skill author to know that doesn't fit in the checklist
fields above. Optional.]
