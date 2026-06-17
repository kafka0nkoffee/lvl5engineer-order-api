# Issue #13 — Skill Audit: The Layer 2 Stocktake

> Written in real time during the session.

---

## Phase 1 — Full Prompt Library Inventory

**Date:** 2026-06-16
**Status:** ✅ Complete

Sources searched:
- CLAUDE.md — all actionable instruction sections
- docs/skills/ — all three tiers, all versions
- docs/prompts/ — the pre-skill prompt from Issue #9
- docs/ (non-skill reference documents)
- tests/steps/ — four step definition files (implicit patterns)
- findings/ — session instruction patterns across Issues #2–#12

### Inventory

---

**Item 1: Session start and documentation protocol**

```
Source:      CLAUDE.md §"Documentation protocol — findings/"
Type:        PATTERN
Current tier: UNCLASSIFIED
Decision:    CONVERT TO SKILL
Reason:      Every session requires this sequence; no skill, no routing signal,
             no output contract — an agent follows CLAUDE.md prose or guesses.
Priority:    HIGH
```

---

**Item 2: Findings file entry structure**

```
Source:      CLAUDE.md §"Documentation protocol" + Tier 1 output-formatting-standard.md
Type:        SKILL (partially — Tier 1 covers format, not the session workflow)
Current tier: 1 (format covered); protocol portion UNCLASSIFIED
Decision:    KEEP AS-IS (format covered by Tier 1); protocol addressed by Item 1
Reason:      The five-section format is already documented; the question is when
             and how to start — which is Item 1.
Priority:    MEDIUM
```

---

**Item 3: Commit message conventions**

```
Source:      CLAUDE.md §"Commit conventions" + Tier 1 output-formatting-standard.md
Type:        SKILL
Current tier: 1
Decision:    KEEP AS-IS
Reason:      Fully covered by output-formatting-standard.md commit message section.
Priority:    LOW
```

---

**Item 4: Newsletter audience description**

```
Source:      CLAUDE.md §"Newsletter context"
Type:        CONTEXT
Current tier: N/A
Decision:    KEEP AS-IS
Reason:      Not an agent instruction; provides caller context for tone calibration.
Priority:    LOW
```

---

**Item 5: output-formatting-standard.md (Tier 1 v1.0)**

```
Source:      docs/skills/tier1/output-formatting-standard.md
Type:        SKILL
Current tier: 1
Decision:    KEEP AS-IS
Reason:      Well-formed skill covering findings format, Gherkin formatting,
             commit messages, and code snippets. No gaps identified.
Priority:    LOW (already a skill)
```

---

**Item 6: gherkin-scenario-quality.md (Tier 2 v1.1)**

```
Source:      docs/skills/tier2/gherkin-scenario-quality.md
Type:        SKILL
Current tier: 2
Decision:    DEPRECATE
Reason:      Superseded by v2.0; Issue #12 review gave CHANGES REQUESTED verdict;
             an agent finding both versions may use the less-safe one.
Priority:    HIGH (risk of active use of deprecated version)
```

---

**Item 7: gherkin-scenario-quality-v2.md (Tier 2 v2.0)**

```
Source:      docs/skills/tier2/gherkin-scenario-quality-v2.md
Type:        SKILL
Current tier: 2
Decision:    KEEP AS-IS (APPROVED WITH COMMENTS verdict from Issue #12)
Reason:      Canonical version; four guards correctly implemented; v2.1 improvements
             documented but not blocking.
Priority:    LOW (already canonical)
```

---

**Item 8: why-this-matters-writing.md (Tier 3 v1.0)**

```
Source:      docs/skills/tier3/why-this-matters-writing.md
Type:        SKILL
Current tier: 3
Decision:    PROMOTE to Tier 2
Reason:      Skill file itself documents the promotion decision and criteria; the
             four-component structure is a project-wide output contract, not a
             personal pattern.
Priority:    MEDIUM
```

---

**Item 9: prompt-gherkin-scenario-quality.md**

```
Source:      docs/prompts/prompt-gherkin-scenario-quality.md
Type:        PROMPT
Current tier: N/A
Decision:    DEPRECATE
Reason:      The "before" artifact from Issue #9. The skill it preceded (Item 7)
             is now canonical v2.0. An agent reading this prompt file gets the
             pre-skill version of the quality check — no output contract, no
             routing signal, no guards.
Priority:    HIGH (active liability if used instead of skill)
```

---

**Item 10: spec-audit-framework.md**

```
Source:      docs/spec-audit-framework.md
Type:        SKILL candidate (methodology without routing signal or output contract)
Current tier: UNCLASSIFIED
Decision:    CONVERT TO SKILL
Reason:      Contains the complete five-question diagnostic, six-class taxonomy,
             fix rubric, and scorecard template — all the methodology needed for
             a Tier 2 skill. Missing: routing signal, when-to-use, output contract.
Priority:    HIGH
```

---

**Item 11: skill-review-checklist.md**

```
Source:      docs/skill-review-checklist.md
Type:        SKILL candidate (structured checklist used by PR template)
Current tier: UNCLASSIFIED
Decision:    KEEP AS-IS as reference document
Reason:      The checklist is a structured document, not an agent instruction —
             agents are directed to it explicitly (from CLAUDE.md and skill
             descriptions) rather than routed to it automatically.
Priority:    LOW
```

---

**Item 12: skill-pr-template.md**

```
Source:      docs/skill-pr-template.md
Type:        CONTEXT
Current tier: N/A
Decision:    KEEP AS-IS
Reason:      Template document filled in by humans for PR review; not an agent
             instruction that requires a routing signal.
Priority:    LOW
```

---

**Item 13: Step definition section separator pattern**

```
Source:      tests/steps/ — all four files use # ── Given/When/Then ──
Type:        PATTERN (implicit)
Current tier: UNCLASSIFIED
Decision:    CONVERT TO SKILL (merged with Items 14–17 into one step-definition skill)
Reason:      Implicit visual convention followed in all four test files; undocumented.
Priority:    HIGH
```

---

**Item 14: Fixture chaining pattern**

```
Source:      tests/steps/ — Given steps return stub scenario keys;
             When steps consume them
Type:        PATTERN (implicit)
Current tier: UNCLASSIFIED
Decision:    CONVERT TO SKILL (merged with Item 13)
Reason:      The fixture chaining model (given returns "success"/"declined"/etc.,
             when uses it to select the mock stub) is the core test architecture
             pattern. An agent writing steps without this produces structurally
             incompatible test files.
Priority:    HIGH
```

---

**Item 15: API response dict pattern**

```
Source:      tests/steps/ — When steps return {"response": r, "elapsed": t}
Type:        PATTERN (implicit)
Current tier: UNCLASSIFIED
Decision:    CONVERT TO SKILL (merged with Item 13)
Reason:      Then steps depend on this structure; divergence causes AttributeError.
Priority:    HIGH
```

---

**Item 16: Assertion message pattern**

```
Source:      tests/steps/ — every assert has an f-string with actual value
Type:        PATTERN (implicit)
Current tier: UNCLASSIFIED
Decision:    CONVERT TO SKILL (merged with Item 13)
Reason:      Without the assertion message, test failures produce no useful output.
Priority:    MEDIUM
```

---

**Item 17: Sleep-before-async-assert pattern**

```
Source:      tests/steps/ — time.sleep(0.3) before fire-and-forget assertions
Type:        PATTERN (implicit)
Current tier: UNCLASSIFIED
Decision:    CONVERT TO SKILL (merged with Item 13)
Reason:      Without this, notification assertions fail intermittently on timing.
             The 0.3-second constant is derived from profiling and never explained.
Priority:    MEDIUM
```

---

**Item 18: Agent fresh re-implementation protocol**

```
Source:      findings/issue-03-agent-fresh-implementation.md §"What I tried"
Type:        PATTERN (used once)
Current tier: UNCLASSIFIED
Decision:    KEEP AS-IS
Reason:      Used once (Issue #3); not a recurring session pattern; historical record.
Priority:    LOW
```

---

**Item 19: Spec cross-run testing**

```
Source:      findings/issue-05-the-spec-that-doesnt-lie.md §"What I tried"
Type:        PATTERN (used once)
Current tier: UNCLASSIFIED
Decision:    KEEP AS-IS
Reason:      Used once; high-value technique but not a recurring session pattern.
Priority:    LOW
```

---

### Inventory summary

**Total items: 19**

**Type breakdown:**
- PROMPT: 1 (item 9)
- PATTERN: 7 (items 13–19)
- SKILL: 5 (items 3, 5, 6, 7, 8)
- CONTEXT: 3 (items 4, 11, 12)
- SKILL candidate: 2 (items 10, 11)
- Mixed (covered by multiple items): 2 (items 1, 2)

**Already properly converted to skills: 4**
(output-formatting-standard, gherkin-quality-v1.1, gherkin-quality-v2.0, why-this-matters-writing)

**Note:** gherkin-quality-v1.1 counts as "converted" but is now superseded; v2.0 is the correct canonical version.

**HIGH priority unconverted items: 5**
- Item 1: Session start protocol (no skill exists)
- Item 6: v1.1 still active (deprecation needed)
- Item 9: Prompt file still active (deprecation needed)
- Item 10: spec-audit-framework (skill candidate, not a skill)
- Items 13–17 combined: Step definition conventions (five patterns, zero documentation)

**Most dangerous gap:**

Items 13–17 combined. Five distinct implicit conventions followed in every step definition file in the project — the section separator format, the fixture chaining model, the response dict structure, the assertion message pattern, and the sleep duration for async assertions — are not written down anywhere outside the code itself. An agent that has not read all four existing step files would produce structurally incompatible tests. Two of the five conventions (Items 15 and 17) cause test failures when violated, not just style drift.

**Most surprising finding:**

The session start protocol (Item 1) is the most-used skill-shaped behaviour in the project — applied at the beginning of every one of the twelve completed issues — and it has never been formalized. Every findings file in this project was created because an agent read CLAUDE.md prose and followed it correctly. There was never a contract; there was only a document. Twelve issues of correct behavior is evidence that CLAUDE.md is clear, not that the protocol is robust.

---

## Phase 2 — Three Highest-Priority Skill Conversions

**Date:** 2026-06-16
**Status:** ✅ Complete

The three conversions selected from HIGH priority items:

1. **Session start protocol** → docs/skills/tier2/session-start-protocol.md
2. **Feature file audit** → docs/skills/tier2/feature-file-audit.md
3. **Step definition conventions** → docs/skills/tier2/step-definition-style.md

### Self-review: session-start-protocol.md

**Dimension 1: Routing signal**

1.1 Description: "Initialize a new issue session: create the findings file, update the index, and confirm scope before first tool call."
Count: 117 characters. **PASS.**

1.2 Names artifact type: "findings file" is the primary output. **PASS.**

1.3 Names domain/scope: "issue session" is the scope; the "When to use" section constrains to this project. Borderline — the description doesn't say "order-api." **CONDITIONAL PASS** — relies on When-to-use for full scoping.

1.4 Names methodology: This skill is a procedure, not a reasoning methodology — correct for a protocol skill. The description names the three actions. **PASS** (procedure by design, not by omission).

1.5 Routing test:
- SHOULD: "Start Issue #14 session" → routes correctly
- SHOULD: "Begin a new newsletter issue session" → routes correctly
- SHOULD: "Create the findings file for this session" → routes correctly
- SHOULD NOT: "Write a Gherkin scenario for the payment timeout" → does not route (no findings/index language)
- SHOULD NOT: "Commit changes to the repo" → does not route
- SHOULD NOT: "Review the v2.0 skill for quality" → does not route

No misroutes found. **PASS.**

**Dimension 2: Output contract — PASS** (explicit file creation, enumerable format checks, testable without running)

**Dimension 3: Methodology — PASS** (procedure appropriate; domain knowledge about naming convention and zero-padding documented)

**Dimension 4: Idempotency — STABLE** (same output every session start; if file already exists, skill should detect and halt)

**Dimension 5: Failure modes:**
- File already exists: CORRECT REFUSAL (documented in skill)
- Issue number not in session instructions: CORRECT REFUSAL

**Self-review verdict: APPROVED**

---

### Self-review: feature-file-audit.md

**Dimension 1: Routing signal**

1.1 Description: "Audit a Gherkin feature file for spec debt using the six-class taxonomy and return a scored report."
Count: 97 characters. **PASS.**

1.2 Names artifact type: "scored report" — the output is the report, not the fixed file. **PASS.**

1.3 Names domain: "Gherkin feature file" — names the input domain. "Spec debt" — names the problem space. **PASS.**

1.4 Names methodology: "six-class taxonomy" — distinguishes this from a generic quality review. **PASS.**

1.5 Routing test:
- SHOULD: "Audit order_creation.feature for spec debt" → routes correctly
- SHOULD: "Review the notification feature file before the next session" → routes
- SHOULD: "Find all the debt in this feature file before we fix it" → routes
- SHOULD NOT: "Fix this scenario's underspecified step" → does not route (that's gherkin-quality-v2.0)
- SHOULD NOT: "Write new scenarios for order cancellation" → does not route
- SHOULD NOT: "Review app/main.py for correctness" → does not route

No misroutes. **PASS.**

**Dimension 2: Output contract**

2.3 The skill must NOT produce a fixed version of the feature file. This absence requirement is explicitly stated. **PASS.**

2.4 Downstream consumer: the audit output is consumed by the human author (to decide which debt items to fix) and then by gherkin-quality-v2.0 (to fix each item). Both consumers are identified. **PASS.**

**Dimension 3: Methodology — PASS** (references spec-audit-framework.md; methodology is fully documented there; reasoning is present, not just procedure)

**Dimension 4: Idempotency — STABLE** (auditing same file produces same report; audit does not modify the file)

**Dimension 5: Failure modes:**
- order_status_bad.feature input: CORRECT REFUSAL (explicitly handled — this is a pedagogical artifact)
- Non-feature-file input: CORRECT REFUSAL (documented)
- Empty feature file: CORRECT REFUSAL

**Self-review verdict: APPROVED**

---

### Self-review: step-definition-style.md

**Dimension 1: Routing signal**

1.1 Description: "Write pytest-bdd step definitions for order-api using the fixture-chaining pattern and assertion conventions."
Count: 108 characters. **PASS.**

1.2 Names artifact type: "step definitions" — the Python file produced. **PASS.**

1.3 Names domain: "order-api" — project-scoped. **PASS.**

1.4 Names methodology: "fixture-chaining pattern and assertion conventions" — distinguishes from generic pytest step writing. **PASS.**

1.5 Routing test:
- SHOULD: "Write step definitions for the payment cancellation feature" → routes
- SHOULD: "Implement the pytest-bdd steps for this scenario" → routes
- SHOULD: "Create the test steps file for order_cancel.feature" → routes
- SHOULD NOT: "Write a feature file for order cancellation" → does not route (Gherkin, not steps)
- SHOULD NOT: "Review the step definitions for quality" → ambiguous; currently routes; acceptable
- SHOULD NOT: "Implement app/main.py for the cancel endpoint" → does not route (implementation, not test)

One borderline SHOULD NOT (review vs. write). Acceptable given the "When NOT to use" section. **PASS.**

**Dimension 2: Output contract**

2.2 Potential agent divergence: helper function names (`_post_order` style) and whether to extract a shared helper or duplicate the request call. This is under-specified. **APPROVED WITH COMMENT**: helper function naming and extraction pattern is under-specified; a v1.1 should add a helper extraction rule.

**Dimension 3: Methodology — PASS** (each convention has reasoning; the sleep duration has documented origin)

**Dimension 4: Idempotency — CONDITIONALLY STABLE** (same feature file → same step structure; fixture names and helper organization may vary)

**Dimension 5: Failure modes:**
- Scenario with no parseable step: CORRECT REFUSAL
- Feature file from a different service (not order-api): CORRECT REFUSAL (documented)

**Self-review verdict: APPROVED WITH COMMENTS** (helper function pattern under-specified; note for v1.1)

---

## Phase 3 — The Junk Drawer

**Date:** 2026-06-16
**Status:** ✅ Complete

**Items deprecated:**

1. **docs/prompts/prompt-gherkin-scenario-quality.md** — DEPRECATED
   - Was: the "before" artifact from Issue #9; the prompt as it existed before being converted to a skill
   - Now superseded by: docs/skills/tier2/gherkin-scenario-quality-v2.md
   - Risk of leaving active: an agent finding this file has the pre-guard, pre-output-contract version of the quality check. It produces output that satisfies no formal contract, has no idempotency protection, and no domain check. Issue #11 found four failure modes in the skill version; the prompt version has all four plus additional divergence risk.

2. **docs/skills/tier2/gherkin-scenario-quality.md (v1.1)** — DEPRECATED
   - Was: the first formalized version, produced in Issue #9; received CHANGES REQUESTED verdict in Issue #12 review
   - Now superseded by: docs/skills/tier2/gherkin-scenario-quality-v2.md
   - Risk of leaving active: any agent routing to this skill gets the UNSTABLE idempotency version with PLAUSIBLE WRONG behavior for UI scenarios and contradictory inputs. The v2.0 header says "Supersedes: gherkin-scenario-quality.md" but an agent that reads v1.1 directly has no way to know it's deprecated.

**No MERGE candidates found:** Each item expresses a distinct instruction. The spec-audit-framework.md and the new feature-file-audit.md skill are related but not duplicates — the framework is the detailed reference; the skill is the callable interface.

**No DELETE candidates found in this session** (per constraints: mark only, do not delete).

---

## Phase 4 — Skill Audit Template

**Date:** 2026-06-16
**Status:** ✅ Complete

Created at: `docs/skill-audit-template.md`

The template is standalone — no references to order-api, Gherkin, or newsletter-specific tools. Structured in six sections per the session instructions:
1. What counts as a prompt library item
2. Classification taxonomy (four types with decision tree)
3. Conversion decision criteria (five questions)
4. Conversion checklist (five questions, abbreviated from Issue #12 review checklist)
5. Audit scorecard template
6. Junk drawer test (four questions)

---

## Phase 5 — Layer 2 Retrospective

**Date:** 2026-06-16
**Status:** ✅ Complete

### What building Layer 2 (Issues #9–13) changed

Before Issue #9, this project had one reusable quality check: a pasted prompt. No routing signal. No output contract. No version. No idempotency guarantee. The prompt worked because the human author remembered to paste it and because the agent happened to be in the right context to apply it. That is not infrastructure. That is memory.

Five issues later:

- **A Tier 1 skill** governs all formatting decisions across every agent in every session — findings files, commit messages, Gherkin indentation, code snippet format. Agents that have never seen this project before can produce correctly-formatted findings files because the skill tells them exactly what to produce.

- **A Tier 2 skill (v2.0 with four guards)** replaces the pasted prompt. It fails loudly for UI scenarios, contradictory inputs, and already-correct inputs. Issue #11's stress tests found the failure modes; Issue #12's review found the routing signal problem and the Guard 4 ambiguity that the stress tests could not find. The skill has been reviewed by a structured five-dimension checklist. The prompt never was.

- **A review framework** — the five-dimension checklist and PR template from Issue #12 — means that future skills can be evaluated before they're published, not after they've been stress-tested into failure. This is the most significant infrastructure addition: it makes the skill-building process itself auditable.

- **A skill audit template** — created in this session — means any project can run the same inventory process without reading the newsletter. The work generalizes.

Three new Tier 2 skills — session start protocol, feature file audit, and step definition style — capture patterns that survived twelve issues without being written down. That these patterns were followed consistently for twelve issues is evidence that CLAUDE.md is a clear document. It is not evidence that the patterns are robust. The difference matters when CLAUDE.md changes, when a new agent reads a different version, or when the project scales beyond the newsletter context.

### What is still missing at the end of Layer 2

**The implementation layer is undocumented.** Every implementation session relies on an agent reading `app/main.py` and inferring the patterns: the FastAPI route structure, the in-memory order store, the mock-stub selection via request body, the background notification thread. These are consistent across twelve issues. They are consistent because the same files were read each time, not because a skill exists.

**The why-this-matters promotion is incomplete.** The Tier 3 skill has a documented promotion decision with three criteria that must be met first. None of those criteria have been met in this session. The skill remains at Tier 3. An agent writing "why this matters" paragraphs for a new project member or a new agent will not find this skill through automatic routing.

**The step-definition-style skill has an open finding.** The self-review gave APPROVED WITH COMMENTS — the helper function extraction pattern is under-specified. An agent writing step definitions may or may not extract `_post_order`-style helpers. The resulting test files will work, but they will not be structurally consistent.

**The answer to "what's still living in someone's head":**

The implementation conventions in `app/main.py` — how the order store works, why the mock stub selection is done via request body parameters rather than URL routing, why the notification is fire-and-forget with a 0.3-second sleep rather than synchronous — are not documented anywhere except the code itself and the findings files that explain individual decisions. An agent implementing a new endpoint today would read the code, derive the patterns, and probably get them right. An agent implementing a new endpoint after a refactor might not.

Layer 3 inherits: a working skills infrastructure, a review process, an audit process, one under-specified skill (step-definition-style v1.0), one promoted-but-not-merged skill (why-this-matters at Tier 3), and an undocumented implementation layer that is the highest-risk gap in the project.

---

## Phase 6 — Test Suite Results

**Date:** 2026-06-16
**Status:** ✅ Complete

```text
pytest tests/steps/ -v
→ 11 passed

pytest tests/pact/ -v
→ 4 passed

python3 scripts/can_i_deploy.py
→ ALL CONTRACTS VERIFIED — safe to deploy
```

All 15 tests passed. No implementation files modified.

---

### Why this matters

The most dangerous item in the inventory is not the deprecated prompt or the v1.1 skill — it is the five implicit step definition conventions that have been followed in every test file across twelve issues without ever being written down. UNDERSPECIFIED knowledge is not neutral: it works until it doesn't, and when it stops working, there is no contract to point to. The step-definition-style skill converts five conventions from implicit to explicit — not because the code was wrong, but because implicit conventions don't survive agent context switches, project transfers, or version upgrades. The broader principle: auditing a prompt library is not about finding what failed; it is about naming what hasn't failed yet and asking how much of that success is documented versus remembered. After twelve issues of careful work, this project had more in the second category than anyone expected.
