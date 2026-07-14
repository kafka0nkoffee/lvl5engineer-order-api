# The J-Curve Conditions Framework

> When does infrastructure-first AI-assisted development pay off?  
> A decision framework derived from 19 sessions of documented work.

---

## What this document is

This is the practical takeaway from the Level 5 Engineer newsletter's 20-issue build. It
is not a theory. It is a set of conditions, derived from a time audit of actual session
data, that predict whether a specific level of infrastructure investment will return its
cost in a real project.

The J-curve: when you invest in agent-facing infrastructure (skills, ADRs, evals,
constraints), session output drops to near zero while the infrastructure is being built,
then recovers at a higher and safer level. The question every engineer faces before
starting this investment is: will my project live long enough to see the recovery?

---

## The four infrastructure layers, costs, and payoff conditions

---

### Layer 0: Minimal (CLAUDE.md + test suite)

**What it includes:**
- CLAUDE.md with project description, directory layout, what the agent may/may not touch
- Gherkin or equivalent behavioral tests
- A test runner command that the agent can run and interpret

**Build cost:** 1–2 sessions.

**What it prevents:** Agent confusion about project structure; behavioral regressions.

**What it does NOT prevent:** Invariant violations that pass tests; contract drift;
infrastructure weakening; fire-and-forget converted to synchronous.

**When to use this level:**
- Project runs fewer than 5 implementation sessions with agent assistance
- The project has no external service dependencies with formal contracts
- No architectural invariants that tests cannot express (rare, but exists for pure
  calculation logic or UI projects)
- A production incident costs less than 5 days of developer time to recover from

**Warning sign that you've outgrown this layer:** You discover a change that passes all
tests and is wrong in a way you cannot easily explain.

---

### Layer 1: Foundation (Layer 0 + skills + CI pipeline)

**What it adds over Layer 0:**
- One or two domain-specific skills (output contracts for your most-repeated agent tasks)
- A CI pipeline with at minimum: test suite + contract verification (Pact or equivalent)
- A session-start protocol that creates a findings file at the start of each session

**Build cost:** 3–5 sessions after Layer 0.

**What it prevents, in addition to Layer 0:** Spec debt from accumulating silently; contract
drift between services; session context lost between agent instances.

**Payoff condition:** Your project has at least 8–10 implementation sessions after the
skills are built. One session of skill investment saves approximately 30–60 minutes per
downstream session. A Tier 2 Gherkin skill that takes 2 sessions to build breaks even
after 3–6 downstream implementation sessions.

**When to use this level:**
- Project runs 8+ implementation sessions
- You have multiple Gherkin feature files or multiple external service dependencies
- You've experienced at least one "the agent did something plausible but wrong" incident
- Your team has more than one person (including multiple agent instances) working on specs

---

### Layer 2: Constraints (Layer 1 + ADRs + evals)

**What it adds over Layer 1:**
- Architecture Decision Records for your top 3–5 load-bearing design decisions, each with:
  a dangerous-improvements list and agent check questions
- Pre-flight evals for your highest-risk modification categories:
  shared infrastructure, implementation of core flows, contract/stub changes
- A decision index in CLAUDE.md pointing at ADRs before the agent touches covered code

**Build cost:** 4–6 sessions after Layer 1.

**What it prevents, in addition to Layer 1:** Architectural invariant violations that pass
all tests; dangerous "improvements" that look correct; undocumented decisions being silently
reversed.

**The specific failure mode this layer prevents that no test can:** A change that makes the
system more reliable by one definition while making it catastrophically less reliable by
another. The canonical example from this project: making the notification call synchronous
passes all 20 tests and causes a complete order processing outage on the first notification
service incident.

**Payoff condition:**
- You have at least one architectural invariant with no behavioral test (the
  notification-asynchronous property in this project)
- OR your project has external service dependencies with response-field-level contracts
- OR you have made at least one dangerous improvement in the past (an agent change that
  passed tests and caused a production incident)

**When to use this layer:** The question is not "how long will this project run" — it is
"what is the cost of the specific failure modes this layer prevents?" One production
incident caused by a violated invariant typically costs more time to recover from than
the entire Layer 2 build. If your invariants are real and your project is in production,
this layer pays for itself the first time it prevents an incident.

---

### Layer 3: Full infrastructure (Layer 2 + runbooks + skill review process)

**What it adds over Layer 2:**
- Agent-facing runbooks for your top 2–3 operational failure scenarios, each with:
  explicit decision trees, named commands, specific verification steps, named halt conditions
- A skill review process (five-dimension checklist) before publishing any new skill version
- An operational dry-run process that executes runbook commands against the real system
  before the runbook is needed

**Build cost:** 3–4 sessions after Layer 2.

**What it prevents, in addition to Layer 2:** Agent inference errors during degraded-state
operations; plausible-but-wrong actions taken during incidents; runbooks that reference
commands that have never been validated.

**Payoff condition:**
- You expect agents to operate during incidents (not just development), OR
- Your project has more than 3 people writing skills or runbooks (review process prevents
  publishing PLAUSIBLE WRONG skill output that is invisible to the publisher)

**When to use this layer:** For most engineering projects, this layer is optional. Its
value is concentrated in two scenarios: (1) you have agents in operational roles, not just
development roles; (2) your team is large enough that skill review becomes a quality gate
rather than overhead.

---

## The break-even calculator

Total infrastructure investment = sessions × average session length (in hours)

Session efficiency gain from infrastructure = minutes saved per implementation session
from not re-deriving conventions, spec patterns, and constraint checks.

Break-even in implementation sessions = investment / efficiency gain per session

| Layer | Build investment | Efficiency gain/session | Break-even implementation sessions |
|-------|-----------------|------------------------|-------------------------------------|
| Layer 1 | ~8–12 hr | ~60 min/session | 8–12 sessions |
| Layer 2 | +12–18 hr | ~30 min/session | +24–36 sessions |
| Layer 3 | +8–12 hr | ~15 min/session | +32–48 sessions |

**What this table does not capture:** Risk reduction value. The break-even calculation
only measures session efficiency. A single prevented production incident is typically worth
5–30× the infrastructure investment.

---

## The three questions to ask before starting

**Question 1: How many implementation sessions will this project have?**

Fewer than 5: Use Layer 0. The infrastructure investment will not break even.

5–15: Use Layer 1. Build skills for your most-repeated agent task (spec writing, code
review, step definition writing) and a minimal CI pipeline.

15–50: Use Layers 1 and 2. Add ADRs for your three most load-bearing architectural
decisions and evals for your highest-risk modification categories.

50+: Build the full stack. The infrastructure is a fraction of total session cost.

---

**Question 2: Does your project have architectural invariants with no behavioral test?**

If yes: build Layer 2 regardless of project length. The evals are the only protection
for these invariants. The notification-asynchronous property, the inventory-before-payment
ordering, the payment idempotency window — none of these can be expressed as a behavioral
test that passes when the invariant holds and fails when it doesn't, because the test
would have to assert "this call was not made" or "this call was asynchronous" — properties
that tests cannot observe for implementation structure, only for output.

If no: Layer 1 may be sufficient if your invariants are all captured by your test suite.

---

**Question 3: What is the cost of one production incident caused by an agent acting on
incomplete context?**

If high (financial, reputational, or operational cost of > 1 week to recover): build Layer
2 before you need it. ADRs and evals prevent the specific class of incident where an agent
makes a plausible improvement that violates a constraint nobody wrote down.

If low (experimental project, internal tool, sandbox): Layer 0 is sufficient until your
first incident. Build Layer 2 after you understand what you're protecting against.

---

## The J-curve investment profile

When you choose to build infrastructure, your session output curve looks like this:

```
Output
density
  │
  │   ██
  │  ████           ████
  │ ██████         ██████
  │████████       █████████
  ├────────────────────────── Sessions
     Foundation   Trough    Recovery
     (Layers 0-1) (Layer 2)  (Assembly)
```

The trough is real. Ten consecutive sessions with zero new features is not a sign that
something went wrong — it is the cost of investing in constraints before the code that
needs constraining exists. The recovery is also real: Issue #19 (the first
full-infrastructure implementation session in this project) produced 5 scenarios with zero
post-implementation rework, no dangerous improvements, and no spec debt. That is not the
baseline for all future sessions — but it demonstrates what the infrastructure makes
possible.

The decision is not "should I do this?" It is "does my project live long enough to see
the recovery, and do my failure modes justify paying for protection?"

---

## What the infrastructure does not solve

**Specification ambiguity.** If the product requirement is underspecified, the most
sophisticated skill architecture will produce underspecified scenarios. The Gherkin quality
skill catches the language patterns of underspecification ("appropriate," "correct,"
"reasonable") — but it cannot supply product decisions that haven't been made.

**Context window limits.** A session that runs long enough will begin losing context. ADRs
help by making decisions queryable rather than requiring context to hold them, but they do
not eliminate the problem. Very long sessions still accumulate context debt.

**The first session on a new codebase.** No amount of infrastructure in CLAUDE.md
compensates for an agent's inability to physically read and understand a very large
codebase. Infrastructure helps agents make safe decisions about what they read; it does not
help agents read things they cannot reach.

**Agent hallucination about infrastructure that doesn't exist.** An agent that cites an
ADR that doesn't exist is not protected by the ADRs that do exist. The decision index in
CLAUDE.md helps — it tells the agent which ADRs exist and which code paths they cover —
but it cannot prevent an agent from inventing a reference.

---

## The one-sentence summary

Build infrastructure to the level that matches the cost of the failure modes you are
preventing — not to the level that matches your confidence in the agent.
