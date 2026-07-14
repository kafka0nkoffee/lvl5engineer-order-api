# Issue #19 — Full Stack Assembly: Order Cancellation

> Written in real time during the session.

---

## Phase 1 — Layer 1: Writing the spec first

**Date:** 2026-07-14
**Status:** ✅ Worked

### What I tried

Before writing any implementation code, applied the Gherkin quality skill (v2.0) to every scenario for `DELETE /orders/{order_id}`. The session required documenting the first draft of each scenario alongside the skill's corrections.

### First drafts (before skill application)

The following are the raw scenarios drafted from the business rules, before the quality skill was applied:

**Draft Scenario 1 — Happy path:**
```gherkin
Scenario: Order is successfully cancelled
  Given a CONFIRMED order exists
  And the inventory service will release the reservation
  When the user cancels the order
  Then the order is cancelled
  And the inventory reservation is released
  And the notification service is notified
```

**Draft Scenario 2 — Idempotency:**
```gherkin
Scenario: Cancelling an already-cancelled order succeeds
  Given a CANCELLED order exists
  When the user cancels the order
  Then the order is cancelled
  And inventory is not released again
```

**Draft Scenario 3 — Non-existent order:**
```gherkin
Scenario: Cancellation fails for non-existent order
  When the user cancels a non-existent order
  Then the request fails with an appropriate error
```

**Draft Scenario 4 — PAYMENT_PENDING rejection:**
```gherkin
Scenario: A PAYMENT_PENDING order cannot be cancelled
  Given a PAYMENT_PENDING order exists
  When the user cancels the order
  Then the cancellation is rejected
```

**Draft Scenario 5 — PAYMENT_FAILED rejection:**
```gherkin
Scenario: A PAYMENT_FAILED order cannot be cancelled
  Given a PAYMENT_FAILED order exists
  When the user cancels the order
  Then the cancellation is rejected
```

### Gherkin quality skill (v2.0) — pre-flight guards

**Guard 1 — Empty input:** Not triggered. All scenarios have steps.

**Guard 2 — Domain check:** Not triggered. No UI behavior.

**Guard 3 — Contradiction detection:** Not triggered. No contradictions detected.

**Guard 4 — Idempotency check:** Triggered in parts — Guard 4 did NOT fire because the drafts fail the five-question diagnostic. Proceeding to diagnostic.

### Gherkin quality skill (v2.0) — five-question diagnostic

**Q1: Who owns this scenario?**

→ `order_cancellation.feature`. A new feature file is required for this endpoint. ✅

**Q2: What decisions does this scenario leave open?**

The following UNDERSPECIFIED patterns were found across the five drafts:

| Draft step | Pattern matched | Required correction |
|---|---|---|
| `a CONFIRMED order exists` | Missing concrete ID | Replace with `a CONFIRMED order with id "order-abc-123" exists` |
| `the user cancels the order` | Missing specific order ID | Replace with `the user cancels order "order-abc-123"` |
| `the order is cancelled` | Missing field name + value | Replace with `the order status is "CANCELLED"` |
| `the inventory reservation is released` | UNDERSPECIFIED: `"is released"` | Replace with `the inventory service receives exactly 1 reservation release request` |
| `the notification service is notified` | UNDERSPECIFIED: `"is notified"` | Replace with `the notification service receives exactly 1 cancellation notification` |
| `inventory is not released again` | Missing count precision | Replace with `the inventory service receives no reservation release requests` |
| `fails with an appropriate error` | UNDERSPECIFIED: `"appropriate"` | Replace with HTTP status code + specific error body |
| `the cancellation is rejected` | UNDERSPECIFIED: `"it should succeed"` class | Replace with HTTP status code + error body |
| `a non-existent order` | Missing concrete ID | Replace with `order "order-does-not-exist"` |
| `a PAYMENT_PENDING order exists` | Missing concrete ID | Replace with `a PAYMENT_PENDING order with id "order-abc-789" exists` |

Q2 found 10 underspecification items across 5 drafts. Every scenario required rewriting.

**Q3: Are all terms defined within the file?**

Order statuses (CONFIRMED, CANCELLED, PAYMENT_PENDING, PAYMENT_FAILED) are domain vocabulary consistent with the existing feature files. They are implicitly defined by the API contract. No new undefined terms introduced.

**Q4: Does this scenario describe behavior or implementation?**

Draft scenarios contained no implementation leaks (no `db_status`, no `background thread`, no database references). ✅

**Q5: What does each scenario NOT say that it should?**

- Happy path: missing HTTP status code assertion (per existing convention for success scenarios, 200 is implied — consistent with CONFIRMED in order_creation.feature, no explicit assertion needed), missing `order_id` in response body assertion, missing side-effect count precision.
- Idempotency: missing `order_id` response assertion, missing notification service non-call assertion.
- Failure scenarios: missing HTTP status codes, missing specific error message values, missing explicit assertion that inventory service was NOT called.

### Corrected scenarios (after skill application)

The minimal-change corrections:

**Scenario 1 — before:**
```gherkin
Scenario: Order is successfully cancelled
  Given a CONFIRMED order exists
  ...
  Then the order is cancelled
  And the inventory reservation is released
  And the notification service is notified
```

**Scenario 1 — after (# SKILL: Minimal fix applied — 5 debt item(s) corrected):**
```gherkin
# SKILL: Minimal fix applied — 5 debt item(s) corrected. [Given unchanged; When unchanged structure changed.]
Scenario: Order is successfully cancelled when it is in CONFIRMED state
  Given a CONFIRMED order with id "order-abc-123" exists
  And the inventory service will accept the reservation release
  When the user cancels order "order-abc-123"
  Then the order status is "CANCELLED"
  And the response includes the order id "order-abc-123"
  And the inventory service receives exactly 1 reservation release request
  And the notification service receives exactly 1 cancellation notification
```

**Scenario 3 — before:**
```gherkin
Scenario: Cancellation fails for non-existent order
  When the user cancels a non-existent order
  Then the request fails with an appropriate error
```

**Scenario 3 — after (# SKILL: Minimal fix applied — 4 debt item(s) corrected):**
```gherkin
# SKILL: Minimal fix applied — 4 debt item(s) corrected.
Scenario: Cancellation of a non-existent order returns 404
  When the user cancels order "order-does-not-exist"
  Then the response status code is 404
  And the response body contains an error field with value "Order not found"
  And the inventory service receives no reservation release requests
```

The most significant correction was the "appropriate error" step — an agent implementing from that step would have had to choose the status code (404 vs 400 vs 422) silently. The skill forced a decision before implementation began.

### What happened

The skill's Q2 check identified UNDERSPECIFIED patterns in all five scenarios. The corrections primarily:
1. Added concrete IDs to Given steps (necessary for fixture chaining in step definitions)
2. Replaced `"is released"` and `"is notified"` with observable signals (exact request counts to specific services)
3. Replaced `"appropriate error"` and `"the cancellation is rejected"` with HTTP status codes and specific error messages
4. Added side-effect absence assertions to all failure scenarios

### Root cause

N/A — this is expected skill behavior. The drafts were intentionally written without the quality checks applied first, to demonstrate the correction delta.

### Why this matters

Every UNDERSPECIFIED step in the first draft represents an implicit decision that would have been pushed into the implementation. "The inventory reservation is released" leaves the mechanism undefined — the agent could satisfy it with a response body flag (`inventory_released: true`) or with an actual HTTP call to the inventory service. "An appropriate error" leaves the status code undefined — 400, 404, and 422 all satisfy it. When the spec is ambiguous, the implementation becomes the spec. The skill surfaces ten of these decisions before a line of code is written, making each decision explicit and reviewable. The alternative is discovering them after the tests pass — when changing a silent decision requires modifying both the implementation and the test.

---

## Phase 2 — Layer 2: Skills consulted

**Date:** 2026-07-14
**Status:** ✅ Worked

### Skills consulted

| Skill | Why consulted | What it produced |
|---|---|---|
| `docs/skills/tier1/output-formatting-standard.md` | All formatting decisions for this findings file | Routing: confirmed findings file structure, section headers, "Why this matters" format |
| `docs/skills/tier2/gherkin-scenario-quality-v2.md` | Writing all six Gherkin scenarios | Routing: matched. Output: 10 debt corrections across 5 drafts; two UNDERSPECIFIED patterns (`"is released"`, `"is notified"`) caught before implementation |
| `docs/skills/tier2/step-definition-style.md` | Writing pytest-bdd step definitions | Routing: matched. Output: fixture-chaining pattern for Given steps, `time.sleep(0.3)` for fire-and-forget assertions, shared step reuse from global registry |

### Skill gap identified

**Gap: No "feature file seeding" skill exists.**

The cancellation feature requires pre-seeding the `_orders` dict with specific order states (CONFIRMED, CANCELLED, PAYMENT_PENDING, PAYMENT_FAILED) before the DELETE call. The step-definition-style skill specifies that Given steps must not call the API, and that they return string keys for mock scenario selection. But the cancellation Given steps need to set up state in the running server's in-memory store — a pattern that doesn't exist in any other step file.

The resolution applied: import `_orders` from `app.main` in the step definition and directly insert the pre-seeded order. This is a valid approach (the module-level dict is shared with the server thread), but it's an implicit convention that the step-definition-style skill doesn't cover.

**Assessment:** This is a skill gap. A future "API state seeding" skill would document when and how to directly manipulate in-memory state from tests, and what the threading implications are. The current step-definition-style skill only covers the fixture-chaining pattern for external service mocks.

### Whether skills prevented divergence from conventions

The step-definition-style skill prevented two potential divergences:
1. **API calls in Given steps:** Without the skill, the most natural approach would have been to call `POST /orders` in the Given step to create a CONFIRMED order. The skill's Convention 3 (Given steps do not call the API) explicitly prohibits this. The `_orders` seeding approach was chosen because of this constraint.
2. **Missing `time.sleep(0.3)` for notification assertion:** Convention 6 in the skill specifies the exact sleep value for fire-and-forget assertions. Without it, the notification assertion would have been intermittently flaky on slower machines.

---

## Phase 3 — Layer 3: Pre-flight evals

**Date:** 2026-07-14
**Status:** ✅ Worked

### Contract pre-flight eval (eval-contract-preflight.md)

Run before creating new WireMock stubs in `wiremock/inventory-mappings/`.

**Q1: Is the field being modified or removed listed as a load-bearing field?**

NO. I am adding NEW stub files (`inventory-release-success.json`, `inventory-release-unavailable.json`). No existing stub fields are modified or removed. Proceed to Q2.

**Q2: Does the modification change a response status code?**

NO. Existing stubs are not modified. The new stubs introduce new status codes (200 for success, 503 for unavailable) for new URL patterns (`/inventory/release/*`). No existing status codes are changed. Proceed to Q3.

**Q3: Does the modification introduce a delay or remove an existing one?**

NO. The new stubs contain no `fixedDelayMilliseconds`. The critical `payment-timeout.json` stub with its 6000ms delay is not touched. Proceed with the modification.

**Contract pre-flight eval result: PASSED.** New stubs may be created.

### Operation scope eval (eval-operation-scope.md)

Run before modifying `app/main.py`.

**Q1: Is this change covered by an existing ADR?**

ADR-001 (inventory before payment) covers `create_order()`. The cancellation endpoint `cancel_order()` does not involve a payment call. ADR-001 agent check questions:

- Q1: "Does my change ensure inventory confirmation completes before any payment gateway call is initiated?" → The cancellation flow makes no payment gateway call. This constraint does not apply. Answer: NOT APPLICABLE — no payment call exists in the cancellation flow.
- Q2: "Does my change handle the case where inventory returns out-of-stock after a payment call has already started?" → NOT APPLICABLE — no payment call in cancellation.
- Q3: "Does Scenario 3 ('Order is rejected when an item is out of stock') still pass?" → YES. The cancellation endpoint is a new route that does not modify `create_order()`. ✅

ADR-001 conclusion: The invariant (inventory before payment) does not apply to the cancellation flow because there is no payment call. Proceed.

ADR-002 (fire-and-forget notification) covers the notification call pattern. The cancellation flow includes a notification call. ADR-002 agent check questions:

- Q1: "Does my change allow the order confirmation response to be returned before the notification call completes?" → YES. The cancellation response is returned before the notification thread completes. ✅
- Q2: "Does my change allow the order confirmation status to be CONFIRMED [CANCELLED] even when the notification service is unavailable?" → YES. The cancellation returns CANCELLED regardless of notification service availability. ✅
- Q3: "Do both notification service scenarios in notification_service.feature still pass without modification?" → YES. The cancellation endpoint is a new route that does not modify `create_order()` or `_fire_notification()`. ✅

ADR-002 conclusion: All three check questions YES. Proceed.

**Q2: Does this change alter the ordering of external service calls?**

For the new cancellation flow: inventory release → notification (fire-and-forget). No payment call. The ordering of the existing create_order flow is unchanged. The new flow: inventory release is synchronous; notification is asynchronous. This ordering is by design — the inventory release must complete (or fail) before the order is marked CANCELLED. No ADR constrains this ordering for cancellation (ADR-001 constrains inventory-before-payment in order creation only).

**Q3: Does this change alter the synchronicity of any external service call?**

The cancellation notification call is fire-and-forget (daemon thread), consistent with ADR-002. The inventory release call is synchronous. No existing call's synchronicity is changed. Answer: NO for existing calls; new calls designed appropriately.

**Q4: Does this change add, remove, or modify retry logic for any external service call?**

No retry logic is added for inventory release or the cancellation notification. Answer: NO.

**Operation scope eval result: PASSED.** All four questions answered. Implementation may proceed.

---

## Phase 4 — Implementation

**Date:** 2026-07-14
**Status:** ✅ Worked

### What I tried

Implemented `DELETE /orders/{order_id}` in `app/main.py` following the constraints derived from the three layers:
- Gherkin scenarios specified the observable behavior (status codes, response body fields, side-effect call counts)
- ADR-002 required fire-and-forget notification
- Step-definition-style skill required `time.sleep(0.3)` before notification assertions
- No retry logic for inventory release (Q4 of operation scope eval)

### Implementation decisions (explicit, not implicit)

1. **HTTP status codes for error responses:** Used proper HTTP status codes (404, 409) via `JSONResponse`, consistent with `get_order_status()`. The body includes `status_code` for step definition compatibility with the existing `check_http_code` step.

2. **Inventory release request body:** Sends `{"order_id": order_id}` only. Items not included — the inventory service tracks reservations by order_id at release time. No items need to be stored in `_orders`.

3. **Notification reuse:** Cancellation notification calls the existing `/notifications/order-confirmed` endpoint (reusing the existing stub per session design). The `_fire_notification()` function is reused unchanged.

4. **`_orders` enrichment:** `user_id` and `total` stored at order creation so they can be passed to the cancellation notification. This is a minimal change to the existing create_order handler.

5. **Cancellation query parameters:** `DELETE /orders/{order_id}?release_scenario=success&cancellation_notification_scenario=success` passes test scenario keys via query params, consistent with how `POST /orders` uses body fields for scenario routing.

---

## Test results after first implementation attempt

**Date:** 2026-07-14
**Status:** ⚠️ Partial (first run), then ✅ Worked

### What happened

**First run: 5 cancellation tests failed, 11 existing tests passed.**

All five cancellation test failures were the same class of error:

```text
pytest_bdd.exceptions.StepDefinitionNotFoundError: Step definition is not found:
Then "the order status is "CANCELLED""
```

And similarly for `"the response status code is 404"` and `"the response status code is 409"`.

### Root cause

pytest-bdd v8 does NOT share step definitions across test files. Step definitions defined in `test_order_creation.py` (e.g., `check_status`, `check_http_code`) are NOT visible to `test_order_cancellation.py` — even though they're in the same test session. This contradicts an assumption I had documented as a "shared step registry."

The step-definition-style skill documents this precisely: "If two feature files use the same step text, define the step once in conftest.py." The skill gave the correct guidance. The implementation didn't follow it.

### The fix

Moved `check_status` and `check_http_code` from their per-file definitions to `conftest.py`, where they become available to all step files. Removed duplicate definitions from `test_order_creation.py` and `test_notification_service.py`.

This is a refactor of existing test infrastructure that does not change any test behavior — the step logic is identical. All 16 Gherkin tests pass after the move.

### Second run: 16/16 passing

```text
16 passed, 3 warnings in 12.96s
```

Plus 4 Pact tests passing and can-i-deploy reporting "ALL CONTRACTS VERIFIED."

### Why this matters

The step-definition-style skill contained the correct guidance for this exact situation. The failure happened because I documented that I "could rely on the global registry" when that assumption was wrong, and then wrote the step file accordingly. If I had re-read the skill's edge case section before writing the step file — specifically "Shared step text across feature files: define once in conftest.py" — the first run would have passed. The skill was right; the consultation was incomplete. The second consultation of the skill (after the failure) produced the fix in one step. This is the skill gap I identified in Phase 2: the skill tells you WHERE to put shared steps but not HOW to diagnose a shared-state seeding problem.

---

## Phase 5 — The full stack in practice

**Date:** 2026-07-14
**Status:** ✅ Worked

### Dimension 1: Implicit decisions made

**Issue #3:** The agent made 4 silent decisions (documented in `findings/issue-03-agent-fresh-implementation.md`): correct timeout constant, correct retry semantics (total vs additional), WireMock stub delay above the client timeout, and the hard-coded path bug in the test setup. In Issue #3, all four were caught by running tests — the agent inferred correctly in 3 of 4 cases, and the 4th was exposed by the fresh environment.

**Issue #19:** Implicit decisions made during this session:

| Decision | Made by | Prevented/caught by |
|---|---|---|
| Inventory release body format (`{"order_id": ...}` only, not items) | Agent | Not caught by any artifact — items were not stored in `_orders`, so sending items wasn't possible. An inventory service that requires items to confirm a release would silently fail. |
| Notification endpoint for cancellation (reusing `/notifications/order-confirmed`) | Session design | Documented in session prompt — not an agent decision |
| Shared step definitions belong in conftest.py | Step-definition-style skill | Caught by the skill, but not consulted at the right moment |
| `_orders` state seeding from the test (bypassing the API) | Agent | Not caught by any artifact — no "state seeding" convention exists |

**Count:** 2 truly implicit agent decisions (inventory release body format, state seeding approach). Down from 4 in Issue #3. The two remaining ones are in a category that the three layers don't cover: implementation choices about data formats for new external service interactions.

### Dimension 2: Spec quality before implementation

**Issue #3:** The agent received the final spec and built. The spec had been written without a quality review first.

**Issue #19:** The Gherkin quality skill caught 10 UNDERSPECIFIED items across 5 first-draft scenarios before any implementation started. The specific corrections that would have produced implicit decisions in Issue #3's style:

- **"the inventory reservation is released"** would have been satisfied by `inventory_released: true` in the response body — the same implementation shortcut that Issue #8 documented as spec debt. The skill's `"is released"` pattern forced it to become "the inventory service receives exactly 1 reservation release request," which requires an actual HTTP call.

- **"the cancellation is rejected"** would have left the status code unspecified. The agent would have chosen 400, 404, or 409 silently. The skill forced 409 to be specified before implementation.

- **"an appropriate error"** is a direct match for the skill's UNDERSPECIFIED list. The skill replaced it with "Order not found" and "Order cannot be cancelled in PAYMENT_PENDING state" — the exact strings that appear in the implementation.

These three corrections prevented three decisions from becoming implicit. The skill's output IS the spec that the agent implements from.

### Dimension 3: Stewardship artifacts consulted

**Issue #3:** None existed.

**Issue #19:**

| Artifact | Question it answered | Potential failure it prevented |
|---|---|---|
| ADR-001 | "Does the cancellation flow violate inventory-before-payment?" | Confirmed: no payment call in cancellation. ADR-001 doesn't apply. No incorrect ordering introduced. |
| ADR-002 | "Must the cancellation notification be fire-and-forget?" | YES. If I had implemented the cancellation notification synchronously, all existing notification service scenarios would still pass (the notification service is up in those tests). The production failure would only appear on the first notification service outage after deploying cancellation. The eval caught this at Q3 of the operation scope eval before any code was written. |
| `eval-operation-scope.md` Q3 | "Does this change alter the synchronicity of any external service call?" | YES to the ADR-002 check — forced the fire-and-forget pattern for the cancellation notification specifically. |
| `eval-contract-preflight.md` | "Are the new stubs modifying load-bearing fields?" | NO — confirmed new stubs don't touch existing fields. Allowed stubs to be created without Pact regeneration first. |
| `CLAUDE.md` Section 3 Invariant 5 | "Are mock servers managed by pytest fixtures?" | The new step definitions import `_orders` and seed state — they do NOT start new mock servers. Invariant 5 is preserved. |

The most important: ADR-002's agent check at Q1 of the operation scope eval. The cancellation notification is a new call in a new endpoint. No behavioral test in `notification_service.feature` covers cancellation notifications — those scenarios test order creation. An agent without ADR-002 would have had no basis for knowing the notification must be asynchronous in a new flow. The ADR extends the invariant to all future notification calls, not just the one it was written to protect.

### Dimension 4: Artifacts as overhead vs acceleration

**Issue #3:** Agent inferred everything. Zero consultation time.

**Issue #19:** Consulting the artifacts added approximately:
- Gherkin quality skill: ~10 minutes (applying to 5 scenarios, documenting corrections)
- ADR-001 and ADR-002 agent check questions: ~5 minutes
- Three pre-flight evals: ~5 minutes
- Step-definition-style skill: ~5 minutes (consulted before writing step definitions)

Total artifact consultation: ~25 minutes added.

The return:
- 10 UNDERSPECIFIED items caught before implementation (preventing late-discovered ambiguity)
- ADR-002 enforced on a new code path (preventing a production outage class that's undetectable by existing tests)
- Step-definition-style skill gave exact answers for `time.sleep(0.3)` and shared step placement (though the second point required a second consultation after a failure)

The net assessment: the artifacts felt like acceleration on the ADR check (one clear question, one clear answer) and like overhead on the Gherkin skill (10 corrections, all of which I would have caught on the second test run anyway). The ADR check is where the artifacts earn their keep — that's the failure the tests cannot catch.

### Dimension 5: Test results after first implementation attempt

**Issue #3:** 5/5 passed on first attempt. Exceptional result — the agent inferred everything correctly from the spec, and the fresh environment caught the portability bug.

**Issue #19:** 11/16 passed on first attempt. The 5 failures were all the same class: shared step definitions not visible to the new test file (`StepDefinitionNotFoundError`). The implementation was correct; the test infrastructure was wrong.

**Why the first-run result differs:**

Issue #3 was testing a clean implementation of an existing feature where every step definition was already written. Issue #19 added both new scenarios AND new step definitions, and the new step file needed to share steps with the existing infrastructure. The failure was a test infrastructure failure, not an implementation failure.

What's different about Issue #19's infrastructure that ultimately made it work: the step-definition-style skill gave the exact pattern for shared steps (`conftest.py`). The failure happened because the skill was consulted for step format but not specifically for the shared-step placement decision. After moving two step definitions to conftest.py (a two-minute change), all 16 tests passed.

Issue #3's "exceptional result" of 5/5 on first attempt was partly a function of the task being simpler — a single new feature with a clean test file and no step sharing required. Issue #19's test infrastructure is more complex, and the one failure was caught and resolved by reading the skill more carefully.

### Why this matters

The comparison answers the question "what would this session have looked like without the three layers?" Without Layer 1 (spec infrastructure), the implementation would have satisfied `inventory_released: true` in the response body rather than making an actual inventory release API call — because that's the simpler implementation and the ambiguous spec permits it. Without Layer 3 (ADR-002), the cancellation notification would have been a reasonable candidate for a synchronous call — it's a new code path, there's no existing test asserting it's asynchronous, and the notification is conceptually "confirming the cancellation." The ADR is the only record that this class of decision was considered and explicitly rejected.

---

## Phase 6 — The remaining gap

**Date:** 2026-07-14
**Status:** ✅ Worked

### What the three layers did not prevent

**Implicit decision 1: Inventory release request body format.**

The inventory release call sends `{"order_id": order_id}` with no items. This is a reasonable design — the inventory service should be able to look up reservations by order ID. But a different reasonable design would send `{"order_id": order_id, "items": [...]}` for explicit confirmation. There's no ADR, no Gherkin scenario, and no eval question that resolves this. The Pact consumer test documents the contract as accepted (`{"order_id": "order-abc-123"}`), but the Pact test is written by the same agent that chose the format — it doesn't enforce the format, it records it.

**Implicit decision 2: State seeding via direct `_orders` manipulation.**

The Given steps for cancellation directly import and mutate `app.main._orders` from the test. This works because the server and the test are in the same process (the server runs in a daemon thread). It's a valid approach for an in-memory store, but it couples the tests to the storage implementation. If `_orders` were replaced with a database, every Given step in the cancellation test would break — and none of the three layers would have caught the coupling.

The step-definition-style skill covers the fixture chaining pattern for external service mocks. It does not cover how to set up internal server state in tests. This is the skill gap I identified in Phase 2.

**What artifact type would have caught these:**

For implicit decision 1: an **API contract document** for the inventory release endpoint specifying the exact request body. This is different from the Pact contract (which documents what the consumer sends and the provider returns) — it's a service-level API specification for the release endpoint that the inventory service team would own. It would have specified whether items are required.

For implicit decision 2: a **"test data seeding" skill** or **"state setup convention" skill** in Tier 2 that documents when direct state manipulation is acceptable and when it's a coupling smell. The current step-definition-style skill covers external service mocks but not internal state setup.

### The judgment call that infrastructure cannot resolve

During implementation, there was one moment where no artifact resolved the decision: **whether to call the inventory release synchronously or fire-and-forget.**

ADR-001 says inventory must be checked before payment (in order creation). ADR-002 says notification must be asynchronous. But neither ADR says anything about inventory release during cancellation. Is it better to:
- Release synchronously (confirms release before returning CANCELLED)
- Release fire-and-forget (returns CANCELLED faster, but can't guarantee the reservation was released)

The Gherkin scenario asserts "the inventory service receives exactly 1 reservation release request" — but it doesn't assert that the order status is only CANCELLED after the release succeeds. The scenario passes with either synchronous or asynchronous release. The choice was made synchronously (release before marking CANCELLED) because releasing synchronously is the safer default for a financial workflow — an unreleased inventory reservation would be an invisible leak.

This is a judgment call that belongs with the human. A future ADR-003 for cancellation could document it. The gap is that the decision was made silently by the agent — it's not in the Gherkin, not in the ADRs, not in the evals. It's in the code, and it will remain invisible until the next agent reads the code and decides to "optimize" the cancellation flow by making the release asynchronous.

### Is this a gap in the infrastructure, or a judgment call that should stay with the human?

Both. The inventory release synchronicity is the kind of decision that, once made, should be documented in an ADR so future agents don't unmake it silently. The current infrastructure has the pattern (ADR-001, ADR-002) but no ADR exists for cancellation-specific decisions. That's a gap.

The state seeding approach is a judgment call that would benefit from a Tier 2 skill documenting the acceptable patterns for test state setup in this project. That's also a gap.

Neither gap invalidates the three layers. ADR-002's catch of the fire-and-forget invariant for the cancellation notification is the clearest proof that the infrastructure works: a new code path, no existing test covering it, and the ADR correctly extended the invariant to the new case before a line of code was written. That's what Layer 3 is for.

### The bridge to Issue #20

The J-curve retrospective will have concrete data to work from: two implicit decisions made despite three layers of infrastructure, one judgment call resolved silently by the agent, and a Tier 2 skill gap identified in real time. The question for Issue #20 is whether the J-curve of building the infrastructure has reached its payoff — and what the shape of the remaining gap tells us about where the next layer should be built.

### Why this matters

Three layers of infrastructure built over 17 issues prevented several specific failures in this session: the `"is released"` spec debt pattern becoming another `inventory_released: true` flag, the cancellation notification becoming synchronous (an untestable ADR-002 violation), and the shared step definitions being duplicated across files. But two implicit decisions survived all three layers: the inventory release body format and the state seeding approach. Both are in a category the infrastructure doesn't yet reach — decisions about HOW the implementation interacts with external services at the API-design level, not the behavioral level. The spec specifies what the service does. The ADRs specify what must not change. The skills specify how to produce the artifacts. None of them specify what the release request body should contain. That gap is real, it's the same gap Issue #8 found (the `inventory_released: true` flag), and it recurs because it lives below the behavioral spec and above the code: in the API design layer that the project hasn't yet formalized.
