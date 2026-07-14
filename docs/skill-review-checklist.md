---
type: Reference
title: "Skill Review Checklist"
description: "Five-dimension checklist for reviewing skill artifacts before publishing a new skill version; must be completed before any skill PR is approved."
tags: [reference, skill-review, checklist, skill-governance]
timestamp: 2026-06-16
---

# Skill Review Checklist

**Version:** 1.0
**Last updated:** 2026-06-16 (Issue #12)

A skill review is not a code review. The review target is the skill artifact itself: its
routing signal, its output contract, its methodology, its failure modes. A reviewer who reads
a skill file and asks "does this look reasonable?" is not doing a skill review. A reviewer
who works through this checklist is.

This checklist must be completed before approving any new skill version. Every question must
be answered. "No issues" is only a valid answer when the reviewer has explicitly worked
through the question.

For the PR template that uses this checklist, see `docs/skill-pr-template.md`.

---

## Dimension 1: Routing signal review

The routing signal is the skill's description line — the single line used by agent
frameworks to match prompts to skills. A broken routing signal means the skill is never
called. All behavioral improvements in a skill are unreachable if the routing signal fails.

Review the routing signal FIRST, before behavioral testing.

---

**1.1 Is the description on a single line and under 120 characters?**

Count the characters in the description. Multi-line descriptions break routing in most agent
frameworks. Descriptions over 120 characters are truncated or deprioritized by routing
frameworks with character limits.

> Pass: Single line, ≤ 120 characters.
> Fail: Multi-line, OR character count > 120. Record the count and the excess.

---

**1.2 Does the description name the artifact type the skill produces?**

The artifact type is what a caller receives when the skill completes successfully.

Not "specs" — Gherkin scenarios.
Not "output" — the specific artifact name.
Not "results" — the specific artifact name.

> Pass: Artifact type is named using its domain-specific term.
> Fail: Artifact type is named with a generic synonym. Record which synonym is used
> and what it should be replaced with.

---

**1.3 Does the description name the domain or project scope?**

Without a scope constraint, the skill can be routed into contexts where it does not apply.
A skill that produces Gherkin scenarios for an order management API should not route when
someone asks for Gherkin scenarios for a user authentication service.

> Pass: Domain or project is named explicitly in the description.
> Fail: Description could match any project. Record which routing contexts would
> incorrectly match.

---

**1.4 Does the description name the methodology used?**

The methodology distinguishes this skill from other skills that produce the same artifact
type without the same rigor. "Write Gherkin scenarios" is a skill. "Write Gherkin scenarios
using the five-question debt diagnostic" is a different skill.

Check: Does the named methodology describe the distinguishing approach, or does it name
an internal implementation detail (e.g., "using four pre-flight guards")? Internal
implementation details do not help routing.

> Pass: Methodology is named in terms visible and meaningful to a caller.
> Fail: No methodology named, OR methodology is named as an internal mechanism.
> Record what the correct methodology description should be.

---

**1.5 Routing test — six prompt verification**

Write three prompts that SHOULD route to this skill and three that SHOULD NOT. Verify that
the description routes correctly for all six. Document any misroutes found.

The three SHOULD prompts must cover different caller intents (e.g., write new, review
existing, audit for debt). The three SHOULD NOT prompts must cover inputs that share surface
features with the skill's domain (e.g., same domain, different artifact; same artifact,
different domain; same artifact and domain, but out-of-scope task).

> Pass: All six prompts route correctly based on the description alone.
> Fail: Any misroute found. Record which prompt mismatch occurs and why.
> Document misroutes even if the skill header metadata would prevent them —
> routing signal review tests the description, not the full file.

---

## Dimension 2: Output contract review

The output contract specifies what a caller receives. It is the interface between the skill
and its downstream consumers. An output contract that requires running the skill to verify
is not a contract — it is a description of the skill's current behavior.

---

**2.1 Is the output contract explicit and enumerable?**

Each requirement in the output contract must be a yes/no check that a reviewer can apply
to a skill output without running the skill. Judgment calls are not enumerable requirements.

For each requirement, ask: can two reviewers independently verify this requirement against
the same output and reach the same conclusion?

> Pass: Every requirement is a yes/no check with unambiguous criteria.
> Fail: Any requirement requires judgment to evaluate. Record which requirements
> are ambiguous and what would make them enumerable.

---

**2.2 Could two agents produce different outputs that both satisfy the contract?**

Apply the contract to a hypothetical output. Now construct a different hypothetical output
that also satisfies the contract but differs structurally from the first. If you can, the
contract is under-specified.

Common under-specification patterns:
- Contract specifies presence but not content (e.g., "includes a status field" but not which
  values are valid)
- Contract specifies format but not which items must use that format (e.g., "all external
  services named" but not which services are required for each scenario type)
- Contract specifies shape but not count (e.g., "one or more scenarios" without specifying
  how many paths require separate scenarios)

> Pass: No alternative output exists that satisfies the contract while differing
> structurally from the expected output.
> Fail: Alternative valid outputs exist. List the under-specified requirements.

---

**2.3 Does the contract specify what the skill must NOT produce?**

Absence requirements are as important as presence requirements. A contract that specifies
what must be in the output but not what must be absent is incomplete.

Common absence requirements for skill output contracts:
- No prose explanation in the artifact (for artifacts that are code or structured text)
- No implementation details in interface-layer artifacts
- No unnecessary changes to already-correct content (for review/improvement skills)

> Pass: Absence requirements are listed and enumerable.
> Fail: No absence requirements, OR absence requirements are vague.
> Record which absence requirements are missing.

---

**2.4 Is there a downstream consumer identified for this skill's output?**

Document:
- What system or agent receives the skill's output
- What that consumer does with the output (pastes it into a file? feeds it to another
  skill? presents it to a human for review?)
- Whether the output contract is sufficient for that consumption pattern

Check: Does the skill have multiple output types (e.g., normal output for one consumer
and failure signals for a different consumer)? If yes, are BOTH consumers identified?

> Pass: Downstream consumer is named and the contract is sufficient for its
> consumption pattern.
> Fail: Consumer not identified, OR contract is insufficient for the identified
> consumption pattern. Record what is missing.

---

**2.5 Is the output contract testable without running the skill?**

For each requirement in the output contract, confirm that a reviewer can check it by
reading the output, not by running the skill against the same input.

A contract requirement that can only be verified by running the skill is a description of
current behavior, not a contract. It will not catch regressions introduced by rewrites.

> Pass: All requirements are checkable by reading the output.
> Fail: Any requirement requires running the skill to verify. Record which
> requirements are behavior-descriptions rather than contracts.

---

## Dimension 3: Methodology review

The methodology section describes how the skill produces its output. A methodology that
describes procedure ("do X, then Y") gives an agent a process to follow but no reasoning to
apply when the process doesn't fit. A methodology that describes reasoning ("when you see X,
the correct decision is Y because Z") gives an agent a principle that generalizes.

---

**3.1 Does the methodology describe reasoning, not procedure?**

For each section of the methodology, ask: if an agent encounters an input not covered by
the examples, can it apply the methodology to produce correct output? If the methodology is
purely procedural (a list of steps or patterns), the answer is usually no.

Procedure: "Step 1: Check X. Step 2: Check Y."
Reasoning: "When you see pattern X, the correct response is Y because the caller cannot
distinguish between [A] and [B] from the outside."

> Pass: Each methodology section explains why, not just what.
> Fail: Any section is purely procedural without justification. Record which sections
> lack reasoning and what the reasoning should be.

---

**3.2 Does the methodology generalize to inputs not shown in examples?**

Pick three edge case inputs not covered by any examples in the methodology. Apply the
methodology manually. Document whether the methodology produces correct output for all three.

Choose edge cases that probe the boundary conditions:
- An input that is valid but unusual for the domain
- An input that is partially in scope and partially out of scope
- An input that satisfies the preconditions but violates an implicit assumption in the
  methodology

> Pass: Methodology produces correct output for all three edge cases.
> Fail: Any edge case produces incorrect output or undefined behavior.
> Record the edge case, the methodology's output, and what the correct output should be.

---

**3.3 Is there domain knowledge in the methodology that requires documentation?**

Domain knowledge is knowledge that an agent cannot infer from first principles. It must be
stated explicitly, not implied. Examples:

- Field name substitutions specific to this project's leaky abstractions
- Feature file naming conventions not derivable from the project structure
- Status code assignments not defined by a standard
- External service names used in assertions

For each piece of domain knowledge, ask: would a new agent, reading only this skill file
and the project files it references, know this without being told?

> Pass: All domain knowledge is documented explicitly.
> Fail: Any domain knowledge is implied rather than stated. Record what is missing
> and where it should be added.

---

**3.4 Does the methodology handle the failure cases identified in "Edge cases and
failure modes"?**

For each listed failure case, trace through the methodology to find where it diverges from
the default path. If the methodology doesn't diverge — if it continues as normal — the
failure case is listed but not handled.

> Pass: Every listed failure case has a corresponding divergence point in the
> methodology.
> Fail: Any listed failure case is handled only in the edge cases section without a
> corresponding methodology divergence. Record which cases are documented but
> not handled.

---

## Dimension 4: Idempotency and stability review

A stable skill produces the same structural output when applied to the same input, regardless
of how many times it is applied. An unstable skill rewrites correct output — creating
unnecessary churn, dropping documented decisions, and producing outputs that downstream
agents cannot distinguish from necessary changes.

---

**4.1 Apply the skill to the same input three times with different framings. Do all three
produce structurally identical output?**

Use the same underlying scenario or content, but frame it differently: as a direct
instruction, as a user story, as an audit request. If structural elements vary (field names,
ID values, HTTP status codes, assumption comment placement), record which elements varied
and why.

> Pass: All three framings produce structurally identical output.
> CONDITIONALLY STABLE: Content is identical but structural elements vary
> (e.g., assumption comment placement differs).
> Fail (UNSTABLE): Content varies across framings.

---

**4.2 Apply the skill to an already-correct input. Does the skill return it unchanged, or
does it produce unnecessary rewrites?**

Construct an input that satisfies the output contract exactly. Apply the skill. If the skill
produces any change, record what changed and whether it was necessary to satisfy the contract.

An unnecessary rewrite is a change that modifies content or structure that already satisfied
the contract, even if the new version also satisfies the contract.

> Pass: Already-correct input is returned unchanged (or with an explicit "no changes
> required" signal).
> Fail: Already-correct input is rewritten. Record what changed.

---

**4.3 Apply the skill to its own output. Does it return unchanged, or produce a third
version?**

Feed the skill's output from one run as the input to a second run. If the skill produces
a different output (a "third version"), the skill is failing the self-reference test.

This test is the strictest idempotency check: a skill that rewrites its own output will
create an infinite rewrite chain in any agent pipeline that loops.

> Pass: Skill applied to its own output returns it unchanged.
> Fail: Skill rewrites its own output. Record what changed in the second run.

---

**4.4 Document the idempotency verdict**

Based on 4.1–4.3, assign one of three verdicts:

**STABLE** — All three tests pass. The skill produces the same output for the same input
regardless of framing, and returns already-correct input unchanged.

**UNSTABLE** — Any of the three tests fail. The skill rewrites correct input, produces
varying output for different framings, or rewrites its own output.

**CONDITIONALLY STABLE** — The skill is stable on content but unstable on structure
(e.g., assumption comment placement varies, or already-correct inputs trigger minor
reformatting). Record the condition under which stability breaks.

> Document the verdict with evidence from 4.1–4.3.

---

## Dimension 5: Failure mode review

A skill's failure modes are the inputs where the skill produces incorrect or dangerous
output. The most dangerous failure mode is PLAUSIBLE WRONG: output that looks correct but
contains an error. Explicit failures (FAIL SIGNAL, CORRECT REFUSAL) are better because they
surface the problem. Silent wrong output is worse because it passes downstream checks.

---

**5.1 Does the skill have explicit termination conditions for out-of-scope inputs?**

Identify one input that is outside the skill's domain. Apply the skill. Document whether:
- The skill fails explicitly (FAIL SIGNAL: named error, no output)
- The skill refuses with guidance (CORRECT REFUSAL: actionable error message)
- The skill translates the out-of-scope input silently (PLAUSIBLE WRONG)

An out-of-scope input is one that is superficially similar to the skill's domain but belongs
to a different layer, service, or artifact type.

> Pass: FAIL SIGNAL or CORRECT REFUSAL for the out-of-scope input.
> Fail: PLAUSIBLE WRONG or uncaught exception. Record what the skill produced.

---

**5.2 Does the skill have explicit handling for contradictory inputs?**

Identify one input that contains logically incompatible constraints. Apply the skill.
Document the output.

Common contradiction patterns: "exactly N" and "no more than M" for N > M on the same
action; "always" and "never" for the same condition; a precondition that contradicts the
action being taken.

> Pass: FAIL SIGNAL or CORRECT REFUSAL for contradictory input. The skill halts and
> names the contradiction.
> Fail: PLAUSIBLE WRONG — the skill documents the contradiction as a comment and
> proceeds. Record what the skill produced.

---

**5.3 Does the skill have explicit handling for empty or degenerate inputs?**

Apply the skill to an empty input. Document the output.

An empty input is one with no content relevant to the skill's task (blank scenario, empty
prompt, missing required fields). A degenerate input has the minimum required structure but
no semantic content.

> Pass: FAIL SIGNAL or CORRECT REFUSAL for empty input. The skill halts and
> provides actionable guidance.
> Fail: PLAUSIBLE WRONG — the skill produces output from nothing. Record what it
> produced.

---

**5.4 For each failure mode, classify the output**

For every failure mode in the skill's "Edge cases and failure modes" section, and for any
new failure modes found in 5.1–5.3, apply one classification:

**FAIL SIGNAL** — The skill failed explicitly, no output was produced, and the caller knows
the skill did not complete. Appropriate for unrecoverable inputs where proceeding would
produce wrong output.

**CORRECT REFUSAL** — The skill refused with an actionable error message. The caller knows
the skill did not complete AND knows what to do next. Better than FAIL SIGNAL.

**PLAUSIBLE WRONG** — The skill produced output that looks correct but contains an error.
The caller cannot tell the output is wrong without independent verification. This is the
worst outcome.

> Document one classification per failure mode. Note any PLAUSIBLE WRONG outcomes,
> which require remediation before the skill version is approved.

---

**5.5 Are all PLAUSIBLE WRONG outcomes eliminated in the current version?**

Review the classification table from 5.4. For each PLAUSIBLE WRONG outcome:
- Can it be converted to a CORRECT REFUSAL by adding an explicit termination condition?
- If not, why is the PLAUSIBLE WRONG outcome acceptable in this version?

A PLAUSIBLE WRONG outcome that remains in an approved skill version requires a documented
exception: what is the scope of the wrong output, how likely is it to be encountered, and
why is it not blocking.

> Pass: No PLAUSIBLE WRONG outcomes remain, OR remaining ones have documented
> exceptions that are reviewed and accepted.
> Fail: PLAUSIBLE WRONG outcomes remain without documented exceptions.
> Record which ones remain and block approval until resolved or accepted.

---

## Review completion

After working through all five dimensions:

1. Record the verdict:
   - **APPROVED** — No issues found across all five dimensions.
   - **APPROVED WITH COMMENTS** — Issues found that do not block approval but should be
     addressed in a future version. Document each issue and the version that should address it.
   - **CHANGES REQUESTED** — Issues found that block approval. Document the required changes
     and the dimension where each was found.

2. Document what the review caught that behavioral testing (stress tests, integration tests)
   did NOT find. This is the primary value of the review.

3. Sign off using the template in `docs/skill-pr-template.md`.
