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

- **WireMock-compatible stubs** for payment gateway and inventory service
- **Gherkin BDD test suite** (pytest-bdd) covering 5 core order scenarios
- **Pact contract tests** for both downstream dependencies, with provider verification
- **Bounded service specs** — notification service isolated in its own feature file
- **Four-job GitHub Actions CI/CD pipeline**: Gherkin → Pact consumer → Pact provider → can-i-deploy
- **Spec audit framework** — a reusable tool for diagnosing and classifying spec debt
- **Skills infrastructure** — structured skills with output contracts that replace ad-hoc prompts

The five Gherkin scenarios:

1. Happy path — payment accepted, all items in stock → `CONFIRMED`
2. Payment declined → `PAYMENT_FAILED` (402), inventory released
3. Out of stock → `UNAVAILABLE` (409), payment gateway never called
4. Partial availability → `PARTIAL_UNAVAILABLE` (207), no auto-confirm, payment never called
5. Payment timeout → `PAYMENT_PENDING` (202), inventory held 15 mins, max 2 retry attempts

Current state: **11 Gherkin tests passing, 4 Pact tests passing, all contracts verified.**

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
│   ├── main.py                          # FastAPI order service
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
│   │   └── inventory-partial.json
│   └── notification-mappings/           # Stub definitions for notification service (Issue #7)
│       ├── notification-success.json
│       └── notification-unavailable.json
├── tests/
│   ├── features/
│   │   ├── order_creation.feature       # Gherkin scenarios — order creation
│   │   ├── order_status_bad.feature     # Deliberately bad specs (Issue #5)
│   │   ├── order_status_good.feature    # Rewritten good specs (Issue #5)
│   │   └── notification_service.feature # Bounded notification spec (Issue #7)
│   ├── steps/
│   │   ├── conftest.py                  # Shared session-scoped server fixtures
│   │   ├── test_order_creation.py       # pytest-bdd step definitions
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
│   └── issue-09-skills-infrastructure.md
├── docs/
│   ├── spec-audit-framework.md          # Reusable spec audit framework (Issue #8)
│   ├── prompts/
│   │   └── prompt-gherkin-scenario-quality.md  # Raw prompt (before state, Issue #9)
│   └── skills/
│       └── gherkin-scenario-quality.md  # Structured skill (after state, Issue #9)
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

Issue #9 introduced the `docs/skills/` directory: structured artifacts that encode judgment into a format agents can route to consistently.

A skill differs from a prompt in three ways:
1. **Version control** — a skill lives in git, has a version history, and can be diffed. A prompt has no equivalent.
2. **Output contract** — a skill specifies exactly what the output must contain and what it must not. A prompt implies a format but never guarantees one.
3. **Routing signal** — a skill's description line is designed to route correctly. A prompt has no routing signal — the human must remember to use it.

`docs/skills/gherkin-scenario-quality.md` is the first skill. The "before" state (the raw prompt) is preserved at `docs/prompts/prompt-gherkin-scenario-quality.md`.

---

## Newsletter

**[The Level 5 Engineer](https://level5engineer.substack.com/)** — free, 22 issues planned across five layers: Specification (Issues 1–8, complete), Skills, Stewardship, and Synthesis.

If you found the repo useful, the newsletter is where the full context lives — the agent session transcripts, the honest failures, and the editorial reasoning behind each design decision.

---

_Repo current as of Issue #9._
