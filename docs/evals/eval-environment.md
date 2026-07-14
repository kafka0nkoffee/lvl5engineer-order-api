---
type: Guardrail
title: "Eval: Environment"
description: "Pre-flight check intercepting modifications to shared production resources: ci.yml, CLAUDE.md, docs/skills/, and docs/ADR/."
tags: [eval, pre-flight, environment, infrastructure]
timestamp: 2026-06-16
---

# Eval: Environment

> This eval runs before any agent action that modifies infrastructure files:
> `ci.yml`, `CLAUDE.md`, any file in `docs/skills/`, any file in `docs/ADR/`,
> `requirements.txt`, `pytest.ini`, or any file in `.github/`.
>
> Answer all three questions before proceeding. A HALT instruction must not be
> overridden by task urgency, confidence in the change, or prior approval of
> similar changes. HALT means flag to the human author and wait.

---

## What this eval is for

Infrastructure files are shared production resources: their modification affects
the behavior of all agents in all sessions, not just the current one. A change to
`ci.yml` affects every future merge. A change to `CLAUDE.md` changes every
agent's standing orders from that point forward. A change to a skill file changes
the behavior of every agent that reads that skill in any future session.

This eval asks three questions that ordinary code review does not ask, because
they concern the cross-session and cross-contributor effects of the change —
effects that are invisible in a single-session context.

---

## Q1: Is the file being modified a shared production resource?

**Definition:** A shared production resource is any file whose modification
affects the behavior of all agents in all sessions, or any contributor's merge
gate — not just the current session or branch.

**In the order-api project, shared production resources include:**

| File / Path | Why it qualifies |
|---|---|
| `.github/workflows/ci.yml` | Controls the merge gate for all contributors |
| `CLAUDE.md` | Read by every agent at session start; changes standing orders |
| `docs/skills/tier1/` | Applies to all formatting decisions project-wide |
| `docs/skills/tier2/` | Applies to all domain-specific methodology |
| `docs/skills/tier3/` | Applies to all personal workflow decisions |
| `docs/ADR/` | Constrains all future agent actions on covered code paths |

**If YES:**

Require explicit confirmation of the specific change and its consequences before
proceeding. Write out, in plain text, what the file does now and what it will do
after the modification. If the change alters agent behavior, document the
behavioral delta explicitly.

**If NO:**

Proceed to Q2.

---

## Q2: Does the modification disable, weaken, or bypass any pipeline gate?

**Disabling:** Removing a job, step, or check from `ci.yml`.

**Weakening:** Adding `continue-on-error: true` to any job. Reducing a coverage
threshold. Removing assertions from a check script. Replacing a hard failure with
a warning.

**Bypassing:** Adding an `if:` condition that allows a job to be skipped on
certain branches. Excluding test files from a coverage check. Commenting out a
verification step. Adding a `--allow-failure` flag.

**In the order-api project, the four protected pipeline gates are:**

| Job | What it protects |
|---|---|
| `test` | All Gherkin scenarios pass |
| `pact-consumer` | Pact consumer contracts match implementation |
| `pact-verify` | Provider stubs satisfy all consumer contracts |
| `can-i-deploy` | All contracts verified before any deployment |

These are sequential gates. Weakening any one of them removes protection for
every change that passes through that gate from that point forward.

**If YES — HALT.**

Do not proceed without human review. State exactly which gate is being affected,
what the proposed modification does to that gate, and why the modification is
being proposed. The human author must explicitly approve. Do not proceed after
a self-assessment that the change is "low risk" — the gate exists because the
risk was not always apparent.

**If NO:**

Proceed to Q3.

---

## Q3: Will the modification change the behavior of any agent session that reads the modified file?

**Why this question is necessary:** Changes framed as "just updating documentation"
or "fixing a typo" in `CLAUDE.md` or a skill file may silently change the
instructions that every future agent receives. An agent that reads a modified
`CLAUDE.md` receives different standing orders than one that read the previous
version — even if the change appears cosmetic.

**How to answer:** Read the current file and the proposed change. Ask: "If a
fresh agent read the modified file at the start of a new session, would it take
any action differently than it would have before the change?" If the answer
requires reasoning through downstream effects, the answer is YES.

**If YES:**

Before making the modification, document the behavioral change explicitly in the
session's findings file. Name the specific behavior that will change, name the
sessions or scenarios where the change will be visible, and state whether the
change is intentional.

**If NO:**

Proceed with the modification.

---

## Failure mode addressed

This eval addresses **production blindness** — the failure mode where an agent
takes a high-blast-radius action without recognising that the blast radius extends
beyond the current session. An agent modifying `ci.yml` in a single session does
not automatically recognise that the change affects all future merges. An agent
modifying a skill file does not automatically recognise that it is changing the
standing orders for every future agent. This eval makes the cross-session scope
of infrastructure changes explicit before the change is made.

---

## Historical example: Issue #6 — ci.yml port conflict

**What happened:** During Issue #6, `ci.yml` was modified to add "Start mock
servers" steps in the `test` and `pact-verify` jobs. The intent was to ensure
the mock servers were running before pytest executed.

**Result:** The pytest session fixtures already start the mock servers on ports
8091 and 8092 as part of test setup. The CI steps started the same servers on
the same ports before the fixtures ran, causing `OSError: Address already in use`
in both jobs.

**Which eval question would have fired:** Q1 (ci.yml is a shared production
resource) and Q3 (the modification would change CI behavior — specifically, it
added a "start mock servers" step that ran before the pytest session fixtures).

**Would the eval have prevented the issue or only flagged it for review?**

Flagged for review. Q1 requires the agent to state the specific change and its
consequences before proceeding. If the agent had written out "I am adding a step
that starts mock servers on ports 8091 and 8092 before pytest runs," the
consequence — that pytest fixtures also start servers on those same ports — would
have been visible at review time. Whether the human reviewer would have caught it
depends on their familiarity with the pytest session fixture design.

The eval does not automatically prevent the issue. It forces the agent to make
the change visible and consequence-explicit before committing, which surfaces
the double-start problem to human review instead of to CI failure.

---

## Related

* [ADR-001: Inventory Before Payment](../ADR/ADR-001-inventory-before-payment.md) — decision this eval protects via shared-production-resource classification of docs/ADR/
* [ADR-002: Fire-and-Forget Notification](../ADR/ADR-002-fire-and-forget-notification.md) — decision this eval protects via shared-production-resource classification of docs/ADR/
* [Skill Review Checklist](../skill-review-checklist.md) — process for publishing skill changes that this eval intercepts
* CLAUDE.md Section 2 — environment discrimination section this eval operationalises
* CLAUDE.md Pre-flight evals table — routing entry that triggers this eval
