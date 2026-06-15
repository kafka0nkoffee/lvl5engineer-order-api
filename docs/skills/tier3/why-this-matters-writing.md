# Skill: "Why This Matters" Paragraph Writing

**Tier:** 3 — Personal workflow
**Version:** 1.0
**Last updated:** 2026-06-15 (Issue #10)
**Project:** lvl5engineer-order-api

**Socialization decision:** Promote to Tier 2 — see end of this file.

---

## Description

Write the "Why this matters" paragraph for a findings file entry using the four-component structure derived from Issues #2–#9.

---

## When to use this skill

Use this skill when:
- You are completing a `### Why this matters` section in a findings file
- You have finished documenting a finding (What I tried / What happened / Root cause / The fix) and need to write the newsletter-facing paragraph
- You are reviewing an existing "Why this matters" paragraph to assess whether it is complete

Do NOT use this skill when:
- You are writing the other four sections of a finding — this skill is only for the "Why this matters" paragraph
- You are writing the "closing reflection" at the end of a full findings file — that is a different artifact with a different structure
- You are summarizing changes for a commit message — commit messages are governed by the Tier 1 output formatting standard

---

## Methodology

The "Why this matters" paragraph has a specific four-component structure derived from reading the nine existing findings files in this project. The structure is not arbitrary — it reflects the editorial logic of the newsletter: give the reader the specific before the general, the principle before the failure, and the failure before the implication.

### The four components, in order

**Component 1 — The practitioner observation**
State the specific technical finding as a practitioner would state it: as something that was true and was observed, not as a problem that was solved. The observation should be specific enough that a reader who wasn't in the session can understand exactly what was found.

Not: "We discovered that spec debt can be hard to find."
Yes: "Spec debt can migrate from the feature file into the step definition."

The observation must reference something concrete from the finding: a file, a line, a pattern, a number. If you cannot make it concrete, the finding is not fully documented yet.

**Component 2 — The transferable principle**
One sentence connecting the specific observation to a principle that applies beyond this codebase. This is the sentence that makes the paragraph useful to a reader who works on a different project. It must be derivable from the observation — not imported from a general engineering principle that was already known before the finding.

Not: "This is why it's important to write good tests."
Yes: "Treat step definitions as part of the spec surface, not just as test harness code."

**Component 3 — The failure mode**
Name the specific failure that would occur if the finding had not been made or the principle had not been applied. Concrete: name the system, the outcome, the mechanism. Not "things would have gone wrong" but "a second agent reading the same scenario would have built a confirmation flow that doesn't exist in the product spec, and it would have passed all tests."

The failure mode must be causally connected to the observation in Component 1. If you have to introduce a new concept to name the failure mode, you are either writing about a different finding or the observation was not specific enough.

**Component 4 — The reader's implication**
One sentence: what should the reader do differently in their own practice as a result of this finding? Phrased as a positive action, not a warning. The implication must be actionable — something the reader can apply in the next session.

Not: "So be careful when writing specs."
Yes: "The practical conclusion: run the five-question diagnostic on step definitions as well as feature files."

### How to sequence the components

Write them in order: 1 → 2 → 3 → 4. Do not invert. The observation grounds the principle. The principle frames the failure mode. The failure mode motivates the implication. Inverting any pair produces a paragraph that reads as generic advice followed by a belated example — which is the pattern of a bad blog post, not a good finding.

### Length and tone

Four to six sentences total. One paragraph. No bullet points. No sub-paragraphs. No headers.

Voice: peer-to-peer. The reader is a senior engineer who hasn't seen this codebase. They do not need the context explained to them — they need the observation stated clearly so they can evaluate whether the principle applies to their own work.

Do not hedge. "This might suggest that" and "it's possible that" are weak. The observation is what it is. State it.

---

## Output contract

The output is a single paragraph containing all four components in order, conforming to the Tier 1 formatting standard (`docs/skills/tier1/output-formatting-standard.md`):

- One paragraph, 4–6 sentences
- Opens with Component 1 (the observation), not with "This finding shows that..." or "In this session..."
- No first-person plural ("we discovered") — use impersonal or second-person
- No reference to "this codebase" or "this project" — the principle must generalize
- Ends with Component 4 (the implication) as an actionable statement

---

## Quality criteria

Before submitting, ask:

1. **Specificity of the observation**: Could a reader identify the specific file, pattern, or number that the observation refers to, without reading the rest of the finding? If not, the observation is too abstract.

2. **Independence of the principle**: Could the principle in Component 2 have been stated before the finding was made? If yes, it is a general principle being illustrated by the finding, not a principle derived from it. Rewrite it to be derivable from the observation.

3. **Causality of the failure mode**: Is the failure mode causally connected to the observation? If removing Component 1 from the paragraph would leave Component 3 making no sense, the causality is present. If Component 3 could stand alone as a general warning, it is not connected to the specific finding.

4. **Actionability of the implication**: Can the reader do something different in their next session based on Component 4? If the implication is "pay more attention to X," it is not actionable enough. "Apply Q4 to step definitions as well as feature files" is actionable. "Be more careful about step implementations" is not.

---

## Examples from this project

**Issue #5** (good spec vs bad spec):

> The bad spec was written from the implementation's perspective — it described what the code did. The good spec was written from the caller's perspective — it describes what the caller can rely on. The two perspectives produce very different Gherkin even when they describe the same endpoint. Passing tests are not evidence that the spec is correct — they are only evidence that the implementation satisfies the spec. If the spec is wrong, passing tests are indistinguishable from a correct implementation of a wrong contract.

Components: Observation (bad spec describes implementation; good spec describes caller contract) → Principle (two perspectives produce different Gherkin for the same endpoint) → Failure mode (passing tests cannot distinguish correct implementation from wrong contract) → Implication (implicit: write from the caller's perspective, not the implementation's).

**Issue #9** (prompt vs skill):

> The prompt produces output that passes today's tests; the skill produces output that a different agent can implement tomorrow without making any decisions you didn't make. Copying a prompt copies the words but not the contract. The skill specifies what to produce, not just what to consider. The step definitions in `tests/steps/` are only as reliable as the scenarios they implement — and the scenarios are only as reliable as the judgment that produced them.

Components: Observation (prompt vs skill — decisions embedded vs decisions surfaced) → Principle (copying a prompt copies words, not contract) → Failure mode (step definitions are only as reliable as the scenarios) → Implication (implicit: use skills with output contracts for artifacts consumed by downstream agents).

---

## Edge cases

**The finding is purely operational (a command was run, a server started):** Do not write a "Why this matters" paragraph for purely operational steps. Reserve this structure for findings that contain a lesson. An operational step that worked as expected has no observation, no principle, and no failure mode worth writing.

**The finding has multiple root causes:** Write one "Why this matters" paragraph per distinct root cause. If two causes share the same principle, they can share a paragraph — but only if both observations are stated in Component 1.

**The finding failed and the root cause was simple (e.g., a typo):** The "Why this matters" paragraph is not required for simple mechanical failures. If the root cause is "I misread a variable name," the finding can end at `### The fix` with a note: "No generalisable lesson — mechanical error."

---

## Socialization decision: promote to Tier 2

**Decision date:** 2026-06-15 (Issue #10)
**Verdict:** Promote to Tier 2

**Promotion criteria check:**
Would every agent working on this project benefit from this skill, or is it specific to one person's working style?

The four-component structure is not personal style — it is an output contract for the most reused artifact in this project. The findings files are the raw material for the newsletter, and structural consistency across them is a project requirement. An agent writing Issue #14's findings without this skill will produce a "Why this matters" paragraph that satisfies CLAUDE.md's "one paragraph, senior engineer voice" requirement but may invert the component order, omit the failure mode, or write the implication as a general principle rather than a specific action.

**What must change before promotion:**
1. The description line must be refined for routing: the current description routes correctly when the agent is writing a findings entry, but would benefit from naming the output artifact more precisely.
2. The "Do NOT use this skill when" section should be reviewed to include the closing reflection pattern (which has a different structure — not four components, but a synthesis across the full session).
3. The skill should be cross-referenced from the Tier 1 output formatting standard, which currently describes the "Why this matters" structure but defers the methodology to this skill.

Until those changes are made, this skill lives at Tier 3 — usable by agents that are explicitly directed to it, but not in the automatic routing set for all agents working on findings files.
