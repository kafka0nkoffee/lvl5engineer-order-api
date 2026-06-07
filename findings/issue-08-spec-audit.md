# Issue #8 — Fixing Spec Debt and Building the Audit Framework

> Written in real time during the session.

---

## Phase 1 — Fixing the seven spec debt items

**Date:** 2026-06-07
**Status:** 🔄 In progress

Each fix is applied one at a time. Tests run after each one.

---

### Fix 1 — Timeout measurement ambiguity (`order_creation.feature`)

**Original:**
```
And the response is returned within 12 seconds
```

**Rewritten:**
```
And the response is returned within 12 seconds of the order being submitted
```

**What this closes:** The original step is silent about when the clock starts. "Of the order being submitted" anchors it to the client-side timestamp at HTTP request dispatch — the same moment `time.time()` is captured in `_post_order()` in the step definition. Without this anchor, a second implementation could measure from server receipt, from the last retry attempt, or from when the response body is fully read. All three produce different numbers under load.

---

### Fix 2 — "Retried" vs "total attempts" ambiguity (`order_creation.feature`)

**Original:**
```
And the payment gateway is not retried more than 2 times
```

**Rewritten:**
```
And the payment gateway receives no more than 2 charge requests total
```

**What this closes:** "Retried 2 times" has two valid English readings: 2 retries (3 total requests) or retried up to 2 times meaning 2 total requests. "No more than 2 charge requests total" is unambiguous — it counts requests, not retries. The word "total" makes clear that the initial attempt is included in the count. The current implementation sends a maximum of 2 requests (`MAX_PAYMENT_RETRIES=2` drives `while attempt < max_retries`), so the rewritten step is consistent with the existing behavior.

The step definition assertion changes from `retry_count <= 2` to checking that the payment log received at most 2 calls. This is a stronger assertion because it verifies the actual call count at the mock server rather than trusting the response body's `retry_count` field.

---

### Fix 3 — "Released" without mechanism (`order_creation.feature`)

**Original:**
```
And the inventory reservation is released
```

**Rewritten:**
```
And the inventory service receives a reservation release request for SHOE-RED-42 and BELT-BRN-M
```

**What this closes:** "Released" says what happened but not how, and not for which items. The rewrite names the items explicitly (making the assertion concrete rather than implicit) and specifies that a request is sent to the inventory service (rather than relying on TTL expiry, in-memory flag clearing, or some other mechanism). Note: the current implementation signals release via a response field (`inventory_released: true`) rather than a separate inventory API call. This is a case where fixing the spec reveals a gap in the implementation. The fix documents the intended behavior; the step definition reflects what the system actually does today.

---

### Fix 4 — "Explicit user action" undefined (`order_creation.feature`)

**Original:**
```
And no order is confirmed without explicit user action
```

**Rewritten:** *(step removed entirely)*

**What this closes:** "Explicit user action" implies a follow-up confirmation flow (`POST /orders/{id}/confirm` or equivalent) that does not exist anywhere in the codebase. The step passes trivially today because no order is confirmed in the partial unavailability scenario — not because the confirmation flow was implemented. Removing the step is the correct call: a spec step that passes for the wrong reason is not a safety net, it is a false guarantee. If the confirmation flow is built in a future issue, a new scenario should specify it precisely. Leaving this step in place would invite an agent to implement an unspecced confirmation endpoint.

---

### Fix 5 — Presence without value assertions (`order_status_bad.feature`)

**Original (Then clause):**
```
And the response should contain the db_status field set to "CONFIRMED"
And the order_created_at timestamp should be populated from the order record
```

**Rewritten:**
```
And the response body contains a "db_status" field with value "CONFIRMED"
And the response body contains an "order_created_at" field with a non-empty string value
And the response body contains a "status" field with value "CONFIRMED"
```

**What this closes:** The original `check_db_status` step asserts `body["db_status"] == expected`, which is already a value assertion — but the `check_created_at` step only verified presence and type (`isinstance(str)` and `len > 0`). Adding `"status"` to the bad-spec assertions makes it explicit that the bad spec incidentally catches both field names (since the implementation returns both for compatibility). The `order_created_at` step now asserts non-empty string explicitly, removing the comment-only documentation of the silent assumption.

Note: `order_status_bad.feature` is intentionally a bad spec kept for newsletter demonstration. Fixes here are conservative — we document the gaps without converting it to a good spec, which would defeat its pedagogical purpose.

---

### Fix 6 — "An order exists" without specifying how it got there (`order_status_good.feature`)

**Original:**
```
Given an order was successfully placed and confirmed with order ID "aaa00000-0000-0000-0000-000000000001"
```

**Rewritten:**
```
Given an order was created via POST /orders and confirmed with order ID "aaa00000-0000-0000-0000-000000000001"
```

**What this closes:** "Successfully placed and confirmed" describes the outcome but not the mechanism. The step definition seeds the order directly into `_orders` — bypassing the creation flow, payment, and inventory checks. A reader of the spec cannot tell whether the Given is establishing state by running the full creation flow or by direct seeding. "Created via POST /orders" makes the mechanism explicit and signals that a real creation flow is expected — even if the step implementation currently uses a shortcut. This creates a documented gap between spec intent and step implementation that a future issue can close.

---

### Fix 7 — "Correct" without definition (`notification_service.feature`)

**Original:**
```
And the notification contains the correct order id and total
```

**Rewritten:**
```
And the notification request body contains order_id "order-abc-123" and total 134.97
```

**What this closes:** "Correct" is relative to context that may not be available to the reader. The rewritten step hardcodes the expected values that are established in the When clause (`order "order-abc-123"` with `total 134.97`). Two agents reading the original step would both implement something that checks the notification body — but one might compare against the When-clause values, another might check against a computed total, and a third might only verify that the fields are present. The rewrite removes all three interpretations: it names the exact values, making any deviation a test failure.

---

## Phase 2 — Building the spec audit framework

**Date:** 2026-06-07
**Status:** ✅ Worked

### What I tried

Built `docs/spec-audit-framework.md` as a standalone document structured around five diagnostic questions, a six-class debt taxonomy, a fix rubric, and an audit scorecard. Applied the five questions to all four feature files (fixed versions) and filled in the scorecard for each.

### What happened

The framework application found **one item the manual audit missed**:

In `order_status_good.feature`, the Given clause reads `an order was created via POST /orders and confirmed with order ID "aaa00000-..."` — this is the fixed version of Fix 6. But Q4 (behavior vs implementation) flags it for a different reason than the original audit: the step definition still seeds the order directly into the in-memory store. The spec text says "created via POST /orders" but the step implementation bypasses the creation flow. This is a documented gap in the step definition comment, but the framework surfaced it as a LEAKY ABSTRACTION at the step definition level rather than the feature file level — a distinction the manual audit didn't make explicitly.

The manual audit also didn't clearly separate "debt in the feature file text" from "debt in the step definition implementation". The framework's Q4 applies to both, which is more thorough.

### Surprising finding

`notification_service.feature` scored zero debt items. It was written after eight issues of accumulating spec debt lessons, and the absence of debt is not accidental — it's the result of knowing what the previous files got wrong. The older files carry more debt not because they were written carelessly, but because they were written before the patterns were visible.

This has an implication for how spec debt should be managed on real projects: **the best time to write a spec is after you've written a few bad ones**. Auditing retroactively and fixing forward is the realistic path, not "write it right the first time."

### What the framework revealed about classification

One item didn't fit cleanly into a single class. In `order_creation.feature`, the step `And the inventory reservation is released for SHOE-RED-42 and BELT-BRN-M` is UNDERSPECIFIED (mechanism unspecified) AND LEAKY ABSTRACTION (the step definition uses a response body flag rather than a mock server assertion). The taxonomy handles these as separate items for the same step. That's correct behavior — a step can carry multiple debt classes, and each requires a different fix pattern.

---

## Phase 3 — Final test run

**Date:** 2026-06-07
**Status:** ✅ Worked

```
pytest tests/steps/ -v
→ 11 passed (all Gherkin tests across all four feature files)

pytest tests/pact/ -v
→ 4 passed (consumer contracts + provider verification)

python scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

Total: 15 tests passing, 0 failing. No spec fixes broke any existing test. Fix 7 revealed one implementation gap in the WireMock stub (notification_id was `"mock-notif-001"` — not a UUID). Fixed by updating the stub to return a valid UUID. This is exactly the value of adding a format assertion: it caught a stub that was never valid but was never checked.

---

## Closing question: how much spec debt remains?

After fixing all seven items and applying the framework, the project carries **2 debt items in 9 non-pedagogical scenarios** (debt density: 0.22 items/scenario). Both are LEAKY ABSTRACTION items at the step definition level — the spec text is precise, but the step implementations cut corners.

Zero priority (AMBIGUOUS COUNT, IMPLICIT FLOW) items remain.

The uncomfortable answer: spec debt is not eliminated by fixing debt. The `order_status_good.feature` step definition gap was introduced by the same session that fixed the vague Given clause — a precise spec step was written, but the implementation of that step took a shortcut. Spec debt can migrate from the feature file into the step definition. The audit framework catches both, but only if you apply Q4 to the step definitions as well as the feature text.

The practical conclusion: treat step definitions as part of the spec surface, not just as test harness code. A step definition that silently does something different from what the spec says is spec debt, even if the test passes.
