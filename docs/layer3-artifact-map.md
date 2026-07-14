---
type: Reference
title: "Layer 3 Artifact Map"
description: "Maps the four agent failure modes from Issue #14 to the five artifact types built in Issues #15–18."
tags: [reference, layer-3, failure-modes, artifact-map]
timestamp: 2026-07-05
---

# Layer 3 Artifact Map

**Layer:** 3 — Stewardship Infrastructure
**Status:** Reference document — map for Issues #15–18
**Created:** 2026-07-05 (Issue #14)

This document maps the four agent failure modes identified in Issue #14 to the five artifact types that Layer 3 will build. It is a navigation aid, not a skill. Read it before starting any Issue #15–18 session to understand which failure mode the session targets and why the artifact type was chosen.

---

## The four failure modes

| # | Name | What it is |
|---|---|---|
| 1 | Production blindness | The agent cannot distinguish production from non-production resources |
| 2 | Historical amnesia | The agent cannot access decisions made before the current session |
| 3 | Dependency ignorance | The agent does not know what external systems it is affecting |
| 4 | Invariant blindness | The agent does not know which properties must remain true across all changes |

---

## The five artifact types

| Failure Mode | Layer 3 Artifact | Issues |
|---|---|---|
| Production blindness | Environment discrimination in CLAUDE.md | #15 |
| Historical amnesia | Architecture Decision Records | #16 |
| Dependency ignorance | Dependency map + external service contracts | #15, #16 |
| Invariant blindness | Invariant documentation + Evals as guardrails | #17 |
| All four | Runbooks with explicit decision trees | #18 |

---

## Artifact descriptions

### Environment discrimination (Issue #15)

**What it is:** A dedicated section in `CLAUDE.md` — or a separate `ENVIRONMENTS.md` linked from it — that explicitly names each environment the agent may operate in, describes what distinguishes production resources from non-production resources, and states the rule for what the agent may and may not modify in each.

**What it contains:** A list of named environments (CI, local dev, staging if applicable), the resources that exist in each, which resources are shared across environments (and therefore carry production risk even in development), and an explicit protocol for any action that affects a shared resource. For this project: the `main` branch as production-equivalent, the CI pipeline as a shared gate, the `pacts/` directory as derived-not-editable.

**Why it prevents production blindness:** An agent cannot infer environment boundaries from code structure or naming conventions. Configuration values differ across environments, but the agent does not know which values correspond to which risk level unless told explicitly. This document makes the boundary explicit and machine-readable, so the agent can apply it without inferring it.

---

### Architecture Decision Records (Issue #16)

**What it is:** A set of short documents in an `ADR/` directory, one per significant architectural decision, following a consistent format: context, decision, consequences, and an agent-readable "Do not reverse without reading" section that names the downstream consequences of undoing the decision.

**What it contains:** For this project: the fire-and-forget notification design (notification failure must not block order confirmation), the inventory-before-payment call ordering (payment gateway must never be called for out-of-stock items), the mock server lifecycle ownership (session fixtures own server startup, not CI YAML), the two-attempt payment retry cap (2 total attempts, not 2 retries on top of the first), and the Pact contract as the authoritative enforcement mechanism for API shape.

**Why it prevents historical amnesia:** Decisions accumulate in systems in non-queryable forms — commit messages, Slack threads, post-mortem reports, oral tradition. An ADR makes a decision queryable: it is in the repository, it follows a consistent format, and an agent can be instructed to read it before modifying a relevant code path. The agent does not need to re-derive the decision; it can read the reasoning directly.

---

### Dependency map + external service contracts (Issues #15, #16)

**What it is:** A section in `CLAUDE.md` or a dedicated `docs/dependencies.md` that states for each external service: what the order service sends to it, what it must receive back (with load-bearing fields distinguished from informational fields), which failure modes the order service handles, which failure modes it intentionally does not handle, and which design decisions were made specifically because of that dependency's behavior.

**What it contains:** For this project: the payment gateway contract (fields sent, fields required in response, retry behavior and why it is capped at 2 total attempts), the inventory service contract (fields sent, field meanings, what "partial" means to the order service), the notification service contract (fire-and-forget protocol, exception handling, why success is not verified), and the Pact contract's role as governance mechanism (the Pact contract is not a test — it is a binding agreement; changing it requires consumer consent).

**Why it prevents dependency ignorance:** Dependency contracts exist in the consuming systems, not the producing system. An agent modifying the producing system cannot discover consumer expectations from the code — the code shows the calls but not the contracts. This document surfaces the contracts into the context of the agent making the change, making the dependency relationships explicit before any action is taken.

---

### Invariant documentation + Evals as guardrails (Issue #17)

**What it is:** A short `docs/invariants.md` listing the implementation constraints that must survive all future changes, in a structured format that an agent can be instructed to read before making any change to core service behavior. Paired with eval scripts that test for invariant violations in a way that complements (but does not replace) the behavioral Gherkin specs.

**What it contains:** For this project: numbered invariants stating properties of the implementation that must not change, the consequence of violating each, and how each is currently enforced. Examples: "Inventory must be checked before the payment gateway is called — violating this results in payment charges for unfulfillable orders." "The notification call must remain asynchronous — synchronous notification delivery couples order confirmation latency to notification service availability." "The Pact consumer tests must not be modified to accommodate a change in the provider — the flow is always: change the provider, run the consumer tests, fix the provider if they fail."

**Why it prevents invariant blindness:** The Gherkin spec tests behavioral output; it does not constrain implementation structure. An agent can satisfy every Gherkin scenario while violating an implementation invariant — by reordering calls, by changing the synchrony of a call, by removing a guard that has no corresponding assertion. Invariant documentation states constraints on the implementation, not the output. Evals add executable verification that catches invariant violations the behavioral spec cannot reach.

---

### Runbooks with explicit decision trees (Issue #18)

**What it is:** Operational documents that describe how to perform specific actions in this system — deploying, rolling back, adding a new external dependency, changing an API contract — as step-by-step decision trees that an agent can follow without requiring context that is not present in the runbook.

**What it contains:** Decision trees, not prose instructions. Each step has an explicit branch: "If X, do Y; if Z, do W." The decision trees encode the institutional knowledge that currently lives in convention and experience. For this project: the protocol for introducing a new external service dependency (add to dependency map, write consumer Pact test, add to CLAUDE.md, write ADR), the protocol for changing an API response shape (check Pact contracts first, version the change if consumers exist, run full suite before committing), and the protocol for any change to `ci.yml` (test locally first, confirm all jobs pass, confirm branch protection rules are enforced before merging).

**Why it prevents all four failure modes:** Runbooks are the intersection of the other four artifacts. A well-written runbook references the environment discrimination document (which environment does this action affect?), the ADRs (what decisions constrain this action?), the dependency map (what external systems are affected?), and the invariant documentation (what must remain true after this action?). A runbook that does not reference all four is incomplete. This is also why it comes last in the build order — it can only be written after the artifacts it references exist.

---

## Build order rationale

Issue #15 comes before #16 because environment discrimination and the dependency map are prerequisites for ADRs — you cannot write an ADR for the fire-and-forget notification design without first having a document that states the notification service is a dependency and what its contract is. Issue #17 (invariants + evals) comes after the ADRs because the invariants to document become clear only after the ADR process surfaces which design decisions are most frequently at risk of silent reversal. Issue #18 (runbooks) comes last because runbooks are assemblies of all the prior artifacts — they reference environments, decisions, dependencies, and invariants. A runbook written before those artifacts exist is just a prose checklist, not a decision tree.

---

_This document is a map, not a spec. The issues it references will modify the map as they are built. Update the Issues column when any issue is complete._
