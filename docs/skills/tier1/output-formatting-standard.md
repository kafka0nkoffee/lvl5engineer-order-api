---
type: Methodology
title: "Skill: Output Formatting Standard"
description: "Applies consistent formatting to all agent output: findings files, Gherkin scenarios, commit messages, and code snippets in documentation."
tags: [tier-1, skill, formatting, output-standard]
timestamp: 2026-06-15
---

# Skill: Output Formatting Standard

**Tier:** 1 — Org-wide standard
**Version:** 1.0
**Last updated:** 2026-06-15 (Issue #10)
**Project:** lvl5engineer-order-api

---

## Description

Apply consistent formatting to all agent output in this project: findings files, Gherkin scenarios, commit messages, and code snippets in documentation.

---

## When to use this skill

Use this skill when:
- You are writing any section of a findings file (`findings/issue-{N}-*.md`)
- You are writing or reviewing Gherkin scenarios for formatting (not content — for content quality, use the Tier 2 Gherkin skill)
- You are composing a git commit message
- You are writing a code snippet for inclusion in a findings file or documentation

Do NOT use this skill when:
- You are evaluating whether a Gherkin scenario is well-formed — that is the Tier 2 skill (`docs/skills/tier2/gherkin-scenario-quality.md`)
- You are deciding what content belongs in a finding — this skill controls format, not substance
- You are writing `app/main.py` or test files — this skill applies to documentation artifacts only

---

## Findings file format

### File naming

```
findings/issue-{N}-{short-topic}.md
```

`{N}` is zero-padded to two digits for Issues 1–9 (e.g., `issue-02-`) and unpadded for Issue 10 onwards. `{short-topic}` uses hyphens, all lowercase, no articles ("the", "a", "an").

✅ `issue-10-three-tier-architecture.md`
❌ `issue-10-the-three-tier-architecture.md`
❌ `issue10-three-tier-architecture.md`

### Opening block

Every findings file opens with:

```markdown
# Issue #{N} — [Title in Title Case]

> Written in real time during the session.

---
```

The `> Written in real time during the session.` line is literal — copy it exactly. It is not a placeholder.

### Section headers

Use `##` for top-level sections (phases or named findings). Use `###` for subsections. Never use `####` or deeper in findings files.

**Standard section header format:**

```markdown
## [Short title of what was attempted]

**Date:** YYYY-MM-DD
**Status:** ✅ Worked | ❌ Failed | ⚠️ Partial | 🔄 In progress
```

`🔄 In progress` is used only when a section is being written incrementally over the course of a session. It must be updated to a terminal status (`✅`, `❌`, `⚠️`) before the session is committed.

### Five-section finding structure

Use this structure when documenting a discrete finding (an experiment, a fix, a decision):

```markdown
### What I tried

[What was attempted and why — active voice, past tense]

### What happened

[Exact output, error messages, unexpected behaviour — quote error text verbatim in a code block]

### Root cause

[Why it happened — be specific, not vague. "A race condition" is vague. "The notification thread was not joined before the assertion at line 47" is specific.]

### The fix

[What changed and why it worked — reference specific files and line numbers]

### Why this matters

[One paragraph — see Why this matters format below]
```

### Sequence variant

When documenting a sequence of related fixes (e.g., seven spec debt items applied in order), use the sequence variant instead of five separate five-section entries:

```markdown
### Fix N — [short description] (`filename.ext`)

**Original:**
```
[original text]
```

**Rewritten:**
```
[new text]
```

**What this closes:** [one sentence — what ambiguity or problem this removes]
```

Use this variant only when all items in the sequence share the same root cause category. Mixed-cause sequences should be broken into separate five-section entries.

### "Why this matters" paragraph format

This paragraph is the most important part of every finding. It is the raw material for the newsletter.

Structure (in order):
1. Open with the specific finding stated as a practitioner observation — not "we found that..." but the observation itself
2. Connect the finding to a transferable engineering principle in one sentence
3. Name the failure mode that would occur without this finding, in concrete terms
4. Close with the implication for the reader's own practice

**Length:** One paragraph, 4–6 sentences. Never a list. Never sub-paragraphs.

**Voice:** Peer-to-peer. Written as if explaining to a senior engineer who hasn't seen this codebase. Not tutorial voice, not documentation voice.

**What it must not contain:** References to "this codebase" or "this project" — generalise to "a project like this one." No jargon unexplained. No hedging ("might", "could potentially").

---

## Gherkin scenario formatting

### Indentation

Use 2-space indentation throughout. `Feature:` at column 0. `Scenario:` at 2 spaces. `Given`/`When`/`Then`/`And` at 4 spaces.

```gherkin
Feature: Order Creation

  Scenario: Order is successfully created when payment succeeds
    Given a registered user with id "user-123"
    And the inventory service confirms all items are in stock
    When the user submits an order for SHOE-RED-42
    Then the order status is "CONFIRMED"
```

### Line length

Maximum 100 characters per step. If a step exceeds 100 characters, split the data into a named value referenced from a Background or Examples table.

### Assumption comments

Assumptions embedded in a step (decisions not in the input) must appear as a comment on the line immediately following the step:

```gherkin
    Then the response HTTP status is 422
    # Assumption: 422 chosen over 409 — unprocessable entity fits better here. Verify with product.
```

Comments in `.feature` files are used only for assumptions. Do not use comments to explain what a step does — the step should be self-explanatory.

### Blank lines

One blank line between scenarios. No blank line between steps within a scenario. No trailing blank line at the end of a feature file.

---

## Commit message format

### Type prefixes (exhaustive list)

| Prefix | When to use |
|--------|-------------|
| `feat:` | New functionality visible to a user or caller |
| `fix:` | Correction to broken behaviour |
| `test:` | New or updated test without implementation change |
| `docs:` | Documentation only — findings, README, skills, CLAUDE.md |
| `chore:` | Maintenance — dependency updates, config changes, directory structure |
| `refactor:` | Implementation change with no functional or test change |

Do not use `style:`, `perf:`, `ci:`, or other prefixes not in this list without documenting the addition here.

### Format

```
{type}: {imperative present-tense description} — Issue #{N}

{optional body: why, not what. Reference specific files if relevant.}

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

The `— Issue #{N}` suffix is required on all commits in sessions that correspond to a newsletter issue. The body is optional but recommended when the commit changes more than two files.

### What must not appear in a commit message

- File lists ("updated README.md, findings/README.md, pytest.ini")
- Past tense in the subject line ("added", "fixed", "updated")
- Ambiguous subjects ("various updates", "misc fixes")

---

## Code snippet format in documentation

### Language tags

All fenced code blocks in findings files and documentation must have a language tag:

```markdown
```bash
# shell commands
```

```python
# Python code
```

```gherkin
# Gherkin scenarios
```

```diff
# diffs
```

```markdown
# markdown (for embedded examples)
```
```

Use `text` for output that is not a specific language (e.g., test runner output, error messages).

### Line length in snippets

80 characters maximum in code snippets within documentation. Long commands use `\` continuation. Long output can be truncated with `[...]` on its own line.

### What not to comment in snippets

Do not add inline comments explaining what a line does if the line is self-explanatory. Comments in documentation snippets should only appear when demonstrating a specific point referenced in the surrounding prose.

---

## Quality criteria

Before submitting any documentation output, check:

1. **Section header completeness**: Every `##` section has a Date and Status line. No section is left without a terminal status at commit time.
2. **Language tags**: Every fenced code block has a language tag.
3. **Commit message**: Subject line uses an approved prefix, is imperative, and includes the issue number suffix.
4. **"Why this matters" structure**: Verify all four components are present (observation, principle, failure mode, implication). If any is missing, the paragraph is incomplete.
5. **Gherkin indentation**: 2-space throughout. No tabs.

---

## Edge cases

**A finding has no root cause (it worked first try):** Omit the `### Root cause` section. Compress to three sections: What I tried / What happened / Why this matters.

**A session spans multiple phases with no discrete failures:** Use phase headers (`## Phase N — [title]`) at the `##` level with Date/Status, and document methodology inline rather than in five-section entries.

**A commit spans more than one concern:** This is the signal to split the commit, not to use a compound type prefix. One commit, one concern.

**A code snippet is longer than 40 lines:** Do not embed it in the findings file. Reference the file path and line range instead: "See `tests/steps/test_order_creation.py:47–89`."
