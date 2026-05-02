# CLAUDE.md

> This file is read automatically by Claude Code at the start of every session.
> It defines how the agent should behave, what it should never touch, and how
> it should document its work for the Level 5 Engineer newsletter.

---

## What this project is

This repository is the living codebase behind **The Level 5 Engineer** — a newsletter
documenting a Senior Engineer's climb from Level 2 to Level 5 AI-native development.

Every piece of code here is built by an AI agent working from external behavioural
specifications (Gherkin scenarios) that the agent cannot modify. The agent's job is
to make those scenarios pass. The human's job is to write the scenarios, review the
outcomes, and document the findings.

This is not a tutorial codebase. It is a real working system being built in public,
issue by issue, as a learning artifact.

---

## Architecture overview

```
order-api/
├── app/main.py                         # FastAPI order management service
├── mock_server.py                      # WireMock-compatible mock server (Python)
├── wiremock/
│   ├── payment-mappings/               # Stubs for payment gateway (WireMock format)
│   └── inventory-mappings/             # Stubs for inventory service (WireMock format)
├── tests/
│   ├── features/                       # Gherkin scenarios — the external spec
│   └── steps/                          # pytest-bdd step definitions
├── findings/
│   ├── README.md                       # Index of all findings files
│   └── issue-{N}-{topic}.md           # One file per newsletter issue/session
├── requirements.txt
└── CLAUDE.md                           # You are here
```

---

## What you can and cannot do

### ✅ You may

- Modify `app/main.py` and `mock_server.py` freely
- Add new WireMock stub mappings in `wiremock/payment-mappings/` or `wiremock/inventory-mappings/`
- Add new step definitions in `tests/steps/`
- Add new source files in `app/`
- Install new packages via pip and update `requirements.txt`
- Create new test feature files in `tests/features/`

### ❌ You may not

- Modify existing `.feature` files in `tests/features/` — these are the external
  behavioural spec written by the human. They define what the system must do.
  The agent's job is to satisfy them, not rewrite them.
- Delete or rename existing passing tests
- Modify `CLAUDE.md` unless explicitly instructed to do so by the human

---

## External dependencies

| Service           | Simulated by              | Port | Mapping dir                    |
| ----------------- | ------------------------- | ---- | ------------------------------ |
| Payment Gateway   | WireMock / mock_server.py | 8091 | `wiremock/payment-mappings/`   |
| Inventory Service | WireMock / mock_server.py | 8092 | `wiremock/inventory-mappings/` |
| Order API         | FastAPI / uvicorn         | 8093 | `app/main.py`                  |

**Important:** The mock servers simulate real external services. Do not make real
HTTP calls to external services during testing. All integration work happens
against the stubs.

---

## Running the test suite

```bash
# Install dependencies
pip install -r requirements.txt

# Run all scenarios
pytest tests/steps/test_order_creation.py -v

# Run a specific scenario
pytest tests/steps/test_order_creation.py -v -k "timeout"
```

All 5 scenarios must pass before any work is considered complete.

---

## Documentation protocol — findings/

This is the most important instruction in this file.

**At the start of every session, create a new file in `findings/` named:**

```
findings/issue-{N}-{short-topic}.md
```

For example: `findings/issue-04-pact-contract-testing.md`

Do not append to existing findings files. Each session gets its own file.
Do not summarise at the end of a session. Write findings as you encounter them.

**After creating the file, add a row to `findings/README.md`:**

```markdown
| #N | Short topic description | [findings/issue-N-topic.md](findings/issue-N-topic.md) |
```

**Also update the root `README.md`:**

- Change the `_Repo up to date with Issue #N_` line to the current issue number
- Add the new findings file to the project structure tree
- Add a new section describing what changed this session, linking to the findings file
- Keep the README accurate — it is the first thing a reader sees on GitHub

The README is a public-facing document. Write updates to it as a practitioner
summarising work for a peer, not as a changelog entry.

Use the following structure for each entry within the findings file:

```markdown
## [Short title of what was attempted]

**Date:** YYYY-MM-DD
**Status:** ✅ Worked | ❌ Failed | ⚠️ Partial

### What I tried

[What was attempted and why]

### What happened

[Exact output, error messages, unexpected behaviour]

### Root cause

[Why it happened — be specific, not vague]

### The fix

[What changed and why it worked]

### Why this matters

[One paragraph written as if explaining to a senior engineer
who hasn't seen this codebase. This paragraph will be used
directly in the newsletter. Make it honest, specific, and
free of jargon where possible.]
```

The "Why this matters" paragraph is the most important part. It is the raw
material for the newsletter. Write it as a practitioner reflecting on a real
finding — not as documentation for a codebase.

---

## Commit conventions

```
feat: add Pact consumer test for payment service
fix: handle 404 passthrough from payment mock
test: add scenario for concurrent order requests
docs: add findings/issue-04-pact-contract-testing.md
chore: update requirements.txt
```

Commit after every meaningful unit of work. Do not batch unrelated changes
into a single commit.

---

## Newsletter context

The human author of this newsletter is:

- A Senior Software Engineer with 10+ years of experience
- Currently at Level 2–3 on the AI-native development ladder
- Documenting the climb to Level 5 in public, in real time
- Writing for an audience of engineers who are curious but haven't yet made the leap

When writing `FINDINGS.md`, keep this audience in mind. The reader is a peer,
not a student. Be direct. Don't over-explain. Don't under-explain failures.
