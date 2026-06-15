# Issue #10 — The 3-Tier Skill Architecture

> Written in real time during the session.

---

## Phase 1 — Mapping the project to the 3-tier model

**Date:** 2026-06-15
**Status:** ✅ Complete

Everything in this project that functions as an instruction to an agent — CLAUDE.md sections, the Gherkin quality skill, the spec-audit framework, the step definition patterns, the findings protocol — was reviewed and classified.

---

### Item inventory

---

**Item:** Findings file writing protocol
**Current home:** CLAUDE.md (Documentation protocol section)
**Correct tier:** 1
**Why:** It applies uniformly to every session and every agent — it is not domain-specific to order management, Gherkin, or API testing. Any agent working on any newsletter issue must follow the same structure.
**Gap:** No routing signal description. No output contract specifying what constitutes a complete vs incomplete findings entry. No quality criteria. It reads as procedural prose, not a skill.

---

**Item:** Commit message conventions
**Current home:** CLAUDE.md (Commit conventions section)
**Correct tier:** 1
**Why:** Commit conventions are org-wide by definition — they govern how work is recorded in the shared history, not what work is done. Every agent, every session, every domain.
**Gap:** No routing signal. No edge cases (what if a commit spans multiple concerns?). Listed as examples, not as a contract.

---

**Item:** "What you can and cannot do" constraints
**Current home:** CLAUDE.md (permissions section)
**Correct tier:** 1
**Why:** These constraints apply to every agent in every session regardless of domain. They are the project's safety rails, not domain methodology.
**Gap:** No version. If a constraint changes (e.g., a new directory becomes editable), there is no signal that the constraint was updated — an agent with cached context would apply the old rule.

---

**Item:** Gherkin scenario quality evaluator
**Current home:** docs/skills/gherkin-scenario-quality.md
**Correct tier:** 2
**Why:** Encodes senior practitioner expertise specific to the order-api domain — the five-question diagnostic, the debt taxonomy, and the specific field name substitutions (`db_status` → `status`, `order_created_at` → `placed_at`) are artifacts of this codebase's specific history. A generic Gherkin skill would not know to look for these.
**Gap:** No tier marker. No reference to Tier 1 formatting constraints. Currently sitting in `docs/skills/` root rather than `docs/skills/tier2/`.

---

**Item:** Spec audit framework
**Current home:** docs/spec-audit-framework.md
**Correct tier:** 2
**Why:** The five-question methodology and six-class taxonomy encode the judgment accumulated across Issues #5, #7, and #8. It is domain-specific (Gherkin for API specs) and practitioner-level (requires understanding what "caller perspective" means in the context of HTTP contracts).
**Gap:** Exists as a reference document, not a skill. No routing signal. No output contract. An agent reading it has to extract the methodology from 1,500 words of prose. It is the upstream source material for the Gherkin quality skill — the relationship between them is not documented.

---

**Item:** Step definition writing pattern
**Current home:** Implicit — derivable from reading tests/steps/ across four files, but never written down
**Correct tier:** 2
**Why:** The pattern for how step definitions are written in this project (fixture injection via conftest, mock server log assertions, `time.sleep` placement for async assertions, `reset_all_logs` fixture usage) is domain methodology. It encodes architectural decisions about how this test harness works. A new agent dropped into this project would need to read four files to reconstruct it.
**Gap:** Does not exist as a skill at all. The entire pattern lives only in the existing code. If the code were refactored without preserving the pattern, it would be lost.

---

**Item:** "Why this matters" paragraph writing pattern
**Current home:** Implicit — appears in every findings file, consistent structure but never written down
**Correct tier:** 3
**Why:** This is a personal workflow pattern belonging to the newsletter author. The structure (practitioner voice, one paragraph, honest about failures, peer-to-peer tone) reflects editorial judgment that is specific to this author and this newsletter, not to all agents on all projects.
**Gap:** Does not exist as a skill. Lives only in the CLAUDE.md description ("one paragraph written as if explaining to a senior engineer") and in the examples in the existing findings files.

---

**Item:** External service mock server architecture
**Current home:** CLAUDE.md (External dependencies table) + conftest.py
**Correct tier:** 2
**Why:** The decision to use Python-native mock servers (mock_server.py) that are WireMock-compatible — rather than real WireMock, httpretty, or responses — is a domain architectural decision that affects every test written in this project.
**Gap:** The rationale for this choice is not documented anywhere. It exists as a fact (this is how it works) but not as a principle (this is why, and what to do when adding a new external service). An agent asked to add a third external service would have to reverse-engineer the pattern.

---

**Item:** Newsletter audience framing
**Current home:** CLAUDE.md (Newsletter context section)
**Correct tier:** 3
**Why:** The specific description of the author ("Senior Software Engineer, 10+ years, Level 2–3") and the intended audience ("curious but haven't yet made the leap") is the author's personal editorial context, not a standard that any other engineer would share.
**Gap:** Not a skill — it is a context declaration. That is correct for this item. It belongs in CLAUDE.md as metadata, not in a skill file. It does not need to be promoted or converted.

---

**Item:** Test run verification sequence
**Current home:** Implicit — appears as a closing step in every implementation session
**Correct tier:** 1
**Why:** "Run all 15 tests and confirm they pass before declaring work complete" is a universal project standard, not domain methodology. It does not require judgment — it requires compliance.
**Gap:** No skill file. Documented only in CLAUDE.md's "Running the test suite" section and session-by-session instructions. The verification sequence (Gherkin → Pact → can-i-deploy) has a specific order that matters but is not explained.

---

### Summary: which tier has the most gaps?

**Tier 2 has the most gaps.** The project has accumulated substantial domain methodology across nine issues, but most of it exists as:
- Reference documents (spec-audit-framework.md)
- Implicit code patterns (step definition architecture)
- Session-specific instructions that are re-written each time

The Gherkin quality skill from Issue #9 is the only Tier 2 item that has been properly converted. Everything else is either prose in CLAUDE.md or readable only from the code.

**The item most urgently needing conversion:** The step definition writing pattern. It is the most operationally critical — every test implementation session depends on it — and it is the most at risk of being wrong. A new agent adding a step definition without understanding the conftest fixture injection pattern, mock server log assertion strategy, and async timing approach will write a step that looks correct but behaves incorrectly under load.

**Items that don't fit any tier:** The newsletter audience framing in CLAUDE.md. It is not a skill (no routing signal, no output contract, no methodology) and should not be one. It is editorial context that shapes how the author writes but cannot be operationalized as agent instruction. This is correct: not everything in a CLAUDE.md is a candidate for skill conversion.

---

## Phase 2 — Building the Tier 1 skill

**Date:** 2026-06-15
**Status:** ✅ Complete

### What the Tier 1 skill controls that was previously implicit

Before this skill:
- **Findings file status indicators** were used inconsistently. Issue #8 introduced `🔄 In progress` mid-session; other issues used only `✅` and `❌`. No rule existed for which to use.
- **Code block language tags** were sometimes `bash`, sometimes `python`, sometimes absent. The spec-audit-framework used unlabeled blocks.
- **Commit message type prefixes** were documented as examples in CLAUDE.md but not as an exhaustive list. An agent could reasonably use `refactor:` or `style:` without violating the documented conventions.
- **The "Why this matters" paragraph placement** was specified in CLAUDE.md but the formatting around it (should it have a header? should it be the last section?) was not.

### One concrete example of output formatted differently without this skill

In `findings/issue-08-spec-audit.md`, the Phase 1 section opens with:

```markdown
## Phase 1 — Fixing the seven spec debt items

**Date:** 2026-06-07
**Status:** 🔄 In progress
```

And later each fix is documented using an ad-hoc structure: `**Original:**` / `**Rewritten:**` / `**What this closes:**` — headings that appear nowhere in the CLAUDE.md findings protocol. They were invented mid-session because the standard protocol (What I tried / What happened / Root cause / The fix / Why this matters) did not fit a sequence of seven incremental changes.

With the Tier 1 formatting skill in place, this would be handled explicitly: the skill defines when to use the standard five-section structure vs the sequence variant, and how to format the sequence variant consistently. A second agent producing a multi-fix session would produce a structurally compatible output.

### What "org-wide" means for a solo project

For a real team, Tier 1 exists because inconsistency has a coordination cost: a reviewer reading findings from five engineers needs all of them to use the same section headers, or they spend cognitive load on format rather than content.

For a solo project, the coordination problem is different but equivalent. The "org" is the author plus every agent instance that works on the project — and agents are stateless between sessions. An agent in Issue #14 has no memory of the formatting decisions made in Issue #8. Without a Tier 1 skill, every session re-invents the output format, and the findings archive becomes inconsistent over time — some issues with five sections, some with three, some with inline code and some with fenced blocks.

The Tier 1 skill solves a consistency problem across agent instances rather than across engineers. The coordination cost is the same: a reader (the newsletter author or a future agent) shouldn't have to adapt to per-session formatting conventions. "Org-wide" in this context means "applies to all agent instances regardless of session."

---

## Phase 3 — Why the Gherkin skill is Tier 2, not Tier 1 or Tier 3

**Date:** 2026-06-15
**Status:** ✅ Complete

### Why it is not Tier 1

Tier 1 skills apply universally — to every agent, every session, every domain, without modification. The Gherkin quality evaluator cannot be Tier 1 because it encodes project-specific conventions:

- The field name substitutions in Q4 (`db_status` → `status`, `order_created_at` → `placed_at`) are specific to this codebase's known debt history. Applying them to a different project would produce wrong output.
- The feature file ownership rules (which scenario belongs in which of the four feature files) are specific to this project's service architecture. Another project has different services.
- The "at most one request" vs "exactly one request" decision for the notification service scenario (documented in Issue #8's audit) is a judgment call specific to the notification service's fire-and-forget contract.

A Tier 1 Gherkin skill would need to strip all of these specifics out and become generic — at which point it encodes no domain expertise and provides no more value than the base prompt version from Issue #9.

### Why it is not Tier 3

Tier 3 skills are personal workflow patterns: individual shortcuts that encode one person's editorial taste or working style, not methodology that every agent on the project should apply consistently.

The Gherkin quality evaluator is not personal in this sense. The five-question diagnostic, the debt taxonomy, and the output contract are designed to produce compatible output regardless of which agent runs the skill. That compatibility is the whole point — it exists so that a scenario written in Issue #10 is structurally compatible with one written in Issue #14, even if different agent instances produce them.

If this skill were at Tier 3, it would be optional — something one engineer uses because they like it, not something enforced on every agent that touches a feature file. That would defeat its purpose.

### What makes it the "competitive moat"

A generic Gherkin skill tells an agent: "write Given/When/Then steps that are clear and testable." That instruction appears in every Cucumber tutorial. It produces scenarios that are better than nothing but carry the same debt patterns every project accumulates: vague quantities, undefined terms, mechanism claims without the mechanism.

What the Tier 2 skill encodes that a generic skill cannot:
1. **The specific debt history of this codebase.** The five patterns in Q2 (`"correct"`, relative time bounds, count ambiguity, mechanism claims, internal field names) were not derived from a checklist — they were derived from the specific failures in Issues #2–#8. They are calibrated to this project's failure modes.
2. **The caller's perspective principle.** Q4's "remove the implementation and read the step" test is not a standard Gherkin teaching. It requires understanding the difference between the API surface and the implementation — a distinction that is specific to contract-first API development.
3. **The output contract for downstream consumption.** A step definition author in this project needs `"exactly N"` not `"N times"`, needs `"the payment gateway"` not `"the external service"`, needs a concrete value not a reference. These requirements come from how the step definitions in `tests/steps/` are actually implemented, not from Gherkin best practices in the abstract.

This is what "competitive moat" means at the skill level: the expertise encoded is not transferable to a generic context. It is only valuable because it is specific.

---

## Phase 4 — Tier 3 skill: the "Why this matters" writing pattern

**Date:** 2026-06-15
**Status:** ✅ Complete

### Why this candidate was chosen

The "Why this matters" paragraph appears in every findings file, every session, as the last section of each finding. Reading across the nine issues, it has a consistent structure that was never written down:

1. Opens with the specific technical finding stated as a practitioner observation, not as a problem description
2. Connects the technical finding to a broader engineering principle in one sentence
3. Names the failure mode that would occur without this finding, in concrete terms
4. Closes with the implication for the reader's own practice

From Issue #5: "The bad spec was written from the implementation's perspective — it described what the code did. The good spec was written from the caller's perspective — it describes what the caller can rely on."

From Issue #8: "Spec debt can migrate from the feature file into the step definition. The audit framework catches both, but only if you apply Q4 to the step definitions as well as the feature text."

From Issue #9: "The prompt produces output that passes today's tests; the skill produces output that a different agent can implement tomorrow without making any decisions you didn't make."

All three follow the same shape: observation → principle → failure mode → implication. This pattern was never written down. It lives in the author's editorial instinct and in the examples in the existing findings files.

### The socialization decision

**Promotion criteria:** Would every agent working on this project benefit from this skill, or is it specific to one person's working style?

This is where it gets interesting. The pattern is not style — it is structure. An agent that knows "the Why this matters paragraph must: open with the specific finding, connect to a principle, name the failure mode, close with the reader's implication" would produce a paragraph that is compositionally compatible with the existing findings archive. An agent that does not know this produces a paragraph that is technically correct (it is still one paragraph, it is still addressed to a senior engineer) but structurally different — perhaps it opens with the principle rather than the finding, or it names the failure mode last rather than third.

**Verdict: promote to Tier 2.** The pattern is not personal editorial taste — it is an output contract for the most reused artifact in this project. The findings files are the raw material for the newsletter, and structural consistency across them is a project requirement, not a stylistic preference.

**What would need to change before promotion:**
- The skill currently describes the structure implicitly (through examples). A Tier 2 skill needs an explicit output contract with the four components named and ordered.
- The skill needs a routing signal description specific enough that an agent routes to it when writing a findings entry, not when writing any prose.
- The skill needs quality criteria: how does an agent evaluate whether its "Why this matters" paragraph satisfies the contract before submitting it?

**The organizational liability of leaving it at Tier 3:**
See the next section.

---

## The organizational liability of a Tier 3 skill that should be Tier 2

**Date:** 2026-06-15
**Status:** ✅ Complete

The "Why this matters" pattern was consistent across nine issues because the same person wrote all of them, carrying the pattern in their head. This is the most dangerous form of institutional knowledge: it looks like a standard because it produces consistent output, but the standard exists only as long as the person holding it does.

On a real team, this plays out like this: the senior engineer who built the system leaves. The engineer who joins next reads the existing findings files and reverse-engineers the pattern — correctly, if they're careful, incorrectly if they're not. The pattern has a 50% chance of surviving the transition. The newsletter archive has a 50% chance of remaining structurally consistent. And nobody in the organization has any way to tell which outcome they got, because there is no written standard to check against.

In this project, the equivalent failure mode is session-to-session drift. An agent in Issue #14 reading only CLAUDE.md (which says "one paragraph written as if explaining to a senior engineer") will produce a paragraph that satisfies the letter of the instruction but not the structure that makes the findings archive coherent. The paragraph will be addressed to a senior engineer. It will be one paragraph. It will not necessarily open with the finding before the principle, or name the failure mode before the implication. These are invisible inconsistencies — each paragraph passes the CLAUDE.md check, but the archive loses the parallel structure that makes it readable as a series rather than as isolated entries.

The organizational liability of a Tier 3 skill that should be Tier 2 is not that individuals stop using it. They keep using it. The liability is that when a new agent (or a new engineer) joins the work, there is no artifact to hand them. The pattern transfers as "read the existing examples and try to match the style" — which is how every new hire learns the unwritten rules of their first week, and why it takes months before they're producing output that fits.

---

## Phase 5 — The uncomfortable question

**Date:** 2026-06-15
**Status:** ✅ Complete

### Which personal prompts or patterns would make every agent better if they were documented?

Three patterns from this project's history that belong in a skill and don't exist as one:

**The step definition writing pattern.** Across all four step definition files in `tests/steps/`, there is a consistent architectural pattern: fixtures are injected from `conftest.py` rather than set up inline, mock server state is asserted via `payment_log_shared.calls` rather than via response body fields, async side effects (the notification service) use `time.sleep(0.3)` before assertion, and the `reset_all_logs` autouse fixture handles cleanup. An agent adding a new step definition without knowing this pattern will set up mock state inline, assert via response fields, and skip the sleep — all of which produce tests that pass individually but break when run concurrently or in sequence. This pattern has been the foundation of every test session since Issue #2. It has never been written down.

**The "when to change only the spec vs when to change the implementation" decision rule.** Issues #7 and #8 both required deciding: given a spec debt item, does fixing it require touching the feature file only, the step definition only, the implementation only, or some combination? The answer was re-derived each time. The pattern: UNDERSPECIFIED and AMBIGUOUS COUNT → feature file only. LEAKY ABSTRACTION in the feature file → feature file + step definition. LEAKY ABSTRACTION in the step definition only → step definition only. IMPLICIT FLOW → remove the step if unspecced, add a new feature file if in scope. This is a decision tree that appeared in Issue #8's fixes and was implicit throughout Issue #7. It has never been written down.

**The "what makes a finding article-worthy vs a technical note" filter.** Not every event in a session becomes a finding. The timeout ambiguity in Issue #8's Fix 1 became a full finding. The fact that `notification_id` was not a UUID in the WireMock stub became a single line. The decision rule is: an article-worthy finding must have a root cause that a reader would not have anticipated, a failure mode that would have occurred in a real system, and a fix that encodes a transferable principle. A technical note is a fix with no generalizable lesson. This filter is applied every session. It has never been written down.

Why haven't they been? Because writing them down felt like overhead at the moment they were useful. The step definition pattern was obvious in the session where it was established — it was the right call, and the agent moved on. The decision rule for spec fixes was derived from first principles in the moment it was needed. The article-worthiness filter runs as editorial instinct, not as a procedure. All three share the same problem: they are patterns that are invisible when they work and only visible as "what went wrong" when they don't.

### What would be wrong about promoting everything to Tier 1?

The Gherkin scenario quality evaluator would be the wrong call to promote.

Here is what Tier 1 looks like if the Gherkin skill is added to it: "When writing a Gherkin scenario, check that it is well-formed. Apply the five-question diagnostic. Use the debt taxonomy. Produce output satisfying the output contract."

That instruction would be routed to by every agent, in every context — including agents working on commit messages, finding files, or README updates. The routing signal ("evaluate and produce well-formed Gherkin scenarios") would fire whenever "scenario" or "Gherkin" appeared in context, even in cases where the agent should be doing something else (fixing a step definition, for instance).

But there is a deeper problem than routing. Tier 1 skills are enforced uniformly. Promoting the Gherkin skill to Tier 1 implies that every agent in every session must run the five-question diagnostic. In a session focused on Pact contract testing (Issue #4) or CI/CD pipeline setup (Issue #6), forcing the Gherkin quality check is noise, not signal. It adds overhead to sessions where no Gherkin is being written, and it dilutes the skill's routing signal — instead of being "this is the thing you use when working on feature files," it becomes "this is the thing you're supposed to do always," which means agents stop treating it as a deliberate routing decision and start treating it as a background constraint that can be satisfied minimally.

The Gherkin skill's value comes from being domain-specific. Promoting it to Tier 1 would generalize it until it no longer encodes the expertise that makes it useful. A Tier 1 version of this skill would say "write clear Given/When/Then steps" — which is every Gherkin tutorial, and encodes nothing that took nine issues to learn.

---

## Phase 6 — Full test suite

**Date:** 2026-06-15
**Status:** ✅ All 15 tests passing

```
.venv/bin/python3 -m pytest tests/steps/ tests/pact/ -v
→ 15 passed in 20.x seconds

python3 scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

The tier restructuring, skill creation, and CLAUDE.md update did not touch any implementation files. All tests pass at the same state as Issue #9.

---

## Closing: the architecture is not the point

The 3-tier model is a container for a harder decision: which of your working patterns are personal and which are organizational standards? The answer to that question determines who owns the risk when a pattern fails to transfer.

In this project, after ten issues, the most valuable institutional knowledge is not in the code. It is in the step definition architecture that has never been written down, the article-worthiness filter that runs as editorial instinct, and the spec-fix decision tree that was re-derived in Issue #8 and will be re-derived again in Issue #11. These are Tier 2 skills that exist at Tier 3 — which means they exist only as long as the sessions that carried them.

The organizational liability is not that these patterns get lost. It is that when they get lost, nobody in the organization knows they were there.
