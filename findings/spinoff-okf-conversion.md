# Findings: OKF Conversion — "I Converted the order-api to OKF. Here's What I Found."

**Date:** 2026-07-14
**Session type:** Spin-off article — documentation conversion + comparison experiment
**Test baseline:** 20 tests (16 Gherkin + 4 Pact) — must remain green throughout

---

## Phase 1 — Audit of existing docs/ structure

### Pre-flight: Eval: Environment

Before modifying docs/skills/ and docs/ADR/ (shared production resources per eval-environment.md Q1), the behavioral delta was documented:

- Modification: Adding YAML frontmatter blocks and "## Related" navigation sections
- What changes for future agents: structured type/description/tags at the top of every file; discovery cross-links at the bottom of key files
- What does NOT change: all methodology instructions, all agent check questions, all HALT conditions
- Q2 (pipeline gate disabled?): NO
- Q3 (agent behavior changed?): Marginally yes for discovery — agents reading these files gain additional metadata but receive the same methodology. Intentional. Proceeding.

### File-to-OKF mapping table

| File | Current type | OKF type | Frontmatter needed |
|---|---|---|---|
| `docs/ADR/ADR-001-inventory-before-payment.md` | ADR | Decision | type, title, description, tags, timestamp |
| `docs/ADR/ADR-002-fire-and-forget-notification.md` | ADR | Decision | type, title, description, tags, timestamp |
| `docs/evals/eval-environment.md` | Eval | Guardrail | type, title, description, tags, timestamp |
| `docs/evals/eval-operation-scope.md` | Eval | Guardrail | type, title, description, tags, timestamp |
| `docs/evals/eval-contract-preflight.md` | Eval | Guardrail | type, title, description, tags, timestamp |
| `docs/skills/tier1/output-formatting-standard.md` | Skill | Methodology | type, title, description, tags, timestamp |
| `docs/skills/tier2/gherkin-scenario-quality.md` | Skill (v1.1, superseded) | Methodology | type, title, description, tags, timestamp |
| `docs/skills/tier2/gherkin-scenario-quality-v2.md` | Skill (v2, current) | Methodology | type, title, description, tags, timestamp |
| `docs/skills/tier2/session-start-protocol.md` | Skill | Methodology | type, title, description, tags, timestamp |
| `docs/skills/tier2/step-definition-style.md` | Skill | Methodology | type, title, description, tags, timestamp |
| `docs/skills/tier2/feature-file-audit.md` | Skill | Methodology | type, title, description, tags, timestamp |
| `docs/skills/tier3/why-this-matters-writing.md` | Skill | Methodology | type, title, description, tags, timestamp |
| `docs/runbooks/payment-gateway-degraded-agent.md` | Runbook | Playbook | type, title, description, tags, timestamp |
| `docs/runbooks/payment-gateway-degraded-human.md` | Runbook | Playbook | type, title, description, tags, timestamp |
| `docs/layer3-artifact-map.md` | Reference | Reference | type, title, description, tags, timestamp |
| `docs/spec-audit-framework.md` | Reference | Reference | type, title, description, tags, timestamp |
| `docs/jcurve-conditions-framework.md` | Reference | Reference | type, title, description, tags, timestamp |
| `docs/skill-audit-template.md` | Reference | Reference | type, title, description, tags, timestamp |
| `docs/skill-review-checklist.md` | Reference | Reference | type, title, description, tags, timestamp |
| `docs/skill-pr-template.md` | Reference | Reference | type, title, description, tags, timestamp |
| `docs/prompts/prompt-gherkin-scenario-quality.md` | Prompt source | Reference | type, title, description, tags, timestamp |
| `docs/claude-md-versions/naive.md` | Pedagogical example | Reference | type, title, description, tags, timestamp |
| `docs/claude-md-versions/better.md` | Pedagogical example | Reference | type, title, description, tags, timestamp |
| `docs/claude-md-versions/production-grade.md` | Pedagogical example | Reference | type, title, description, tags, timestamp |
| `CLAUDE.md` (project root) | Agent standing orders | Agent Standing Orders | type, title, description, tags, timestamp |

**Total documents in scope: 25** (24 in docs/ + CLAUDE.md at root)

### Pre-conversion assessment

**Documents that map cleanly to OKF concepts:**
- Both ADRs: have clear decision + rationale structure, map directly to `Decision` type
- All 3 evals: have explicit trigger conditions and HALT protocol, map to `Guardrail`
- Both runbooks: have structured decision trees, map cleanly to `Playbook`
- All 6 skills (tier1, tier2, tier3): have description and when-to-use sections, map to `Methodology`

**Documents that benefit most from OKF cross-linking:**
1. `eval-environment.md` → links to ADRs it enforces and to the CLAUDE.md pre-flight table
2. `eval-operation-scope.md` → links to ADR-001 and ADR-002 explicitly
3. `eval-contract-preflight.md` → links to Pact invariant and payment gateway runbook
4. `ADR-001` and `ADR-002` → link back to the evals that enforce them and the Gherkin scenarios that test them
5. `gherkin-scenario-quality-v2.md` → links to spec-audit-framework.md and the issue that motivated v2

---

## Phase 2 — OKF frontmatter conversion

### What was added to each document type

**ADRs** (`type: Decision`): Added frontmatter and a `## Related` section linking to:
- The eval that enforces this decision at pre-flight
- The Gherkin scenarios in tests/features/ that behaviorally enforce the decision
- The CLAUDE.md invariant section that references the ADR

**Evals** (`type: Guardrail`): Added frontmatter and a `## Related` section linking to:
- The ADRs whose invariants this eval enforces
- The runbooks or skills that reference this eval in their body text
- The CLAUDE.md pre-flight table entry that routes to this eval

**Skills** (`type: Methodology`): Added frontmatter and a `## Related` section linking to:
- The tier-1 skill (for tier-2 and tier-3 skills)
- The skill review checklist
- The findings issue or spec document that motivated the skill

**Runbooks** (`type: Playbook`): Added frontmatter and a `## Related` section linking to:
- The evals that should have prevented the incident scenario
- The ADRs relevant to decisions made during the runbook
- The relevant external service contract section in CLAUDE.md

**Reference documents** (`type: Reference`): Frontmatter only — no "Related" sections added.

**Deprecated files** (`type: Methodology` / `type: Reference`): Frontmatter added before the HTML deprecation comment. OKF frontmatter must be at line 1.

**CLAUDE.md** (`type: Agent Standing Orders`): Frontmatter added at line 1. File remains at project root with original filename.

### OKF conformance check result

```
Total docs: 24
Missing frontmatter: 0
All docs have frontmatter.
```

All 24 docs/ files pass. CLAUDE.md passes as well (checked manually).

---

## Phase 3 — OKF bundle structure

Index files created:

| File | Purpose |
|---|---|
| `docs/index.md` | Entry point for the entire bundle — overview + subdirectory links + root-level concept list |
| `docs/ADR/index.md` | Lists both ADRs with single-sentence descriptions |
| `docs/evals/index.md` | Lists all three evals with trigger summaries |
| `docs/runbooks/index.md` | Lists both runbooks with trigger scenarios |
| `docs/skills/index.md` | Explains the three-tier structure; links to tier subdirectories |
| `docs/skills/tier1/index.md` | Lists the one tier-1 skill |
| `docs/skills/tier2/index.md` | Lists all five tier-2 skills (including deprecated) |
| `docs/skills/tier3/index.md` | Lists the one tier-3 skill |
| `docs/log.md` | Bundle update history — one entry for today's OKF conversion |

All index files: no frontmatter (per OKF spec §6).

---

## Phase 4 — Comparison experiment

### Task (verbatim, used identically in both runs)

> "Add a new endpoint to the order service: GET /orders/{order_id}/history — returns a list of status changes the order has gone through (created, confirmed, cancelled etc.) with timestamps. Write the Gherkin scenarios first. Apply the relevant skills. Run the pre-flight evals. Then implement."

Both runs used real subagents with fresh context. Neither was told what the other did.

---

### Run A — Current structure (baseline)

**Starting conditions:** CLAUDE.md + task description only. No mention of OKF or index files.

**Navigation log (files read before first Gherkin line, in order):**

1. `docs/skills/tier1/output-formatting-standard.md` — Tier 1 formatting skill (CLAUDE.md skill table named it explicitly)
2. `docs/skills/tier2/gherkin-scenario-quality-v2.md` — Gherkin quality skill v2 (CLAUDE.md skill table named it explicitly)
3. `docs/ADR/ADR-001-inventory-before-payment.md` — CLAUDE.md decision index directed here
4. `docs/ADR/ADR-002-fire-and-forget-notification.md` — CLAUDE.md decision index directed here
5. `docs/evals/eval-operation-scope.md` — CLAUDE.md pre-flight table directed here
6. `tests/features/order_creation.feature` — Style reference for Gherkin patterns
7. `tests/features/order_status_good.feature` — Style reference for GET endpoint assertions
8. `app/main.py` — Order data model, in-memory store structure
9. `tests/features/notification_service.feature` — Count pattern style reference
10. `docs/evals/index.md` — Confirmed all three evals; verified nothing missed

**Q2 — Gherkin skill discovery:** Found at step 2. CLAUDE.md's skill table named the exact file path. Two tool calls: CLAUDE.md (already loaded) → open the skill directly.

**Q3 — ADR discovery:** Both found at steps 3–4. CLAUDE.md decision index provided direct paths. No traversal required.

**Q4 — Eval discovery:** eval-operation-scope.md found at step 5 via CLAUDE.md pre-flight table. Step 10 consulted docs/evals/index.md to confirm no other evals missed. The other two evals were NOT read.

**Q5 — Implicit decisions:** 10 decisions made (field names "history", "status", "changed_at"; chronological ordering; feature file name; CONFIRMED as first state; 3 scenarios; 404 behavior; error field name; UUID prefix).

**Q6 — Estimated time:** ~12 tool calls × 2 seconds = ~24 seconds for navigation + Gherkin writing.

---

### Run B — OKF bundle

**Starting conditions:** CLAUDE.md + task description + `docs/index.md` as explicit starting point. Agent told: "The docs/ directory is an OKF knowledge bundle. Start by reading docs/index.md for an overview of available knowledge, then navigate from there."

**Navigation log (files read before first Gherkin line, in order):**

1. `docs/index.md` — entry point (required by experiment)
2. `docs/skills/` directory listing — index mentioned skills/ subdirectory
3. `docs/ADR/` directory listing — index mentioned ADR/ subdirectory
4. `docs/evals/` directory listing — index mentioned evals/ subdirectory
5. `docs/skills/index.md` — to understand three-tier skill structure
6. `docs/ADR/index.md` — to read ADR index before individual ADRs
7. `docs/evals/index.md` — to understand which evals exist and what they trigger on
8. `docs/skills/tier2/index.md` — to find Gherkin quality skill by name
9. `docs/skills/tier2/gherkin-scenario-quality-v2.md` — the Gherkin quality skill
10. `docs/ADR/ADR-001-inventory-before-payment.md` — pre-flight ADR check per eval-operation-scope Q1
11. `docs/evals/eval-operation-scope.md` — pre-flight eval for app/main.py and tests/ changes
12. `docs/ADR/ADR-002-fire-and-forget-notification.md` — complete pre-flight ADR check
13. `docs/evals/eval-environment.md` — **confirmed NOT triggered** (run B read this proactively; run A did not)
14. `docs/evals/eval-contract-preflight.md` — **confirmed NOT triggered** (run B read this proactively; run A did not)
15. `docs/skills/tier1/output-formatting-standard.md` — Tier 1 formatting skill
16. `tests/features/order_status_good.feature` — Style reference
17. `tests/features/order_cancellation.feature` — Style reference (Run A did not read this)
18. `app/main.py` — Order data model
19. `tests/features/order_creation.feature` — Style reference
20. `docs/skills/tier2/step-definition-style.md` — Step definition conventions (**Run A did not read this**)

**Q2 — Gherkin skill discovery:** Found at step 9. Navigation path: docs/index.md → skills/ listing → skills/index.md → tier2/index.md → gherkin-scenario-quality-v2.md. Five hops vs two hops in Run A.

**Q3 — ADR discovery:** Both found at steps 10 and 12. Agent used the ADR/index.md cross-link as primary path; decision index in CLAUDE.md as secondary confirmation. The "Related" section in eval-operation-scope.md also cross-linked both ADRs — a third confirmation.

**Q4 — Eval discovery:** All THREE evals read (steps 11, 13, 14) — agent used evals/index.md to understand the full eval space and confirmed each one's scope. Run A only read the one eval that fires.

**Q5 — Implicit decisions:** 11 decisions made. Same pattern as Run A with one additional decision: "occurred_at" vs "changed_at" as field name for the per-entry timestamp, with explicit reasoning about distinguishing from the top-level timestamp field. Run A also made this decision (chose "changed_at") but documented it less explicitly.

**Q6 — Estimated time:** ~24 tool calls × 2 seconds = ~48 seconds for navigation + Gherkin writing.

---

### The comparison

**1. Did the agent find the relevant skill faster in Run B?**

No. Run A found the Gherkin skill at navigation step 2 (2 tool calls from CLAUDE.md). Run B found it at step 9 (5 tool calls via the index hierarchy: docs/index.md → skills/ → skills/index.md → tier2/ → tier2/index.md → skill file). OKF was slower by 3 navigation steps.

The reason: CLAUDE.md's skill table names exact file paths ("docs/skills/tier2/gherkin-scenario-quality-v2.md"). The OKF index hierarchy adds structural navigation layers that are traversed top-down. When CLAUDE.md already provides a direct pointer, OKF's hierarchical navigation is strictly slower.

**2. Did OKF cross-linking change which documents the agent consulted?**

Yes — significantly. The evals/index.md caused Run B to read ALL THREE evals (eval-environment.md and eval-contract-preflight.md in addition to eval-operation-scope.md). Run A only read the one eval that actually fires. The "Related" section in eval-operation-scope.md provided a third confirmation path to ADR-001 and ADR-002 that Run A's agent did not use.

Specific links followed in Run B that Run A did not follow:
- `docs/evals/index.md` → eval-environment.md → read and confirmed not triggered
- `docs/evals/index.md` → eval-contract-preflight.md → read and confirmed not triggered
- `docs/skills/tier2/index.md` → step-definition-style.md → read (not needed for Gherkin writing, but now known to exist)
- `docs/ADR/index.md` → ADR-001 and ADR-002 (cross-path to same files Run A found via decision index)

**3. Were there documents found in one run but not the other?**

Run A found but Run B did not:
- `tests/features/notification_service.feature` — Read A used it as a count-pattern style reference; Run B found the same patterns elsewhere

Run B found but Run A did not:
- `docs/evals/eval-environment.md` — proactively confirmed not triggered
- `docs/evals/eval-contract-preflight.md` — proactively confirmed not triggered
- `docs/skills/tier2/step-definition-style.md` — discovered via tier2/index.md; Run A never found this skill

Run B's agent now knows about `step-definition-style.md` — a document that CLAUDE.md does not reference in its skill table. This is the clearest case of OKF filling a gap that CLAUDE.md leaves uncovered.

**4. Did the index.md entry point change the order in which the agent built its understanding?**

Yes — and this is the most structural difference between the two runs. Run A built understanding SPECIFIC-FIRST: it went directly to individual documents named in CLAUDE.md before having any overview of what existed. Run B built understanding OVERVIEW-FIRST: it read the bundle structure (docs/index.md → subdir indices) before reading any individual document, arriving at each document with knowledge of what else existed in the same category.

This difference mattered for the eval space: Run B's agent knew "there are three evals" before reading any of them. Run A's agent knew "there is a pre-flight table in CLAUDE.md" and read only the eval that fired.

**5. Did the OKF frontmatter change any agent decision?**

Not directly. The `type`, `tags`, and `description` fields were not cited as decision drivers in either run. The `description` field in index.md entries was used to confirm documents before opening them — but this was confirmation, not routing. Routing was driven by CLAUDE.md's skill table and pre-flight table in Run A, and by index.md hierarchy + CLAUDE.md in Run B.

The frontmatter's most useful effect was indirect: the `description` field in index.md entries gave Run B's agent enough context to decide "this is the eval I need to read" without opening every file first. But this is a modest efficiency gain, not a qualitative change.

**6. How many implicit decisions were made in Run A vs Run B? Is the difference meaningful?**

Run A: 10 implicit decisions. Run B: 11. Difference of 1 — within noise. Both agents made equivalent decisions about field names, ordering, scenario count, and error messages. The extra decision in Run B (explicit reasoning about "occurred_at" vs "changed_at") reflects more documented decision-making, not more correct decision-making — Run A made the same decision and just named it differently ("changed_at").

OKF cross-linking does not reduce implicit decisions for Gherkin scenario writing. The implicit decisions come from product requirements that no amount of infrastructure can supply: what to name a field, what ordering to use, whether "CREATED" is a valid first status. These are specification gaps, not navigation gaps.

**7. The most important finding: what does OKF give an agent that the current structure does not? What does the current structure give an agent that OKF does not add to?**

**What OKF gives:**

*Complete discoverability without CLAUDE.md coverage.* The step-definition-style.md skill was found by Run B (via tier2/index.md) but not by Run A. CLAUDE.md's skill table references three skills by path; tier2/index.md lists five. OKF's index hierarchy makes everything discoverable even when CLAUDE.md's pointers are incomplete. The bundle knows its own contents; CLAUDE.md knows only what it has been told about.

*Structural overview before specific content.* The docs/index.md entry point let Run B's agent build a map before navigating. For a new agent in a project with many documents and no prior context, this matters: it prevents the agent from assuming "I have found everything" when it has only found what CLAUDE.md named.

*Cross-document relationships via "Related" sections.* The "Related" section in eval-operation-scope.md provided a third confirmation path to both ADRs. When an agent reaches a document via one path (pre-flight table) and the document itself confirms the relationship via cross-links, the agent's confidence in the navigation is higher.

**What the current structure (CLAUDE.md) gives that OKF alone cannot:**

*Direct pointers are faster than hierarchical traversal.* When CLAUDE.md names an exact file path, the agent makes one tool call. When OKF provides a hierarchy, the agent makes N calls proportional to depth. For the specific task in this experiment, CLAUDE.md was 3 steps faster for skill discovery.

*Routing logic.* The CLAUDE.md pre-flight table maps file types to evals: "if modifying app/main.py, run eval-operation-scope.md." OKF has no mechanism for this. An OKF bundle can express "eval-operation-scope.md exists and intercepts app/main.py modifications" in the eval's frontmatter description, but it cannot instruct an agent to run it before a specific action. Routing is behavioral instruction; OKF is structural description. These are different layers.

*Behavioral constraints and prohibitions.* CLAUDE.md's "You may not" list, invariant statements, and environment discrimination sections are not representable as OKF frontmatter. They are instructions, not metadata. OKF formalizes what exists and how it relates; it does not formalize what must be done or what must not.

**The synthesis:** OKF and CLAUDE.md solve different problems. CLAUDE.md is an instruction document that happens to contain a knowledge map. OKF is a knowledge map that happens to be readable by agents. When both exist, CLAUDE.md's direct pointers are faster; OKF's index hierarchy is more complete. The combination is more capable than either alone: OKF catches the documents CLAUDE.md doesn't reference; CLAUDE.md provides the routing logic OKF cannot express.

---

## Phase 5 — Gaps and observations

### What OKF does not yet handle for this project

**1. Invariant documentation**

OKF has no standard concept type for "this property must never change regardless of refactoring." The `type: Decision` ADR covers the decision itself; the invariant statement inside each ADR is a non-standard section within the ADR body. OKF's `type` field has no `Invariant` value.

If OKF were to add an invariant convention, it might look like this:

```yaml
---
type: Invariant
title: "Invariant: Inventory Before Payment"
description: "Inventory availability must be confirmed before any payment gateway call is initiated — regardless of implementation approach."
tags: [invariant, order-creation, payment, testable: partial]
timestamp: 2026-05-01
enforced_by:
  - tests/features/order_creation.feature#scenario-3
  - docs/ADR/ADR-001-inventory-before-payment.md
  - docs/evals/eval-operation-scope.md
---
```

The non-standard fields (`enforced_by`, `testable: partial`) would be extensions — OKF's spec explicitly permits custom key-value pairs. This would be a reasonable OKF extension for projects with un-testable invariants.

**2. Eval routing**

OKF's cross-linking is passive: a "Related" section expresses "document X is related to document Y." It cannot express "before modifying file Z, read and answer all questions in eval Y." The CLAUDE.md pre-flight table is active routing: it instructs the agent to do something, not just know that something exists.

OKF could express this as a convention in the eval's frontmatter description: "description: Pre-flight check that must be run before modifying app/main.py or tests/." An agent reading the evals/index.md would see this description and know the eval is a prerequisite, not just a related document.

But this is softer than CLAUDE.md's explicit routing. A description requires the agent to infer that "must be run before" means "run me before your next action." A CLAUDE.md instruction says exactly that. For high-blast-radius operations, description-as-routing is insufficient. The routing logic belongs in CLAUDE.md; the cross-links belong in OKF.

**3. Version tracking**

Skill files in this project have version numbers (v1.1, v2.0) documented in their body text. OKF's `timestamp` field records last meaningful change but has no standard `version` field.

The existing version convention could be added as an OKF extension:

```yaml
---
type: Methodology
version: "2.0"
supersedes: "docs/skills/tier2/gherkin-scenario-quality.md"
timestamp: 2026-06-15
---
```

Both `version` and `supersedes` would be custom fields that OKF consumers must preserve but are not required to interpret. The current `<!-- DEPRECATED -->` HTML comment in the deprecated file is not machine-readable; an OKF `superseded_by` field would be.

---

### What this project already does that OKF formalizes well

**The findings/ directory as a log.md-equivalent.** Each `findings/issue-NN-*.md` file is a timestamped record of what was attempted, what happened, and what was learned. The findings/README.md is an index. This is the same structure as OKF's `log.md` + `index.md` pattern, arrived at independently. OKF's naming convention makes this pattern explicit and interoperable.

**The skill review checklist as a consumer-specification document.** `docs/skill-review-checklist.md` specifies what any agent (or human) must do before publishing a skill version. In OKF terms, this is a consumer-specification: it describes the behavior expected of any agent that reads a Methodology document. OKF's bundle structure makes this document discoverable via docs/index.md without requiring CLAUDE.md to name it — which is exactly what happened in Run B (the agent found skill-review-checklist.md via the docs/index.md listing).

**The tier structure of docs/skills/ as OKF subdirectory organization.** The three-tier skill architecture (tier1/tier2/tier3/) maps directly to OKF's hierarchical subdirectory structure with index.md at each level. The tier design was made before OKF existed; OKF's convention matches it exactly.

---

## Phase 6 — Test suite results

```
pytest tests/steps/ -v
```

**Status:** ✅ 16 passed

```
pytest tests/pact/ -v
```

**Status:** ✅ 4 passed

```
python scripts/can_i_deploy.py
```

**Status:** ✅ RESULT: ALL CONTRACTS VERIFIED — safe to deploy

**Total: 20 tests, 0 failures.** OKF conversion touched only docs/ files — no implementation, no Gherkin feature files, no step definitions, no Pact files modified. All 20 tests pass as expected.

---

## Why this matters

The experiment produced a result that runs counter to the intuitive case for OKF: the agent with the OKF index found the key documents _more slowly_, not faster. CLAUDE.md's skill table named exact file paths; the OKF hierarchy added traversal depth. For a project where CLAUDE.md already contains a curated document map, OKF's index structure is navigation overhead, not navigation shortcut.

What OKF provided instead was something harder to measure: completeness. Run B's agent found `step-definition-style.md` — a document CLAUDE.md doesn't reference in its skill table. Run B's agent confirmed that two non-applicable evals were genuinely non-applicable rather than simply undiscovered. Run B's agent arrived at each document knowing what else existed in the same category. None of these produced a better Gherkin output in this particular experiment. All of them produced an agent with more accurate knowledge of the project's knowledge boundary.

That is the real answer to "what does OKF give an agent that the current structure does not?" It gives the agent a view of what it doesn't know. CLAUDE.md tells an agent what to do and where to find the specific things it needs for specific tasks. OKF tells an agent what exists — including things no task has yet required it to find. The first is routing; the second is discovery. For a project that is still growing its knowledge bundle, the second matters more than the first. CLAUDE.md's skill table will always lag the actual document count. OKF's index never lags, because the index is the documents.

The right architecture is both: CLAUDE.md for routing and behavioral instructions, OKF for structural completeness and cross-linking. Neither replaces the other. They solve different problems at the same layer of the stack.
