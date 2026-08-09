---
title: "The Most Popular Claude Code Framework I Didn't Know Existed"
subtitle: "A Level 5 Engineer — Special Edition"
issue_number: null
seo_title: "Superpowers for Claude Code: What 262k Stars Tells You About Agentic Development"
seo_description: "Jesse Vincent built the most starred Claude Code framework before most of us figured out we needed one. Here's what it does, what it doesn't, and where it fits with what this series has been building."
tags: [ai, softwareengineering, claudecode, superpowers, aiagents]
canonical_url: ""
---

A friend sent me a link after Issue #13 went out.

"Good news and bad news," he wrote. "Good news: there's a really great system for a lot of the stuff you've put together in your L5 blog. Bad news: it may just change the entire calculus on your setup again."

The link: `github.com/obra/superpowers`.

262,000 stars. 23,000 forks. Built by Jesse Vincent — creator of Request Tracker, former Perl 5 pumpking, someone who has been thinking seriously about software process for decades. The most starred Claude Code plugin in existence.

My first reaction, again, was recognition. My second reaction was genuine curiosity about what someone with Jesse's background built and whether it addressed the same failure modes I've been chasing.

Here's what I found.

---

## What Superpowers actually is

Superpowers is a complete software development methodology for coding agents, built on composable skills that auto-trigger based on what you're doing. You don't invoke them by name. As soon as Claude Code sees you building something, the relevant skill activates.

The core workflow:

1. **brainstorming** — activates before any code is written. Refines rough ideas through questions, explores alternatives, presents design in chunks short enough to actually read.
2. **using-git-worktrees** — activates after design approval. Creates an isolated workspace on a new branch, runs project setup, verifies a clean test baseline.
3. **writing-plans** — breaks the approved design into tasks sized for 2–5 minutes each, with exact file paths, complete code, and verification steps.
4. **subagent-driven-development** — dispatches fresh subagents per task with two-stage review (spec compliance, then code quality). Runs autonomously for hours without deviation.
5. **test-driven-development** — enforces RED-GREEN-REFACTOR: write a failing test, watch it fail, write minimal code, watch it pass, commit. Deletes code written before tests.
6. **requesting-code-review** — reviews against the plan between tasks, reports issues by severity, blocks progress on critical issues.
7. **finishing-a-development-branch** — verifies tests, presents options (merge/PR/keep/discard), cleans up the worktree.

The philosophy behind it: systematic over ad-hoc. Evidence over claims. Complexity reduction as a primary goal. Test-driven development always.

---

## What's immediately familiar

Reading through the Superpowers skills, four things stood out as independent convergence on the same conclusions this series reached.

**Brainstorming before building.** Superpowers' brainstorming skill asks questions before any code is written. This series' approach is writing Gherkin scenarios before any code is written. Different tools, same discipline: don't let the agent make product decisions silently.

**Plans before implementation.** Superpowers' writing-plans skill produces implementation plans with verification steps before any implementation begins. This series' approach is writing behavioral contracts (Gherkin) before implementation begins. The forcing function is the same: make decisions explicit before they become implicit choices in code.

**TDD as non-negotiable.** Superpowers enforces RED-GREEN-REFACTOR. This series enforces external behavioral scenarios that the agent cannot modify. Both start with the test, not the implementation.

**Subagent review.** Superpowers' two-stage review (spec compliance, then code quality) between tasks is structurally similar to the skill review checklist built in the series: first check the output contract, then check the quality criteria. Review as a gate before proceeding.

Jesse Vincent and I, working from completely different starting points, reached the same conclusion about what makes agentic coding reliable: enforce the discipline that experienced developers spent decades learning. Don't trust the agent to apply it spontaneously.

---

## What Superpowers doesn't cover

Three things that this series has spent significant effort on that are absent from Superpowers.

**Contract testing between services.** Superpowers is a workflow framework — it governs how a single agent builds within a single project. It has no concept of Pact contracts, WireMock stubs, or the drift between a mock and the real service it simulates. The confidence trap from Issue #4 — "WireMock says green, production is broken" — is not something Superpowers addresses.

**The stewardship layer.** Superpowers has no equivalent of ADRs, evals, or runbooks. When Jesse Vincent's agent makes the "concurrent inventory and payment" optimization that looks reasonable and violates a load-bearing invariant, Superpowers catches it only if the test suite was already written to catch it. The ADR's agent check question — "does my change ensure inventory confirmation completes before any payment call is initiated?" — intercepts the decision before any test is written or any code is run.

**Context persistence across sessions.** One fork of Superpowers — "claude-code-on-steroids" — explicitly notes this gap: "obra/superpowers gives you 14 structured workflows. It gives you zero memory, zero context management, and zero cost routing. Every session restart costs 5,000–15,000 tokens to re-establish context." The production-grade CLAUDE.md, ADRs, and evals built in this series are precisely the context management layer Superpowers doesn't provide.

---

## What this series doesn't cover (that Superpowers does)

Equally important: what Superpowers has that this series hasn't addressed.

**Auto-triggering skills.** Every skill in this series requires either a session instruction or explicit invocation. Superpowers' skills activate automatically. The agent sees "building something" and the brainstorming skill fires. The agent sees "task complete" and the code review skill fires. No human has to remember to invoke it. This is a real gap in the series' approach — and it's the gap the token economics angle your reader suggested is related to.

**Subagent-driven development.** Superpowers dispatches fresh subagents per task with two-stage review. This series has been working with a single long-running Claude Code session per issue. Fresh subagents per task means each task starts with a clean context — no accumulated token burn, no drift from session history. This is architecturally significant and something this series has not explored.

**The full git workflow.** Using-git-worktrees, finishing-a-development-branch — Superpowers manages the complete branch lifecycle. This series' Claude Code sessions have been committing directly to main without branch isolation per task. That's a process gap.

**262,000 people can't be wrong.** The skills have been battle-tested against more codebases, languages, and edge cases than any single project could produce. The TDD skill includes an anti-patterns reference. The systematic-debugging skill includes a root-cause-tracing technique. These aren't theoretical — they're refined through real usage at scale.

---

## The actual relationship

Superpowers and the three-layer infrastructure built in this series are not competing approaches. They're solving adjacent problems at different layers of the same stack.

Superpowers: **how the agent works** — the workflow, the process discipline, the task structure, the review gates.

This series: **what the agent knows** — the behavioral contracts, the documented decisions, the invariants, the context that persists across sessions.

A project with Superpowers and no stewardship layer has good workflow discipline but no protection against an agent that re-derives the inventory-before-payment decision incorrectly in session 14.

A project with stewardship infrastructure and no Superpowers has good context persistence but no enforcement of TDD, no brainstorming gate before coding, no subagent isolation per task.

The ideal stack — which nobody has yet written a comprehensive guide to — is both.

The next spin-off article runs the experiment: install Superpowers on the order-api project, run a session with it active, compare to a session with only the three-layer infrastructure, and compare to a session with both. The data will be in the findings.

---

**Sources & Further Reading**

- [Superpowers — github.com/obra/superpowers](https://github.com/obra/superpowers)
- [Jesse Vincent's original release announcement](https://blog.fsck.com/2025/10/09/superpowers/)
- [Prime Radiant](https://primeradiant.com)
- [The Level 5 Engineer — start here with Issue #1](https://level5engineer.substack.com/p/the-level-5-engineer-the-map-i-didnt)
- [Project repository](https://github.com/kafka0nkoffee/lvl5engineer-order-api)
