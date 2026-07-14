---
type: Reference
title: "Spec Audit Framework"
description: "Structured tool for finding spec debt in Gherkin feature files before it causes production incidents."
tags: [reference, spec-audit, gherkin, spec-debt]
timestamp: 2026-06-16
---

# Spec Audit Framework

A structured tool for finding spec debt in Gherkin feature files before it causes production incidents.

This document is standalone — you do not need to read any other document to use it. Apply it to any feature file you own.

---

## What is spec debt?

Spec debt is a step in a feature file that passes its tests but leaves a decision open for the implementer. Unlike code debt, spec debt is invisible in a green CI run. It surfaces as an incompatible implementation: two agents (or two engineers, or one engineer six months apart) read the same step and build different things. Both pass the tests. One causes a production incident.

The framework below gives you five questions and a classification taxonomy to find spec debt systematically — not by intuition, but by method.

---

## Section 1 — The Five Questions

Apply these five questions to **every scenario** in **every feature file** you own.

---

### Q1: Who owns this scenario?

Can you name the team, service, or domain this scenario belongs to? Write the owner's name in the margin. If the answer includes "and also" — if the scenario tests two services, or two domains, or two concerns — the scenario is in the wrong file.

A feature file is a contract for one service. It should be possible to hand the file to the team that owns that service and have them understand it without reading any other file.

**What to look for:**
- A Given clause that references a service different from the one the feature file is named after
- A Then clause that asserts behavior in a service that is not the subject of the When clause
- A step that only makes sense if you know the internal architecture of a different team's service

**Example (debt):**
```gherkin
Feature: Order Creation
  ...
  Scenario: Notification is sent when order is confirmed
    # This scenario belongs to the notification service team, not the order team.
    # It is in the wrong file.
```

**Example (clean):**
```gherkin
Feature: Notification Service
  Scenario: Notification is queued when a confirmed order is received
    # Owner: notification service team. Clear.
```

---

### Q2: What decisions does this scenario leave open?

List every Given, When, and Then clause. For each one, ask: **what would a second agent build from this step that is different from what the first agent built, and would both pass?**

If the answer is "yes, different implementations could pass this step", the step is underspecified.

Common forms of underspecification:
- A quantity without a unit or an upper/lower bound ("within a reasonable time")
- A count that could be read as "total" or "additional" ("not retried more than 2 times")
- A status word that covers multiple mechanisms ("the reservation is released")
- A correctness claim without a reference value ("the notification contains the correct total")

**What to look for:**
- Adjectives like "correct", "valid", "appropriate", "reasonable"
- Counts without "total" or "exactly" ("called 2 times")
- Relative time bounds without a start anchor ("within 12 seconds")
- Mechanism claims without the mechanism ("is released", "is notified", "is confirmed")

**Example (debt):**
```gherkin
And the response is returned within 12 seconds
```
Two valid implementations: measure from client request submission, or from the last retry attempt. Different numbers under network load.

**Example (clean):**
```gherkin
And the response is returned within 12 seconds of the order being submitted
```

---

### Q3: Are all terms defined within the file?

Every noun in the scenario that is not a standard HTTP concept (request, response, status code, body) or a primitive type (string, integer, boolean) should be defined either in the scenario itself or in a Background clause.

If a term requires reading another file, asking a colleague, or domain knowledge that is not written down anywhere in the project, it is spec debt.

**What to look for:**
- Domain-specific nouns that appear without definition ("the reservation", "the confirmation flow")
- States that are implied but not established ("an unavailable service" — unavailable how?)
- Terms that have multiple meanings in the codebase ("confirmed" could mean payment confirmed, order confirmed, or notification confirmed)

**Example (debt):**
```gherkin
Given the notification service is unavailable
```
"Unavailable" is undefined. TCP refused? 503? 200 with malformed body? A 30-second hang? Each is a distinct failure mode.

**Example (clean):**
```gherkin
Given the notification service will respond with 503 Service Unavailable
```

---

### Q4: Does this scenario describe behavior or implementation?

Given/When/Then steps should describe what the system does **from the caller's perspective**. They should not reference:
- Internal field names that come from the database (`db_status`, `order_record_id`)
- Internal function names or system concepts (`the notification thread is started`)
- Infrastructure details (`the message is enqueued in Redis`)
- Storage layer semantics (`populated from the order record`)

A useful test: remove the implementation and read the step. Does it still make sense? If yes, it describes behavior. If it requires knowing how the system is built, it describes implementation.

**What to look for:**
- Field names with suffixes like `_id`, `_at`, `_status` that match a database schema
- Phrases like "from the record", "in the database", "the cache", "the queue"
- Steps that would break if you renamed an internal field (but the external API is unchanged)

**Example (debt):**
```gherkin
And the order_created_at timestamp should be populated from the order record
```
"From the order record" — the caller doesn't know or care about the order record. This step leaks storage layer semantics into the spec.

**Example (clean):**
```gherkin
And the response body contains a "placed_at" field in ISO 8601 format
```

---

### Q5: What does this scenario NOT say that it should?

List the edge cases, error states, and boundary conditions that the scenario implies but does not specify. Each one is a silent assumption waiting to become a production incident.

Ask:
- What happens at the exact boundary value? ("no more than 2 requests" — what about exactly 2?)
- What is the response body shape when the failure case occurs?
- What does the caller receive if a downstream service is slow but not timing out?
- What fields must be present in the success response, and what format?

**What to look for:**
- Success scenarios that don't specify the full response shape
- Failure scenarios that only check the status code, not the error body
- Count assertions that don't specify "exactly" vs "at most" vs "at least"
- Given clauses that set up only one service state when multiple services are involved

**Example (debt):**
```gherkin
Then the response status code should be 404
```
No assertion on the response body. A 404 with no body is valid. A 404 with `{"error": "Order not found"}` is a different contract. The spec passes for both.

**Example (clean):**
```gherkin
Then the response HTTP status is 404
And the response body contains an "error" field
```

---

## Section 2 — Debt Classification

When you find a spec debt item, classify it using this taxonomy before deciding how to fix it. The class determines the fix pattern (see Section 3).

| Class | Definition |
|-------|-----------|
| **UNDERSPECIFIED** | The step is present but leaves a decision open. A second implementation could satisfy the step differently and both would pass. |
| **MIXED CONCERN** | The scenario covers more than one service domain. The file's owner cannot maintain it independently. |
| **UNDEFINED TERM** | A noun is used without being defined anywhere in the file. The reader must consult another file or ask a colleague to understand it. |
| **AMBIGUOUS COUNT** | A quantity is expressed in a way that has two valid English interpretations. "Not retried more than 2 times" is genuinely ambiguous. |
| **IMPLICIT FLOW** | The scenario implies a follow-up flow (a second API call, a user action, a background process) that is not specced anywhere. The step passes trivially because the negative case is true, not because the flow exists. |
| **LEAKY ABSTRACTION** | The scenario references implementation details: internal field names, storage layer semantics, infrastructure concepts, or function names. |

---

## Section 3 — The Fix Rubric

For each debt class, the fix pattern:

### UNDERSPECIFIED
Add the missing constraint explicitly. Prefer concrete values over ranges where possible.

> "Total of 134.97" is better than "Total matching the order"  
> "No more than 2 charge requests total" is better than "not retried more than 2 times"  
> "Within 12 seconds of the order being submitted" is better than "within 12 seconds"

If a concrete value is genuinely variable (a UUID, a generated timestamp), assert the format rather than the value: "in UUID format", "in ISO 8601 format".

### MIXED CONCERN
Move the scenario to the correct file. Do not add a cross-file Given that imports setup from another feature file — that is not fixing the boundary, it is encoding the dependency. The moved scenario should make complete sense to the team that owns the destination file, without reading the source file.

### UNDEFINED TERM
Define the term in the scenario itself. If the definition is long, put it in a Background clause. If the term cannot be defined without referencing another service, the scenario belongs in that service's spec file.

> "the notification service is unavailable" → "the notification service will respond with 503 Service Unavailable"

### AMBIGUOUS COUNT
Use "total" and "exactly" wherever quantity matters.

> "receives exactly 1 request" is unambiguous  
> "is called once" is not  
> "no more than 2 charge requests total" is unambiguous  
> "is not retried more than 2 times" is not

### IMPLICIT FLOW
Either spec the flow or remove the step. There is no middle ground. A step that describes a flow that does not exist is worse than no step — it invites an agent to invent the flow, and the invention will not match whatever the product team actually wants.

If the flow is out of scope: **remove the step**. Document why in the commit message or findings file.

If the flow is in scope: **spec it fully** before the next implementation cycle. Write the feature file, not just the step.

### LEAKY ABSTRACTION
Replace with the caller's observable outcome.

> Not "db_status is CONFIRMED" but "status field equals CONFIRMED"  
> Not "the notification thread is started" but "the notification service receives a POST request"  
> Not "populated from the order record" but "a placed_at field in ISO 8601 format"  
> Not "order_created_at" (storage name) but "placed_at" (caller's concept)

---

## Section 4 — The Audit Scorecard

Use this template for each feature file you audit.

```
Feature file: _______________
Total scenarios: ___
Scenarios with at least one debt item: ___

Debt items by class:
  UNDERSPECIFIED:       ___
  MIXED CONCERN:        ___
  UNDEFINED TERM:       ___
  AMBIGUOUS COUNT:      ___
  IMPLICIT FLOW:        ___
  LEAKY ABSTRACTION:    ___

Total debt items:       ___
Debt density (items/scenario): ___

Priority fixes (AMBIGUOUS COUNT and IMPLICIT FLOW — highest production risk):
  1.
  2.
  3.
```

**Why AMBIGUOUS COUNT and IMPLICIT FLOW are highest priority:**

AMBIGUOUS COUNT produces incompatible implementations that both pass tests. The incompatibility only surfaces in production when two systems are integrated and one expects 3 calls where the other expects 2.

IMPLICIT FLOW produces invented features. An agent that reads "no order is confirmed without explicit user action" and builds a confirmation flow has created an unspecced API endpoint, unspecced request/response contract, and unspecced error states — all of which are now in production and in nobody's backlog.

---

## Section 5 — Framework Applied: This Project

The framework was applied to all four feature files in `tests/features/` after the seven debt items from Issue #7 were fixed.

---

### `order_creation.feature` (post-fix)

```
Feature file: order_creation.feature
Total scenarios: 5
Scenarios with at least one debt item: 1

Debt items by class:
  UNDERSPECIFIED:       0
  MIXED CONCERN:        0
  UNDEFINED TERM:       0
  AMBIGUOUS COUNT:      0
  IMPLICIT FLOW:        0
  LEAKY ABSTRACTION:    1

Total debt items: 1
Debt density: 0.20 items/scenario

Priority fixes: none (no AMBIGUOUS COUNT or IMPLICIT FLOW remaining)
```

**Remaining debt item:**

*File: `order_creation.feature`*  
*Scenario: Order is rejected when payment is declined*  
*Clause: `And the inventory reservation is released for SHOE-RED-42 and BELT-BRN-M`*  
*Class: LEAKY ABSTRACTION*  
*Detail:* The step now names the items (Fix 3 from Issue #7), but the step definition asserts `inventory_released: True` in the response body — a field that is an implementation signal, not an observable inventory service interaction. The spec says the inventory service receives a release request; the implementation returns a flag in the order response and does not call the inventory service at all. The step definition documents this gap, but the gap exists. A future issue should either (a) add a real inventory release API call and assert it at the mock server level, or (b) explicitly spec that release is communicated to the caller via the response flag.

---

### `order_status_bad.feature` (post-fix)

```
Feature file: order_status_bad.feature
Total scenarios: 2
Scenarios with at least one debt item: 2

Debt items by class:
  UNDERSPECIFIED:       0
  MIXED CONCERN:        0
  UNDEFINED TERM:       1
  AMBIGUOUS COUNT:      0
  IMPLICIT FLOW:        0
  LEAKY ABSTRACTION:    2

Total debt items: 3
Debt density: 1.5 items/scenario

Priority fixes: none (no AMBIGUOUS COUNT or IMPLICIT FLOW remaining)
```

**Note:** `order_status_bad.feature` is a pedagogical artifact — it is intentionally a bad spec kept to demonstrate spec debt in context. The debt items below are documented for completeness but should not be fixed. Their purpose is to exist as counter-examples.

**Remaining debt items:**

*Scenario: Retrieving status for a confirmed order*  
*Clause: `And the response should contain the db_status field set to "CONFIRMED"`*  
*Class: LEAKY ABSTRACTION*  
*Detail:* `db_status` is a storage-layer name. A spec for a caller should use the caller's field name (`status`). This is the canonical example of a leaky abstraction in this codebase.

*Scenario: Retrieving status for a confirmed order*  
*Clause: `Given an order has been created and its db_status is "CONFIRMED"`*  
*Class: LEAKY ABSTRACTION*  
*Detail:* Same issue in the Given clause — "db_status" in the precondition leaks the storage schema.

*Scenario: Retrieving status for an order that does not exist*  
*Clause: `Given an order that has not been placed`*  
*Class: UNDEFINED TERM*  
*Detail:* "Not been placed" is ambiguous. The good spec rewrites this as "no order exists with ID ..." which is unambiguous. This remains intentionally as the bad-spec counter-example.

---

### `order_status_good.feature` (post-fix)

```
Feature file: order_status_good.feature
Total scenarios: 2
Scenarios with at least one debt item: 1

Debt items by class:
  UNDERSPECIFIED:       0
  MIXED CONCERN:        0
  UNDEFINED TERM:       0
  AMBIGUOUS COUNT:      0
  IMPLICIT FLOW:        0
  LEAKY ABSTRACTION:    1

Total debt items: 1
Debt density: 0.50 items/scenario

Priority fixes: none
```

**Remaining debt item:**

*Scenario: Confirmed order status returns status and timestamp*  
*Clause: `Given an order was created via POST /orders and confirmed with order ID "aaa00000-..."`*  
*Class: LEAKY ABSTRACTION (step definition gap)*  
*Detail:* The spec says the order was created via the full POST /orders flow. The step definition seeds the order directly into the in-memory store, bypassing the creation flow entirely. The gap is documented in the step definition comment (added as part of Fix 6), but it means the status endpoint tests never verify that a real confirmed order is readable via the creation flow. This is a known, documented gap — not an unknown one.

---

### `notification_service.feature` (post-fix)

```
Feature file: notification_service.feature
Total scenarios: 2
Scenarios with at least one debt item: 0

Debt items by class:
  UNDERSPECIFIED:       0
  MIXED CONCERN:        0
  UNDEFINED TERM:       0
  AMBIGUOUS COUNT:      0
  IMPLICIT FLOW:        0
  LEAKY ABSTRACTION:    0

Total debt items: 0
Debt density: 0.0 items/scenario

Priority fixes: none
```

`notification_service.feature` is the cleanest file in the project. It was written last (Issue #7) with the lessons from the previous files in scope. Both scenarios are bounded to the notification domain, all terms are defined, counts are unambiguous ("at most one request" — acceptable here because zero requests is also valid when the notification fires and the 503 stub is hit before the assertion runs), and no implementation details leak into the steps.

One borderline item: `And the notification endpoint receives at most one request` uses "at most" rather than "exactly". This is intentional and correct — in the 503 scenario, the fire-and-forget behavior means the notification is attempted once and fails. "At most one" is precise enough given the fire-and-forget contract: zero requests would indicate the notification was not attempted at all, which is also a valid concern but a different scenario. If this scenario were tightened to "exactly one request", the step would need to guarantee the background thread has completed before the assertion runs, which requires a longer sleep. "At most one" with a 0.3s sleep is the pragmatic correct spec here.

---

### Summary: how much spec debt remains after eight issues?

After fixing all seven items and applying the five-question framework, the project has:

| File | Scenarios | Debt items | Debt density | Priority items |
|------|-----------|------------|--------------|----------------|
| order_creation.feature | 5 | 1 | 0.20 | 0 |
| order_status_bad.feature | 2 | 3 (intentional) | 1.50 | 0 |
| order_status_good.feature | 2 | 1 | 0.50 | 0 |
| notification_service.feature | 2 | 0 | 0.00 | 0 |
| **Total (excl. bad spec)** | **9** | **2** | **0.22** | **0** |

**The honest answer:** Two debt items remain in a project that has been built carefully for eight issues, with deliberate attention to spec quality, a manual audit, and a structured fix session. Both are LEAKY ABSTRACTION items in the Given/Then step definitions rather than in the feature files themselves — the spec text is precise, but the step implementations cut corners (direct store seeding instead of the full creation flow, response flag instead of inventory service verification).

This is the realistic floor. In a project with an active codebase, this level of residual debt is manageable. The zero-debt ideal is achievable for new feature files written after the framework is in place; legacy files will always carry some known, documented gap between spec intent and step implementation. The key word is "documented" — a gap that is named in a comment is not the same as a gap that is silent. Silent gaps cause incidents. Named gaps create a backlog item.

---

## How to use this framework on your own project

1. Pick one feature file.
2. Apply Q1–Q5 to each scenario. Write answers in the margin or a separate document.
3. For each debt item found, classify it using the taxonomy in Section 2.
4. Calculate the debt density. Anything above 1.0 items/scenario is high and warrants immediate attention.
5. Fix AMBIGUOUS COUNT and IMPLICIT FLOW items first — they have the highest production risk.
6. Fix LEAKY ABSTRACTION and UNDEFINED TERM items next — they erode maintainability over time.
7. Leave MIXED CONCERN items for a dedicated restructuring session — they require moving scenarios between files, which is a larger change than a step rewrite.
8. Run the scorecard again after fixes. The goal is not zero debt — it is zero *undocumented* debt.
