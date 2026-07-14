# Order Management API — The Level 5 Engineer

[![CI](https://github.com/kafka0nkoffee/lvl5engineer-order-api/actions/workflows/ci.yml/badge.svg)](https://github.com/kafka0nkoffee/lvl5engineer-order-api/actions/workflows/ci.yml)

> A Senior Software Engineer documenting a deliberate climb from Level 2 to Level 5 AI-native development. Specs, agents, stewardship. No hype. No hand-waving. Just the work.
>
> 📬 **Newsletter:** [level5engineer.substack.com](https://level5engineer.substack.com/)

---

## What this repo is

This is the working codebase behind [The Level 5 Engineer](https://level5engineer.substack.com/) — a learning-in-public newsletter tracing what it actually takes to move from AI-assisted coding (Level 2–3) to directing agents from specs (Level 5).

Every file in this repo was built by AI agents working from external Gherkin scenarios. The specs, the findings, and the editorial judgment are mine. The repo is itself a demonstration of the approach the newsletter describes.

**The core thesis:** AI hasn't removed the bottleneck in software development — it's moved it. The constraint is no longer implementation speed; it's specification quality. This codebase is the experiment that tests that claim.

---

## What's implemented

A FastAPI order management service, built entirely from Gherkin specs by Claude Code agents, with:

- **WireMock-compatible stubs** for payment gateway, inventory service, and notification service
- **Gherkin BDD test suite** (pytest-bdd) covering 5 order creation + 5 cancellation scenarios
- **Pact contract tests** for both downstream dependencies (4 interactions for inventory including release), with provider verification
- **Bounded service specs** — notification service isolated in its own feature file
- **Four-job GitHub Actions CI/CD pipeline**: Gherkin → Pact consumer → Pact provider → can-i-deploy
- **Spec audit framework** — a reusable tool for diagnosing and classifying spec debt
- **Skills infrastructure** — 3-tier skill architecture (org-wide, domain, personal) with output contracts

The order creation scenarios (POST /orders):

1. Happy path — payment accepted, all items in stock → `CONFIRMED`
2. Payment declined → `PAYMENT_FAILED` (402), inventory released
3. Out of stock → `UNAVAILABLE` (409), payment gateway never called
4. Partial availability → `PARTIAL_UNAVAILABLE` (207), no auto-confirm, payment never called
5. Payment timeout → `PAYMENT_PENDING` (202), inventory held 15 mins, max 2 retry attempts

The order cancellation scenarios (DELETE /orders/{order_id}):

1. Happy path — CONFIRMED order cancelled → `CANCELLED`, inventory released, notification sent
2. Idempotency — already-cancelled order → `CANCELLED` (200), no double-release
3. Not found → 404, inventory not touched
4. PAYMENT_PENDING order → 409, cannot cancel
5. PAYMENT_FAILED order → 409, cannot cancel

Current state: **16 Gherkin tests passing, 4 Pact tests passing, all contracts verified.**

---

## Why this might interest you

If you write Gherkin, design BDD frameworks, or work in test automation, Issues 4, 5, 7, and 8 are directly in your wheelhouse:

- **Issue 4** demonstrates why WireMock tests and Pact contract tests answer different questions — and what breaks when you assume they're equivalent
- **Issue 5** runs the same agent implementation twice — once from a vague spec, once from a precise one — and cross-runs each implementation against the other's tests to surface the divergence
- **Issue 7** shows what happens structurally when you let two services' scenarios share a feature file, and how to fix it
- **Issue 8** applies a six-class spec debt taxonomy to all four feature files and produces a reusable audit framework

---

## Project structure

```
order-api/
├── app/
│   ├── main.py                          # FastAPI order service (POST /orders + DELETE /orders/{id})
│   └── notification_service.py          # Notification endpoint (Issue #7)
├── mock_server.py                       # WireMock-compatible mock server
├── wiremock/
│   ├── payment-mappings/                # Stub definitions for payment gateway
│   │   ├── payment-success.json
│   │   ├── payment-declined.json
│   │   └── payment-timeout.json
│   ├── inventory-mappings/              # Stub definitions for inventory service
│   │   ├── inventory-all-available.json
│   │   ├── inventory-out-of-stock.json
│   │   ├── inventory-partial.json
│   │   ├── inventory-release-success.json      # Order cancellation release (Issue #19)
│   │   └── inventory-release-unavailable.json  # Release error scenario (Issue #19)
│   └── notification-mappings/           # Stub definitions for notification service (Issue #7)
│       ├── notification-success.json
│       └── notification-unavailable.json
├── tests/
│   ├── features/
│   │   ├── order_creation.feature       # Gherkin scenarios — order creation
│   │   ├── order_cancellation.feature   # Gherkin scenarios — order cancellation (Issue #19)
│   │   ├── order_status_bad.feature     # Deliberately bad specs (Issue #5)
│   │   ├── order_status_good.feature    # Rewritten good specs (Issue #5)
│   │   └── notification_service.feature # Bounded notification spec (Issue #7)
│   ├── steps/
│   │   ├── conftest.py                  # Shared session-scoped server fixtures + shared step definitions
│   │   ├── test_order_creation.py       # pytest-bdd step definitions
│   │   ├── test_order_cancellation.py   # Step definitions for cancellation (Issue #19)
│   │   ├── test_order_status_bad.py     # Steps for bad spec (Issue #5)
│   │   ├── test_order_status_good.py    # Steps for good spec (Issue #5)
│   │   └── test_notification_service.py # Steps for notification spec (Issue #7)
│   └── pact/
│       ├── test_payment_gateway_consumer.py   # Pact consumer tests (payment)
│       ├── test_inventory_service_consumer.py # Pact consumer tests (inventory)
│       └── test_provider_verification.py      # Pact provider verification
├── scripts/
│   └── can_i_deploy.py                  # Local can-i-deploy simulation
├── pacts/                               # Generated .pact files (gitignored)
├── .github/
│   └── workflows/
│       └── ci.yml                       # GitHub Actions pipeline (Issue #6)
├── findings/
│   ├── README.md                        # Index of all findings by issue
│   ├── issue-02-wiremock-gherkin.md
│   ├── issue-03-agent-fresh-implementation.md
│   ├── issue-04-pact-contract-testing.md
│   ├── issue-05-the-spec-that-doesnt-lie.md
│   ├── issue-06-cicd-guardrails.md
│   ├── issue-07-scope-problem.md
│   ├── issue-08-spec-audit.md
│   ├── issue-09-skills-infrastructure.md
│   ├── issue-10-three-tier-architecture.md
│   ├── issue-11-non-human-callers.md
│   ├── issue-12-skill-review.md
│   ├── issue-13-skill-audit.md
│   ├── issue-14-memory-wall.md
│   ├── issue-15-claude-md.md
│   ├── issue-16-adrs.md
│   ├── issue-17-evals.md
│   └── issue-18-runbooks.md
├── docs/
│   ├── spec-audit-framework.md          # Reusable spec audit framework (Issue #8)
│   ├── skill-review-checklist.md        # Five-dimension skill review checklist (Issue #12)
│   ├── skill-pr-template.md             # PR template for skill version control (Issue #12)
│   ├── skill-audit-template.md          # Reusable prompt library audit template (Issue #13)
│   ├── layer3-artifact-map.md           # Failure mode → artifact type map (Issue #14)
│   ├── ADR/                            # Architecture Decision Records (Issue #16)
│   │   ├── ADR-001-inventory-before-payment.md
│   │   └── ADR-002-fire-and-forget-notification.md
│   ├── evals/                          # Pre-flight evals (Issue #17)
│   │   ├── eval-environment.md
│   │   ├── eval-operation-scope.md
│   │   └── eval-contract-preflight.md
│   └── runbooks/                       # Incident runbooks (Issue #18)
│       ├── payment-gateway-degraded-human.md
│       └── payment-gateway-degraded-agent.md
│   ├── claude-md-versions/             # Naive/better/production-grade comparison (Issue #15)
│   │   ├── naive.md
│   │   ├── better.md
│   │   └── production-grade.md
│   ├── prompts/
│   │   └── prompt-gherkin-scenario-quality.md  # Raw prompt (before state, Issue #9)
│   └── skills/
│       ├── tier1/
│       │   └── output-formatting-standard.md   # Org-wide formatting standard (Issue #10)
│       ├── tier2/
│       │   ├── gherkin-scenario-quality.md     # DEPRECATED — use v2 (Issue #13)
│       │   ├── gherkin-scenario-quality-v2.md  # Agent-safe v2 with four guards (Issue #11)
│       │   ├── session-start-protocol.md       # Session initialization protocol (Issue #13)
│       │   ├── feature-file-audit.md           # Spec debt audit skill (Issue #13)
│       │   └── step-definition-style.md        # pytest-bdd step conventions (Issue #13)
│       └── tier3/
│           └── why-this-matters-writing.md     # Personal workflow: findings paragraphs (Issue #10)
├── CLAUDE.md                            # Agent standing orders
└── pytest.ini
```

---

## Quick start (macOS)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full Gherkin test suite
pytest tests/steps/test_order_creation.py -v

# 3. Run Pact consumer tests (generates pacts/ directory)
pytest tests/pact/test_payment_gateway_consumer.py tests/pact/test_inventory_service_consumer.py -v

# 4. Run Pact provider verification
pytest tests/pact/test_provider_verification.py -v -s

# 5. Run the local can-i-deploy check
python scripts/can_i_deploy.py
```

The test harness spins up the Python mock servers automatically on ports 8091/8092 and the FastAPI app on 8093. No manual setup needed.

### Using real WireMock (optional)

The stub JSON files in `wiremock/` are standard WireMock mapping format:

```bash
# https://repo1.maven.org/maven2/org/wiremock/wiremock-standalone/3.3.1/
java -jar wiremock.jar --port 8091 --root-dir wiremock/payment-mappings
java -jar wiremock.jar --port 8092 --root-dir wiremock/inventory-mappings
uvicorn app.main:app --port 8093
```

---

## Findings log — what each issue built and learned

Each newsletter issue has a corresponding findings file documenting what the agent tried, what failed, the root causes, and why it matters. See [`findings/README.md`](./findings/README.md) for the full index.

| Issue                                                                              | What was built                                               | Key finding                                                                                                                                                                                       |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [#2 — Gherkin + WireMock](findings/issue-02-wiremock-gherkin.md)                   | First implementation from spec; 5 order scenarios            | Writing the spec forces you to define the contract before the code                                                                                                                                |
| [#3 — Agent fresh implementation](findings/issue-03-agent-fresh-implementation.md) | Full rebuild from Gherkin only, no prior code                | Agent derived correct timeout/retry logic from spec alone; found a portability bug in the original test harness                                                                                   |
| [#4 — Pact contract testing](findings/issue-04-pact-contract-testing.md)           | Pact consumer tests + provider verification + can-i-deploy   | Renamed `status` → `result` in stub: Pact caught it immediately, Gherkin reported 5/5 passing. They answer different questions.                                                                   |
| [#5 — The spec that doesn't lie](findings/issue-05-the-spec-that-doesnt-lie.md)    | Bad Gherkin vs good Gherkin; agent builds both               | Cross-running implementations revealed `db_status` field leak and 404 body divergence. Passing tests are necessary but not sufficient.                                                            |
| [#6 — CI/CD guardrails](findings/issue-06-cicd-guardrails.md)                      | Four-job GitHub Actions pipeline                             | Deliberate breaking change test: Gherkin passed, Pact caught the drift. That's the whole point of having both.                                                                                    |
| [#7 — The scope problem](findings/issue-07-scope-problem.md)                       | Notification service; bounded feature files; spec debt audit | Mixing two services' scenarios in one file creates four structural problems. Seven spec debt items named and documented.                                                                          |
| [#8 — Spec audit](findings/issue-08-spec-audit.md)                                 | Fixed all 7 debt items; produced reusable audit framework    | Six-class debt taxonomy (UNDERSPECIFIED, MIXED CONCERN, UNDEFINED TERM, AMBIGUOUS COUNT, IMPLICIT FLOW, LEAKY ABSTRACTION). Residual debt: 0.22 items/scenario — both documented, neither silent. |
| [#9 — Skills infrastructure](findings/issue-09-skills-infrastructure.md)           | Converted best reused prompt into a structured skill         | Same input, prompt version → 6 implicit decisions; skill version → 2 (both surfaced explicitly). The prompt produces output that passes today's tests; the skill produces output a different agent can implement tomorrow without making decisions you didn't make. |
| [#10 — 3-tier architecture](findings/issue-10-three-tier-architecture.md)          | Mapped project to 3-tier model; built skills at all three tiers | The most dangerous institutional knowledge looks like a standard — it produces consistent output — but only because the person holding the pattern hasn't left yet. A Tier 3 skill that should be Tier 2 is invisible until the session that exposes it. |
| [#11 — Non-human callers](findings/issue-11-non-human-callers.md)                  | Stress-tested Gherkin skill v1.1; built agent-safe v2 with four guards | A human-friendly skill is dangerous at agent scale not because it produces wrong output — it produces output that looks indistinguishably right — but because it always gives you something useful and never tells you when useful is the wrong thing to give. |
| [#12 — Skill review](findings/issue-12-skill-review.md)                             | Built five-dimension skill review framework; applied it to v1.1 and v2.0 | Stress tests prove a skill works when called. Review proves the skill is ready to be called. Both descriptions exceed 120 characters in the routing signal — a finding that behavioral stress testing cannot reach. |
| [#13 — Skill audit](findings/issue-13-skill-audit.md)                               | Full prompt library inventory; three skill conversions; reusable audit template | Five step definition conventions followed across twelve issues were never written down. The audit found them, named them, and converted them to a skill in the final session of Layer 2. |
| [#14 — Memory wall](findings/issue-14-memory-wall.md)                               | Agent failure taxonomy; Layer 3 artifact map; project exposure assessment | Agents operating on systems with real history fail in four specific, nameable ways — and none of the four are prevented by the spec or skill layers alone. Layer 3 is the infrastructure for what must not change. |
| [#15 — Production-grade CLAUDE.md](findings/issue-15-claude-md.md)                  | Three CLAUDE.md versions built and compared; root CLAUDE.md upgraded | The gap between "works without catastrophic failures" and "production-grade" is not about volume — it's about the difference between describing current behavior and constraining future behavior. |
| [#16 — Architecture Decision Records](findings/issue-16-adrs.md)                     | ADR-001 and ADR-002 built; dangerous improvement demonstrated and reverted | A human-facing ADR documents the past. An agent-readable ADR constrains the future. The dangerous improvements section is the structural difference. |
| [#17 — Evals as guardrails](findings/issue-17-evals.md)                               | Three pre-flight evals built; four task demonstrations run | The most dangerous change in this session passes all 15 tests. Task 4 (synchronous notification) would cause a complete order processing outage on the first notification service incident — and no behavioral test asserts asynchrony. The eval is the only protection. |
| [#18 — Runbooks as infrastructure](findings/issue-18-runbooks.md)                     | Two runbook formats compared; dry run executed; one gap found and fixed | "Consider adjusting the timeout if the gateway is slow" is the instruction that earns Issue #18. An agent increases PAYMENT_TIMEOUT_SECONDS above the stub delay, changes the code path from TimeoutException to response handling, breaks Scenario 5, and closes the incident as resolved. The human-facing runbook enables this. The agent-facing runbook prevents it. |
| [#19 — Full stack assembly](findings/issue-19-full-stack.md)                           | Order cancellation built end-to-end using all three layers simultaneously | The Gherkin quality skill caught 10 UNDERSPECIFIED items before implementation — including the `"is released"` pattern that would have produced another `inventory_released: true` flag (the same gap Issue #8 found). ADR-002 extended the fire-and-forget invariant to a new code path no existing test covers. Two implicit decisions survived all three layers: inventory release body format and test state seeding. Both are in the API-design layer below behavioral specs and above code. |

---

## The spec audit framework

`docs/spec-audit-framework.md` is a standalone tool for auditing any Gherkin feature file. It includes:

- Five diagnostic questions
- Six-class spec debt taxonomy with definitions and examples
- Fix rubric for each debt class
- Scorecard template

Produced during Issue #8 and applied immediately to all four feature files in this repo.

---

## Skills — encoding judgment for agents

Issue #9 introduced the `docs/skills/` directory. Issue #10 organized it into a 3-tier architecture.

**Tier 1 — Org-wide standards** apply to every agent in every session, regardless of domain. `docs/skills/tier1/output-formatting-standard.md` governs all formatting: findings file structure, commit message format, Gherkin indentation, code snippet conventions.

**Tier 2 — Domain methodology** encodes senior practitioner expertise specific to this project. `docs/skills/tier2/gherkin-scenario-quality-v2.md` is the current version — stress-tested in Issue #11 against adversarial inputs and reinforced with four pre-flight guards (empty input, domain check, contradiction halt, idempotency). v1.1 is preserved at `gherkin-scenario-quality.md` for reference.

**Tier 3 — Personal workflow** captures individual patterns that should be documented and shared but are not yet universal standards. `docs/skills/tier3/why-this-matters-writing.md` encodes the four-component structure for findings paragraphs, with a documented decision to promote it to Tier 2.

A skill differs from a prompt in three ways: version control (a skill has a diff; a prompt doesn't), output contract (a skill specifies exactly what to produce), and routing signal (a skill's description line is designed for agent routing; a prompt must be remembered and pasted).

The "before" state of the first skill is preserved at `docs/prompts/prompt-gherkin-scenario-quality.md`.

---

## Layer 2 complete — Skills infrastructure

Issues #9–13 built a complete skills infrastructure on top of the Specification layer from
Issues #1–8.

**What Layer 2 produced:**

| Artifact | Location | Issue |
|---|---|---|
| Gherkin quality skill v1.1 | `docs/skills/tier2/gherkin-scenario-quality.md` *(deprecated)* | #9 |
| Output formatting standard | `docs/skills/tier1/output-formatting-standard.md` | #10 |
| "Why this matters" writing skill | `docs/skills/tier3/why-this-matters-writing.md` | #10 |
| Gherkin quality skill v2.0 (agent-safe) | `docs/skills/tier2/gherkin-scenario-quality-v2.md` | #11 |
| Five-dimension skill review checklist | `docs/skill-review-checklist.md` | #12 |
| Skill PR template | `docs/skill-pr-template.md` | #12 |
| Session start protocol | `docs/skills/tier2/session-start-protocol.md` | #13 |
| Feature file audit skill | `docs/skills/tier2/feature-file-audit.md` | #13 |
| Step definition style skill | `docs/skills/tier2/step-definition-style.md` | #13 |
| Prompt library audit template | `docs/skill-audit-template.md` | #13 |

**What changed:** Before Issue #9, one pasted prompt governed Gherkin quality and everything
else relied on CLAUDE.md prose or agent inference. After Issue #13: six active skills across
three tiers, a review process for new skills, and an audit template that generalizes to any
project.

**What Layer 3 inherits:** An undocumented implementation layer (app/main.py conventions),
one skill with an open comment (step-definition-style v1.0 helper extraction), and
why-this-matters-writing.md at Tier 3 pending its documented promotion criteria.

---

## Layer 3 begins — Stewardship Infrastructure

Issue #14 opens the third layer with a research and documentation session. No new implementation. The deliverable is a concrete taxonomy of agent failure modes and a map of the artifacts that prevent them.

**What Layer 3 asks:** What happens when agents operate in systems with real history — decisions made years ago, undocumented invariants, production environments that look identical to staging until they aren't? The spec layer tells agents what to build. The skill layer tells agents how to reason. Neither answers: what must never change, what happened before the agent arrived, or which external systems it is silently affecting.

**The four failure modes (Issue #14):**

| Failure mode | Definition | Artifact that prevents it |
|---|---|---|
| Production blindness | Agent cannot distinguish production from non-production resources | Environment discrimination in CLAUDE.md |
| Historical amnesia | Agent cannot access decisions made before the current session | Architecture Decision Records |
| Dependency ignorance | Agent does not know what external systems it is affecting | Dependency map + external service contracts |
| Invariant blindness | Agent does not know which properties must remain true | Invariant documentation + Evals |

**Project-specific exposure:** All four failure modes applied to this project as of Issue #13. The findings files were too narrative to be queryable. The skills governed how agents produced output but not what they must not change. The Gherkin spec constrained behavior but not implementation structure. See `docs/layer3-artifact-map.md` for the build plan.

**Issue #15 — Production-grade CLAUDE.md:** Built three versions of CLAUDE.md (naive, better, production-grade) as a comparison artifact. Replaced the root `CLAUDE.md` with the production-grade version, which adds five required sections: project scope boundaries, environment discrimination, architectural invariants, external service contracts, and a decision index. The production-grade version passes all four failure mode tests; the naive version fails all four; the better version fails one (invariant blindness). See `findings/issue-15-claude-md.md` and `docs/claude-md-versions/` for the full comparison.

**Issue #16 — Architecture Decision Records:** Built `docs/ADR/ADR-001-inventory-before-payment.md` and `docs/ADR/ADR-002-fire-and-forget-notification.md`. Each ADR adds four agent-specific sections beyond the standard format: invariant statement, dangerous improvements list, agent check questions (yes/no, answerable from code), and a consequence table mapping test outcomes to specific violations. The session demonstrated the dangerous improvement live: implemented a concurrent inventory+payment refactor, ran tests (2 of 5 failed on "payment gateway is never called"), documented which ADR check question would have caught it before implementation, then reverted. The key finding: the test caught the violation because the spec was written to catch it — and the ADR explains why the spec was written that way, which prevents the violation from being reattempted in every future session framed as a performance task. Updated CLAUDE.md decision index with actual ADR file paths and a mandatory pre-flight protocol.

**Issue #17 — Evals as guardrails:** Built three pre-flight evals: `docs/evals/eval-environment.md` (fires before touching infrastructure files — `ci.yml`, `CLAUDE.md`, skill files, ADRs), `docs/evals/eval-operation-scope.md` (fires before touching `app/main.py` or `tests/`), and `docs/evals/eval-contract-preflight.md` (fires before touching `wiremock/` stubs or `pacts/`). The session ran all three evals against four task descriptions and documented which question fires, what the agent is instructed to do, and whether each task would have caused a production failure without the eval. Key finding: Task 4 (making the notification call synchronous) passes all 15 tests, looks like an improvement, and causes a complete order processing outage on the first notification service incident. No behavioral test asserts that the notification call is asynchronous — the eval is the only protection. Added the "Pre-flight evals" section to CLAUDE.md with the action-to-eval mapping table.

**Issue #18 — Runbooks as infrastructure:** Built two versions of the same payment gateway degradation runbook — human-facing (`docs/runbooks/payment-gateway-degraded-human.md`) and agent-facing (`docs/runbooks/payment-gateway-degraded-agent.md`). The human-facing version is realistic and good — the kind a competent on-call engineer would write and follow. The five judgment calls identified in it are invisible to a human operator because they are automatically filled in by context the human carries. They are not invisible to an agent. The critical judgment call: "Consider adjusting the timeout configuration if the gateway is responding slowly." An agent increases `PAYMENT_TIMEOUT_SECONDS` to 7 (above the stub's 6000ms delay), the stub responds before the client times out, the code returns `PAYMENT_FAILED` instead of `PAYMENT_PENDING`, Scenario 5 fails, and the agent closes the incident as resolved. The agent-facing runbook prevents this with an explicit worst-case latency formula and a verification step that catches the broken code path before the incident is closed. Dry run was actually executed — one gap found: `-k timeout` selects 0 tests (test name uses "times_out"). Fixed in the runbook.

**Issue #19 — Full stack assembly:** Built order cancellation (`DELETE /orders/{order_id}`) end-to-end using all three layers simultaneously. The Gherkin quality skill applied to first-draft scenarios caught 10 UNDERSPECIFIED items — including `"the inventory reservation is released"` (which would have become `inventory_released: true` in the response body again, repeating the Issue #8 gap) and `"an appropriate error"` (which would have left the 404 vs 409 decision to the agent). ADR-002 extended the fire-and-forget invariant to the new cancellation notification path, catching an invariant violation that no behavioral test covers. Two implicit decisions survived all three layers: the inventory release request body format and the test state seeding approach. These live in the API-design layer — below behavioral specification, above code — which the current three-layer infrastructure does not yet reach. The step-definition-style skill identified the correct shared-step pattern but was not consulted at the exact moment it was needed; the first test run failed on `StepDefinitionNotFoundError` and the second (after re-reading the skill) passed 16/16. See `findings/issue-19-full-stack.md`.

---

## Skill review framework

Issue #12 built the review process that should precede every skill version bump. Two documents:

**`docs/skill-review-checklist.md`** — a five-dimension checklist that a reviewer must work
through before approving a new skill version. The five dimensions are:

1. **Routing signal** — Is the description ≤ 120 characters? Does it name the artifact type,
   domain scope, and methodology?
2. **Output contract** — Is every requirement enumerable? Can two agents produce different
   outputs that both satisfy it? Are absence requirements listed?
3. **Methodology** — Does it describe reasoning or just procedure? Does it generalize to
   edge cases not in the examples?
4. **Idempotency** — Does the skill produce the same output for the same input? Does it
   return already-correct input unchanged?
5. **Failure modes** — Are all out-of-scope, contradictory, and empty inputs handled with
   FAIL SIGNAL or CORRECT REFUSAL, not PLAUSIBLE WRONG output?

**`docs/skill-pr-template.md`** — a PR template for version-controlled skill repositories,
with a summary, a behavioral diff (what the previous version did vs. this version), a
reviewer checklist mapping to the five dimensions, and a sign-off section.

Applied retrospectively to both v1.1 and v2.0 of the Gherkin quality skill:

- **v1.1 verdict: CHANGES REQUESTED.** The review would have caught all three v2.0 failure
  modes (idempotency, UI translation, contradiction handling) before the stress tests ran.
- **v2.0 verdict: APPROVED WITH COMMENTS.** The four guards are correctly implemented, but
  the routing signal exceeds 120 characters (both versions), Guard 4 has a return value
  ambiguity for pipeline consumers, and Guard 4 passes scenarios with missing Q5 side-effect
  assertions. These are documented as findings for v2.1.

The key finding: both routing signals are over the 120-character limit. This is not catchable
by behavioral stress tests, which test the skill when invoked — not whether the skill gets
invoked. See `findings/issue-12-skill-review.md`.

---

## Newsletter

**[The Level 5 Engineer](https://level5engineer.substack.com/)** — free, 22 issues planned across five layers: Specification (Issues 1–8, complete), Skills, Stewardship, and Synthesis.

If you found the repo useful, the newsletter is where the full context lives — the agent session transcripts, the honest failures, and the editorial reasoning behind each design decision.

---

_Repo current as of Issue #19 — Order cancellation built end-to-end using all three layers simultaneously._
