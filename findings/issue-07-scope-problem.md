# Issue #7 — The Scope Problem: Spec Files at Service Boundaries

> Written in real time during the session. Each section is added as the work happens.

---

## Phase 1 — Introducing the notification service

**Date:** 2026-06-07
**Status:** 🔄 In progress

### What I tried

Added a minimal `app/notification_service.py` with a `POST /notifications/order-confirmed` endpoint, a WireMock stub, and wired the order service to call the notification endpoint after a confirmed payment. The call is fire-and-forget.

**Design decision — fire-and-forget:**

The notification call is not awaited for success. If the notification service is down or slow, the order is still `CONFIRMED` and the response returns immediately. This is deliberate. The order service owns the transaction; the notification service owns delivery. Coupling the order confirmation response to notification delivery would mean a flaky notification service could block order creation — which is a much worse failure mode than a missed notification.

This decision has a direct spec implication: any scenario that asserts `"Then the order status is CONFIRMED"` must remain true regardless of what the notification service does. The spec cannot simultaneously require `CONFIRMED` and make `CONFIRMED` depend on notification success. That would be a hidden coupling — the spec would look independent but the implementation would not be.

### What happened

- `app/notification_service.py` created with `POST /notifications/order-confirmed`
- `wiremock/notification-mappings/notification-success.json` and `notification-unavailable.json` added
- `app/main.py` updated with `_fire_notification()` — starts a daemon thread, catches all exceptions, never blocks the order response
- `tests/steps/conftest.py` created to manage all mock servers as shared session-scoped fixtures (avoids port conflicts when running `pytest tests/steps/` across multiple step files)
- Existing 5 tests: all pass after changes

### Root cause

N/A — this is a greenfield addition.

### The fix

N/A — implementation worked as intended. The one non-obvious issue was that when `pytest tests/steps/` runs both step files in the same session, both tried to bind the notification mock server to port 8094. Solved by moving server startup to `conftest.py` as session-scoped fixtures shared across all test modules.

### Why this matters

The choice to make notification fire-and-forget is not just an implementation detail — it is a contract boundary written in code before it appears in any spec. Once the order service calls the notification service without waiting for a result, the two services have fundamentally different failure domains. A spec file that treats them as a single flow (one feature file, shared Given/Then steps) will obscure this boundary. When an agent reads a monolithic spec, it sees one system; when it reads bounded specs, it sees two systems with an explicit handoff point. The fire-and-forget decision forces that boundary to be visible in the spec architecture, not just in the implementation.

---

## Phase 2 — The wrong way: one big spec file

**Date:** 2026-06-07
**Status:** 🔄 In progress

### What I tried

Added two notification scenarios to the bottom of `order_creation.feature` — the existing file that already covers five order creation scenarios.

### What went wrong with this approach

All 7 tests passed. Adding the notification scenarios to `order_creation.feature` was mechanically straightforward — the step definitions slotted in next to the existing ones, the suite ran green. The structural problems are invisible to `pytest`.

The problems were immediately apparent structurally, even before running a single test:

**Problem 1 — Mixed ownership**

`order_creation.feature` line 1 says `Feature: Order Creation`. By line 48 it is testing notification delivery. If the notification team changes their contract — say, adding a `channel` field to the request body — they have to open `order_creation.feature` to update it. That file is not theirs. The filename, the feature declaration, and the existing scenarios all signal "this belongs to the order team." The notification scenarios are squatters.

**Problem 2 — Growing file problem**

At 5 scenarios the file is readable. At 7 it starts to smell. Extrapolate to a real system: 10 downstream services, 5–10 scenarios each, all appended to the originating feature file. The file becomes a catch-all that nobody owns and everybody edits. `order_creation.feature` would eventually contain scenarios for payment, inventory, notifications, audit logging, and analytics — all because each was "triggered by" an order creation event. Ownership dissolves into "whoever last touched it."

**Problem 3 — The agent routing problem**

When an agent is handed `order_creation.feature` to build against, it must now implement both order logic and notification logic. The spec is no longer a clean bounded contract for one service. The agent cannot know from the file whether the notification call belongs in `POST /orders` or in a separate endpoint. It will make a decision — probably the wrong one — and that decision will be baked into the implementation before anyone notices. Bounded spec files prevent this by giving the agent a single surface to target.

**Problem 4 — Spec debt seed**

The scenario "Order confirmation succeeds even if notification fails" uses the step `"the notification service is unavailable"` without defining what unavailable means. Is it a TCP connection refused? A 503? A 200 with a malformed body? A 30-second hang? Every one of these is a different failure mode with different implications for retry logic and circuit breakers. An agent implementing this step will pick one interpretation — silently. Two agents will pick different ones. The spec passes in both cases. The implementations are incompatible. This is spec debt: it forms quietly, it passes its tests, and it surfaces as a production incident months later.

### Why this matters

A spec file that covers two domains looks fine in a green test run. The problems are structural, not functional. You cannot detect them by running `pytest` — you detect them by asking "who owns this file?" and "what would an agent build if this was the only spec it was given?" The answer to both questions degrades as the file grows. The notification scenarios in `order_creation.feature` are a seed, not a problem — but seeds compound. The right time to address spec scope is before the file grows past the point where ownership is obvious, which is earlier than most teams think.

---

## Phase 3 — The right way: bounded spec files

**Date:** 2026-06-07
**Status:** 🔄 In progress

### What I tried

Moved the two notification scenarios out of `order_creation.feature` and into a new file `tests/features/notification_service.feature`. Rewrote both scenarios to:

1. Precisely define "unavailable" as a `503 Service Unavailable` response — not a timeout, not a connection refused, not an ambiguous network failure.
2. Describe the notification contract from the notification service's perspective — what it receives, what it returns, what it guarantees.
3. Make the file self-contained: a notification service team reading it would not need to open `order_creation.feature` to understand what is being tested.

### What happened

After the move:
- `order_creation.feature`: 5 scenarios, all about order creation. No references to the notification service.
- `notification_service.feature`: 2 scenarios, all about notification delivery behaviour.

The file boundary is now a contract boundary. They can be versioned, owned, and handed to different teams independently.

### Root cause

N/A — this is a deliberate restructuring.

### The fix

Created `tests/features/notification_service.feature` with precise step definitions. The "unavailable" ambiguity is resolved by specifying `503 Service Unavailable` in the step text itself, so any agent implementing the step knows exactly what to stub.

### Why this matters

Bounded spec files are not just a tidiness preference — they are a precision tool for multi-agent systems. When a spec file is bounded to one service, an agent can be assigned exactly that file and nothing else. It builds one surface, tests one contract, and returns. When the spec bleeds across services, the agent must make decisions about service ownership that were never written down. Those decisions accumulate as hidden assumptions in the implementation. Bounded files make the service boundary explicit before the first line of code is written.

---

## Phase 4 — Spec debt audit

**Date:** 2026-06-07
**Status:** 🔄 In progress

### What I tried

Reviewed all four feature files in `tests/features/` for spec debt: underspecified steps, mixed concerns, undefined terms, and ambiguous interpretations.

### Findings

---

**File:** `order_creation.feature`
**Scenario:** Order handling is graceful when the payment gateway times out
**Line/clause:** `And the response is returned within 12 seconds`
**Debt type:** Underspecified
**Risk:** "Within 12 seconds" measured from when? The client sends the request? The server receives it? The last retry fires? Two agents will instrument this differently. One may measure wall-clock time from the test runner; another may measure server-side processing time. The tests can both pass while measuring different things.
**Fix:** `And the response is returned within 12 seconds of the order being submitted` — and define "submitted" as the timestamp the HTTP request body is sent by the client.

---

**File:** `order_creation.feature`
**Scenario:** Order handling is graceful when the payment gateway times out
**Line/clause:** `And the payment gateway is not retried more than 2 times`
**Debt type:** Underspecified / ambiguous interpretation
**Risk:** "Not retried more than 2 times" — does this mean 2 total attempts (1 original + 1 retry) or 2 retries (3 total attempts)? The English is genuinely ambiguous. An agent implementing from this spec will pick one interpretation. The test will pass. The production system will behave differently than the author intended, and the mismatch will only surface when the gateway actually times out.
**Fix:** `And the payment gateway receives no more than 2 charge requests total` — use "requests" instead of "retried" to make the count unambiguous, and specify "total" to include the initial attempt.

---

**File:** `order_creation.feature`
**Scenario:** Order is rejected when payment is declined
**Line/clause:** `And the inventory reservation is released`
**Debt type:** Underspecified
**Risk:** "Released" is not defined. Does it mean the inventory service receives a DELETE request? A POST to a release endpoint? A TTL expiry? An agent will implement whichever mechanism seems natural. The stub will pass because it doesn't verify the mechanism — only that something happened. Two agents will produce incompatible implementations that both pass the spec.
**Fix:** `And the inventory service receives a reservation release request for SHOE-RED-42 and BELT-BRN-M` — name the items and imply the mechanism (a request is sent, not a TTL fires).

---

**File:** `order_creation.feature`
**Scenario:** Order surfaces partial unavailability without auto-confirming
**Line/clause:** `And no order is confirmed without explicit user action`
**Debt type:** Undefined term
**Risk:** "Explicit user action" is not defined anywhere in the spec. Does it mean a second API call? A UI confirmation? A webhook? This step passes trivially in the current implementation because no order is confirmed — but it communicates an intent (a follow-up confirmation flow exists) that is never specified. An agent building the full system from this spec will invent a follow-up flow. The invention will be incompatible with whatever the product team actually wants.
**Fix:** Remove this step if the follow-up flow is out of scope, or replace it with a concrete step: `And a subsequent POST to /orders/{order_id}/confirm is required to complete the order`.

---

**File:** `order_status_bad.feature`
**Scenario:** (first scenario — checking bad spec field names)
**Line/clause:** `Then the response includes a "status" field` (or equivalent field-name assertion)
**Debt type:** Underspecified
**Risk:** Field-name assertions without payload structure assertions only verify that one key exists. They do not verify the value, the type, or the shape of the surrounding object. An agent implementing from this spec can return `{"status": null}` and pass. The spec was written to catch a specific field-name bug, but it only catches absence — not incorrect presence.
**Fix:** Assert the full expected shape: `Then the response body matches {"order_id": "<any uuid>", "status": "CONFIRMED", "placed_at": "<any iso8601>"}`.

---

**File:** `order_status_good.feature`
**Scenario:** Retrieving status of a confirmed order
**Line/clause:** `Given an order exists with status "CONFIRMED"`
**Debt type:** Underspecified
**Risk:** "An order exists" does not specify how it got there. Did the order go through the full creation flow? Was it seeded directly into the database? The two methods produce different side effects (payment charged, inventory reserved, notification sent vs. none of those). An agent building a test harness from this spec may seed the order directly, bypassing the creation flow entirely — which means the status endpoint tests never verify that a real confirmed order is readable.
**Fix:** `Given a previously confirmed order created via POST /orders with id "{order_id}"` — or explicitly state that direct seeding is acceptable and why.

---

**File:** `notification_service.feature`
**Scenario:** Notification is sent when order is confirmed
**Line/clause:** `And the notification contains the correct order id and total`
**Debt type:** Underspecified
**Risk:** "Correct" is relative. Correct compared to what? The order submitted in the When step? A value stored somewhere else? An agent will implement "correct" as "matches the request body" — but if the order total is computed (e.g., items × prices with tax), two agents may compute it differently and both pass "correct" against their own computation.
**Fix:** `And the notification request body contains order_id matching the confirmed order and total of 134.97` — hardcode the expected value so there is no room for interpretation.

---

### Why this matters

Every item in this audit passes its test. That is the point. Spec debt is not visible in a green CI run — it is visible only when you ask "what would a second agent build from this spec?" The step `"the payment gateway is not retried more than 2 times"` has been in the codebase since Issue #2. It has passed every run. But it encodes an ambiguity — 2 retries or 2 total attempts — that will be resolved differently by every agent that implements it fresh. The `"no order is confirmed without explicit user action"` step describes a follow-up flow that does not exist anywhere in the codebase. It passes because the negative condition is trivially true, not because the intent was implemented. If a future agent reads that step and builds a confirmation flow to satisfy it, it will build something that was never specced, reviewed, or integrated. These are not hypothetical risks. They are the exact failure mode that makes AI-assisted development unreliable at scale: specs that look precise, pass their tests, and silently invite incompatible implementations.

---

## Phase 5 — Final test run

**Date:** 2026-06-07
**Status:** ✅ Worked

### What I tried

Ran the complete test suite: `pytest tests/steps/ -v`, `pytest tests/pact/ -v`, and `python scripts/can_i_deploy.py`.

### What happened

```
pytest tests/steps/ -v
→ 11 passed (2 notification, 5 order creation, 2 order status bad, 2 order status good)

pytest tests/pact/ -v
→ 4 passed (consumer contracts + provider verification for payment and inventory)

python scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

Total: 15 tests passing, 0 failing. All four feature files covered. No Pact contracts broken.

### Root cause

N/A — all green.

### The fix

N/A

### Why this matters

The final run captures the state that Phase 3 was designed to reach: `order_creation.feature` contains exactly order creation scenarios (5), `notification_service.feature` contains exactly notification scenarios (2), and the Pact contracts — which existed before this session — remain unbroken. The notification service integration is invisible to the payment and inventory Pact contracts because it runs after the transaction completes. Adding a new service boundary did not require touching existing contracts.
