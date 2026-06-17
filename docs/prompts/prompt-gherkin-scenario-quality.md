<!-- DEPRECATED: 2026-06-16 — superseded by docs/skills/tier2/gherkin-scenario-quality-v2.md.
     Do not use. Will be removed in Issue #14 session. -->

# Prompt: Gherkin Scenario Quality Check

> The "before" state. This is the prompt as it would be pasted into a Claude Code
> session today — derived from the prose in CLAUDE.md and the spec-audit-framework.md.
> Compare with: docs/skills/gherkin-scenario-quality.md

---

## The raw prompt

Before writing or accepting a Gherkin scenario, check that it is well-formed. A well-formed scenario describes behavior from the caller's perspective, not from the implementation. Each step should be specific enough that only one implementation can satisfy it.

Check for:
- Vague quantities (words like "correct", "reasonable", "appropriate")
- Counts that could be read as total or additional ("not retried more than 2 times")
- Time bounds without a start anchor ("within 12 seconds")
- Mechanism claims without the mechanism ("the reservation is released")
- Internal field names leaking into the spec (database field names, internal flags)

If the scenario has these problems, rewrite it before proceeding.

---

## Honest assessment of weaknesses

### What decisions does this prompt leave open?

**Output format.** The prompt says to "rewrite it before proceeding" but does not say what form the output should take. Does the agent return:
- The corrected Gherkin block only?
- A list of problems found, followed by the corrected Gherkin?
- The original scenario with inline comments marking problems?
- A verbal assessment followed by a recommendation?

All four are valid responses to this prompt. All four are incompatible with each other as downstream input.

**What counts as an "internal field name."** The prompt gives the category but not the method for identifying members of it. An agent must decide: is `order_id` internal (it appears in the database) or external (the caller uses it)? Is `payment_status` internal (it's a database column name) or external (the API returns it)? Two agents will draw this line differently.

**What to do with a partially-good scenario.** The prompt handles two cases: no problems (proceed) and problems (rewrite). It does not address the common third case: a scenario where 4 of 5 steps are well-formed and 1 needs rewriting. Does the agent return the full scenario with one step corrected? Does it flag the problem and ask the human to decide? Does it rewrite the whole thing?

**When to apply the check.** The prompt is written for reviewing an existing scenario. If used in a generative context ("write a new scenario for X"), there is nothing to check at the start. The agent must decide whether to apply the check during drafting (after each step) or after a complete draft. The strategy changes the level of revision.

### What output format does this prompt imply but not specify?

It implies Gherkin will be produced (because it says "rewrite it") but does not specify:
- Whether to include a scenario title
- Whether to include comments explaining what changed
- Whether to produce one scenario or multiple (e.g., success and failure cases)
- Whether to use `Scenario:` or `Scenario Outline:` when the input has variadic data
- Whether the output is a snippet or a complete feature file section

### What would two different agents do differently?

**Agent 1** applies the check to the existing scenario, identifies 3 problems, writes a paragraph describing each, then produces a corrected Gherkin block. Output: 300 words + 8 lines of Gherkin.

**Agent 2** applies the check silently, rewrites the scenario without commentary, and returns only the corrected Gherkin. Output: 8 lines of Gherkin.

Both satisfied the prompt. The first output is useful for a newsletter; the second is useful for direct file editing. These are different tools that the prompt cannot distinguish between.

**Agent 3** — given the prompt in a generative context — writes a draft, applies the check internally, and returns only the final draft with no visibility into which problems were found and fixed. The output looks clean. Any problems that the agent missed are invisible.

### What happens if used in a different context than intended?

This prompt was designed for reviewing a scenario that already exists. Used for planning a new endpoint:

- The agent has no scenario to check, so it skips the check and generates a draft.
- The draft is not checked against the criteria before being returned.
- The quality varies with the agent's prior context — if it has seen good scenarios recently, the draft will be better. If not, it will carry the same problems the criteria are meant to catch.

Used in a session focused on something other than spec quality (e.g., fixing a failing test), the prompt may not be surfaced at all. It must be remembered and pasted by the human. If the human forgets, the judgment is not applied.

---

## Why this exists as a document

This file is the "before" artifact for Issue #9 of The Level 5 Engineer newsletter. It documents the state of the Gherkin quality check as it existed across Issues #2–#8 — embedded in CLAUDE.md prose, repeated session notes, and the spec-audit-framework document.

The "after" artifact is `docs/skills/gherkin-scenario-quality.md`. The demonstration of the difference between the two is in `findings/issue-09-skills-infrastructure.md`, Phase 4.
