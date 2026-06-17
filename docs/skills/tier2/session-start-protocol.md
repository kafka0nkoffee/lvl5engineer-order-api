# Skill: Session Start Protocol

**Tier:** 2 — Domain methodology
**Version:** 1.0
**Last updated:** 2026-06-16 (Issue #13)
**Project:** lvl5engineer-order-api

---

## Description

Initialize a new issue session: create the findings file, update the index, and confirm scope before first tool call.

---

## When to use this skill

Use this skill when:
- You are beginning a new numbered issue session (Issue #N) for this project
- You have received session instructions and need to initialize the documentation before
  any other work begins

Do NOT use this skill when:
- The findings file for this session already exists — the session is already initialized
- You are continuing work within an ongoing session (findings file was created earlier)
- You are performing a task that is not associated with a numbered newsletter issue

---

## Methodology

### Step 1 — Extract scope from session instructions

Before creating any file, read the session instructions and identify:
- The issue number N (integer)
- The short topic (2–4 words, lowercase, hyphenated, no articles)

The issue number and topic must come from the session instructions, not from the most recent
git commit or the findings/README.md index. If the issue number is not stated in the session
instructions, return:

```text
# SKILL HALT: Issue number not found in session instructions.
# Identify the issue number before initializing the session.
```

Do not guess the issue number. Do not derive it by incrementing the most recent entry in
findings/README.md.

### Step 2 — Derive the filename

Apply the naming convention from the Tier 1 output-formatting-standard:

```text
findings/issue-{N}-{short-topic}.md
```

Zero-pad single-digit issue numbers (Issues 1–9): `issue-02-`, `issue-09-`.
Do not zero-pad Issue 10 and above: `issue-10-`, `issue-13-`.

The short topic uses hyphens, all lowercase, no articles ("the", "a", "an"). Maximum four
words.

**Correct:** `findings/issue-13-skill-audit.md`
**Incorrect:** `findings/issue-13-the-skill-audit.md`
**Incorrect:** `findings/issue13-skill-audit.md`

### Step 3 — Check for existing file

If `findings/issue-{N}-{short-topic}.md` already exists:

```text
# SKILL HALT: findings/issue-{N}-{short-topic}.md already exists.
# Session is already initialized. Do not create a duplicate.
```

Do not overwrite the existing file.

### Step 4 — Create the findings file

Create the file with exactly this opening block:

```markdown
# Issue #{N} — [Title in Title Case]

> Written in real time during the session.

---
```

The title is derived from the session instructions, in Title Case. The `> Written in real
time during the session.` line is literal — copy it exactly. Do not substitute alternate
phrasing.

Leave the rest of the file empty. Content is added during the session as work progresses.

### Step 5 — Update findings/README.md

Add a new row to the table in `findings/README.md`:

```markdown
| #{N} | [Short topic description] | [findings/issue-{N}-{topic}.md](findings/issue-{N}-{topic}.md) |
```

The short topic description is a phrase (not a sentence), title case, under 50 characters.
It describes the session's subject, not the finding. Append the row after the current last
row. Do not re-sort or reformat the existing rows.

### Step 6 — Stop

Do not update the root README.md at session start. The root README is updated at session end
when the work is complete and the findings are final. Updating it at the start would require
retroactive revision.

---

## Output contract

What this skill must produce:

- `findings/issue-{N}-{short-topic}.md` exists with the correct opening block (three
  elements: title line, quotation line, horizontal rule)
- `findings/README.md` contains a new row for this session
- No other files are modified

What this skill must NOT produce:

- Any modification to root README.md (session end, not start)
- Any modification to CLAUDE.md
- Any modification to existing findings files
- Any content in the findings file beyond the opening block

---

## Quality criteria

Before returning, verify:

1. **Filename convention**: Zero-padded for Issues 1–9, not for Issues 10+.
2. **Opening block**: Three elements present in order (title line, quotation line, `---`).
3. **README row**: New row appended, link is correct relative path, no existing rows modified.
4. **Scope confirmed**: Issue number and topic came from session instructions, not inferred.

---

## Edge cases and failure modes

**Issue number not in session instructions:** SKILL HALT — return explicit message.

**File already exists:** SKILL HALT — return explicit message, do not overwrite.

**Topic derived incorrectly (too long, contains articles, wrong case):** Apply naming
convention mechanically. If the session instructions give a topic that would exceed four
words, take the first four meaningful words. If they give a title, convert to lowercase
hyphenated form.

**findings/README.md is missing:** Create it with a standard header before adding the row.
This should not occur in a correctly initialized project — note the anomaly in the findings
file after creating it.

---

## Version history

| Version | Change | Issue |
|---------|--------|-------|
| 1.0 | Initial skill — formalizes the CLAUDE.md documentation protocol | #13 |

---

## Reference

This skill formalizes the "Documentation protocol — findings/" section of `CLAUDE.md`.

For findings file format details, see `docs/skills/tier1/output-formatting-standard.md`.
For the "Why this matters" paragraph structure, see
`docs/skills/tier3/why-this-matters-writing.md`.
