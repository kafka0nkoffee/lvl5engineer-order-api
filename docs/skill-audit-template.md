# Prompt Library Audit Template

**Version:** 1.0
**Last updated:** 2026-06-16

A reusable template for auditing the accumulated prompt material in any AI-assisted project.
This document is standalone — it does not require reading any other document to use. It
defines what to look for, how to classify what you find, and how to decide what to do with it.

---

## Section 1 — What counts as a prompt library item

A prompt library item is anything that instructs an agent how to behave — whether it is
formally written down, embedded in a configuration file, or silently followed as convention.

Search these five sources:

### Source 1 — Pasted prompts

Prompts that exist as saved text in notes apps, clipboard managers, pinned messages,
Notion documents, or README files. Characteristics:
- You paste them into a session before asking the agent to do something
- You have to remember to paste them
- They are not automatically applied to any session
- They exist in multiple versions (you might have two versions of "my code review prompt"
  in different places)

### Source 2 — System prompts and agent config files

Standing instructions that apply to every session automatically. Examples: CLAUDE.md files,
system prompt files, assistant personas defined in API calls, agent configuration files.
Characteristics:
- Applied once; affect all subsequent interactions in a project
- Not pasted — they are part of the project setup
- May contain both instructions and context (mix of actionable and informational content)

### Source 3 — Reusable instructions embedded in larger documents

Instructions buried inside README files, onboarding documents, wikis, or specification
documents. Characteristics:
- The document has a primary purpose (documentation, specification) but contains sections
  that are intended to guide agent behavior
- An agent reading the full document would encounter the instruction
- An agent that doesn't read the full document misses it

### Source 4 — Implicit conventions in existing outputs

Patterns that are never written down but are consistently followed in existing files.
Characteristics:
- You can derive the pattern from reading three or more existing outputs
- A new agent that hasn't read the existing outputs would not follow the pattern
- The pattern is consistent enough that its violation would look obviously wrong
- It has never been stated as a rule

Examples: comment style in test files, naming conventions in modules, response format
conventions in API handlers, section structure in documentation.

### Source 5 — Existing skill files

Properly structured agent skill files, if any exist in the project. Characteristics:
- Has a routing signal (description line that agents use to select the skill)
- Has a "when to use / when not to use" section
- Has an explicit output contract
- Is version-controlled

These are already prompt library items in the correct form. Include them in the inventory
so the full picture is visible.

---

## Section 2 — Classification taxonomy

For each item found, assign one of four types.

### PROMPT

A manually-created instruction that an agent acts on, but has no formal structure (no routing
signal, no output contract, no version).

**Identify by:** It is text you would paste or quote to an agent. Removing it would cause
the agent to fall back on default behavior or make a decision you don't want. It is not
self-describing — an agent cannot infer from its content when to apply it.

### PATTERN

An implicit convention derivable from existing outputs but never stated as a rule. Not
pasted into sessions; not documented. Followed by agents that have read the existing outputs
and missed by agents that haven't.

**Identify by:** You can describe the rule in one sentence, but it doesn't exist as written
text anywhere in the project. Multiple existing files follow it. A new file that violates it
would look inconsistent with the others.

### SKILL

A structured instruction with a routing signal, explicit methodology, output contract, and
version. An agent can be directed to it without pasting its content into the session.

**Identify by:** It has a description line (for routing), a methodology section (what to do
and why), and an output contract (what must be produced). It is version-controlled with a
version history.

### CONTEXT

Project metadata, audience description, or background information that an agent reads for
orientation but that does not produce actionable output. Context is not a prompt; it shapes
how other prompts are interpreted.

**Identify by:** Removing it would not change what the agent produces — it would change how
the agent calibrates tone, scope, or depth. It does not tell the agent what to do; it tells
the agent what the situation is.

### Decision tree

```
Is this something an agent acts on?
├── No → CONTEXT
└── Yes → Does it produce a specific artifact with a defined format?
          ├── Yes → Does it have a routing signal + output contract + version?
          │         ├── Yes → SKILL
          │         └── No  → SKILL CANDIDATE (use conversion decision criteria below)
          └── No  → Is it explicitly written down?
                    ├── Yes → PROMPT
                    └── No  → PATTERN
```

---

## Section 3 — Conversion decision criteria

For each item that is not already a SKILL, apply these five questions to determine the
conversion decision.

### Q1: Is this used in more than one session?

If no: **KEEP AS-IS.** Items used only once are historical records, not reusable
infrastructure. Document them as CONTEXT.

If yes: proceed to Q2.

### Q2: Would two agents interpret it differently?

Apply a thought experiment: give this item to two agents with different prior context. Would
they produce the same output? If no: **CONVERT TO SKILL.** Agent divergence is the primary
failure mode of undocumented prompts and patterns.

If yes (two agents would converge without a formal skill): the item may be self-describing
enough to keep as a PROMPT. Proceed to Q3 to verify.

### Q3: Does its output flow into another agent's input?

If yes: **CONVERT TO SKILL.** Any item whose output is consumed by a downstream agent
requires an output contract. Without a contract, the upstream agent produces output in
whatever format makes sense to it; the downstream agent cannot rely on that format.

A skill with an output contract is the only reliable interface between agents.

### Q4: Is it superseded by something else?

If a SKILL now covers the same ground as this PROMPT or PATTERN: **DEPRECATE.**

The risk of leaving superseded items in place: an agent may find both versions and use the
older, less correct one. Superseded items are active liabilities, not harmless artifacts.

### Q5: Does it express the same thing as another item?

If two items give the same instruction in different words: **MERGE.** Keep the more precise
version; deprecate the less precise one.

"More precise" means: fewer judgment calls left open, more specific output format, more
explicit about what NOT to do.

---

## Section 4 — Conversion checklist

Before committing a new skill, answer these five questions. A skill that fails any question
should not be published in its current form.

### 1. Is the routing signal under 120 characters and specific?

Count the characters in the description line. Descriptions over 120 characters may be
truncated or deprioritized by agent routing frameworks.

Verify specificity: does the description distinguish this skill from other skills that
produce similar output? "Write step definitions" is not specific. "Write pytest-bdd step
definitions for [project] using the fixture-chaining pattern" is specific.

### 2. Could two agents produce different outputs that both satisfy the output contract?

List the requirements in the output contract. For each one, ask: is there a second valid
output that satisfies this requirement but differs structurally from the first?

If yes: the requirement is under-specified. Either add detail to the requirement or add an
example of the expected output. Common under-specifications: "a clear title" (clear by
whose standard?), "appropriate fields" (which fields?), "one or more scenarios" (how many
is enough?).

### 3. Does the methodology describe reasoning or procedure?

Read each section of the methodology. For each one, ask: if an agent encounters an input not
covered by the examples, can it apply the methodology to produce correct output?

Procedure answers "what to do." Reasoning answers "why this, not that." A methodology that
only describes procedure fails for inputs outside the examples. A methodology that includes
reasoning generalizes.

### 4. Is the skill idempotent on already-correct input?

Apply the skill mentally to an input that already satisfies the output contract. Does the
skill return it unchanged? If not — if the skill would rewrite a correct input — the skill
will cause unnecessary churn in any agent pipeline that loops.

The test: feed the skill's output back as its input. Does it return the same output?

### 5. Does the skill fail explicitly for out-of-scope inputs?

Identify one input that is clearly outside the skill's domain. Does the skill have an
explicit termination condition for this input? Explicit means: the skill returns a named
error message and produces no artifact.

The worst failure mode is PLAUSIBLE WRONG: the skill processes an out-of-scope input and
produces output that looks correct but isn't. Explicit failure is always better.

---

## Section 5 — Audit scorecard

Fill in this template after completing the inventory.

```
PROMPT LIBRARY AUDIT SCORECARD

Project: _______________
Date: _______________
Auditor: _______________

--- INVENTORY ---

Total items inventoried: ___

Type breakdown:
  PROMPT:    ___
  PATTERN:   ___
  SKILL:     ___
  CONTEXT:   ___

Tier breakdown (for SKILL items):
  Tier 1 (org-wide standard):    ___
  Tier 2 (domain methodology):   ___
  Tier 3 (personal workflow):    ___
  UNCLASSIFIED:                  ___

--- CONVERSION DECISIONS ---

  KEEP AS-IS:       ___
  CONVERT TO SKILL: ___ (HIGH priority: ___ / MEDIUM: ___ / LOW: ___)
  PROMOTE:          ___
  DEPRECATE:        ___
  MERGE:            ___
  DEFERRED:         ___

--- RISK ASSESSMENT ---

Most dangerous unconverted item: _______________
Why: _______________

Most surprising finding: _______________
Why: _______________

--- COMPLETION ---

Estimated sessions to convert HIGH priority items: ___
Items deprecated this session: ___
Items merged this session: ___
Items converted to skills this session: ___
```

---

## Section 6 — The junk drawer test

Every prompt library accumulates items that were once useful, are now superseded, but nobody
has officially removed. Apply these four questions to find them.

### Junk drawer question 1

**Is there a newer version of this item?**

If yes, and you are not using the older version: **deprecate it immediately.**

The risk of leaving it: an agent may find both versions and use the older one. In most cases
the newer version exists because the older one had failure modes. The agent that uses the
older version will exhibit those failure modes.

Mark deprecated items visibly (a header comment or metadata flag). Do not silently remove
them — the newsletter article or findings file may reference them by name.

### Junk drawer question 2

**Do two items say the same thing differently?**

If yes: keep the more precise one; deprecate the less precise one.

"More precise" means fewer decisions left to the agent. Compare the two items by listing
every decision an agent must make when following each one. The item that leaves fewer
decisions open is more precise.

Merge the key content of the deprecated item into the kept item before deprecating, in case
the deprecated item contained detail that the kept item lacks.

### Junk drawer question 3

**Was this written for a specific session and never generalised?**

A session-specific instruction written once and never reused is not a prompt library item —
it is a session note. If you cannot describe when you would use it in a future session,
deprecate it.

### Junk drawer question 4

**Would an agent following this instruction today produce output inconsistent with your
current standards?**

This is the most important junk drawer question. An item that was correct six months ago
may now conflict with current skills, output contracts, or project decisions. An agent that
finds and uses this item will produce output that looks plausible but violates current
standards.

This is an active liability. Deprecate it immediately, before the next session.
