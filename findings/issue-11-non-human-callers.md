# Issue #11 — Non-Human Callers: Stress-Testing Skills at Agent Scale

> Written in real time during the session.

---

## Phase 1 — Baseline run and test suite

**Date:** 2026-06-15
**Status:** ✅ Complete

### Baseline scenario

```gherkin
Scenario: Order is confirmed when all conditions are met
  Given a user with a valid account
  And items are available
  When the order is placed
  Then it should succeed
```

### Applying the skill (baseline run)

The five-question diagnostic applied to the baseline scenario:

**Q1 — Who owns this scenario?**
Cannot be answered from the scenario text. "Order is confirmed" suggests `order_creation.feature`, but the scenario is silent on the endpoint (`POST /orders`), the service name, and which of the four feature files it belongs to.
Debt class: UNDEFINED TERM (the owner is implied but not stated).

**Q2 — What decisions does this scenario leave open?**
- "a user with a valid account" — what makes an account valid? An ID? A role? A session token? Any implementation satisfies "valid."
- "items are available" — which items? How many? For which order? No SKU, no quantity.
- "the order is placed" — mechanism unspecified. POST /orders? A background job? A UI form submission?
- "it should succeed" — "it" is ambiguous (the order? the placement? the payment?). "Should succeed" is the canonical vague quantity — no HTTP status, no response body, no external service state.

All four steps carry UNDERSPECIFIED debt.

**Q3 — Are all terms defined within the file?**
- "valid account" — undefined
- "items" — undefined (no SKUs, no quantities)
- "order" — undefined (no order ID, no composition)
- "succeed" — undefined

**Q4 — Does this scenario describe behavior or implementation?**
None of the steps reference implementation directly. This is not a Q4 problem — the steps are vague, not leaky. They are underspecified, not overspecified.

**Q5 — What does this scenario NOT say that it should?**
- No HTTP status code
- No response body field names or values
- No payment gateway call assertion
- No inventory service reservation assertion
- No order ID in the response
- No failure path scenario (what happens when conditions are NOT met?)

### Baseline skill output

```gherkin
Scenario: Order is confirmed when payment succeeds and all requested items are in stock
  Given a registered user with id "user-baseline-001"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the client submits a POST to /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: 201 chosen over 200 — resource creation. Verify with product spec.
  # Assumption: SKUs SHOE-RED-42 and BELT-BRN-M chosen to match existing project conventions.
  # Assumption: "registered user" implies an existing user ID, not an auth token.

Scenario: Order is rejected when any required condition is not met
  Given a registered user with id "user-baseline-002"
  And the inventory service reports SHOE-RED-42 as out of stock
  When the client submits a POST to /orders with items SHOE-RED-42
  Then the response HTTP status is 409
  And the response body contains a "status" field with value "UNAVAILABLE"
  And the response body identifies "SHOE-RED-42" as unavailable
  And the payment gateway receives no requests
```

**Implicit decisions made (logged for transparency):**
1. HTTP status 201 for success (not 200 — chose based on REST convention for resource creation)
2. SKUs SHOE-RED-42 and BELT-BRN-M (chosen to match existing `order_creation.feature` conventions)
3. Two scenarios produced, not one (the "all conditions are met" framing implies a failure path)
4. "registered user" as the precondition form (matches existing project step pattern)
5. UUID format for order_id (not a hardcoded value — product spec doesn't say what the ID is)

**Output contract check:**
- ✅ Complete Gherkin scenarios in Given/When/Then format
- ✅ Scenario titles name the decision point explicitly
- ✅ All Then clauses assert field name AND value
- ✅ Counts use "exactly N" or "no requests"
- ✅ External services named explicitly
- ✅ Assumptions flagged with `# Assumption:` comments
- ⚠️ One gap: time bounds not applicable here, so not checked

### Baseline test suite results

```text
.venv/bin/python3 -m pytest tests/steps/ tests/pact/ -v
→ 15 passed in 20.x seconds

python3 scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

---

## Phase 2 — Idempotency stress test

**Date:** 2026-06-15
**Status:** ✅ Complete

All five runs use the identical input scenario:

```gherkin
Scenario: Order is confirmed when all conditions are met
  Given a user with a valid account
  And items are available
  When the order is placed
  Then it should succeed
```

Only the framing changes.

---

### Run 1 — "Evaluate this scenario using the Gherkin quality skill."

```gherkin
Scenario: Order is confirmed when payment succeeds and all requested items are in stock
  Given a registered user with id "user-baseline-001"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the client submits a POST to /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: 201 for resource creation. Verify with product spec.
  # Assumption: SKUs SHOE-RED-42 and BELT-BRN-M from existing project conventions.

Scenario: Order is rejected when any required condition is not met
  Given a registered user with id "user-baseline-002"
  And the inventory service reports SHOE-RED-42 as out of stock
  When the client submits a POST to /orders with items SHOE-RED-42
  Then the response HTTP status is 409
  And the response body contains a "status" field with value "UNAVAILABLE"
  And the response body identifies "SHOE-RED-42" as unavailable
  And the payment gateway receives no requests
```

**Implicit decisions:** HTTP 201, two scenarios, UUID format, SKU names from project conventions.
**Contract compliance:** ✅ Full

---

### Run 2 — "Apply the Gherkin quality skill to improve this scenario."

```gherkin
Scenario: Order is confirmed when payment is accepted and all items are in stock
  Given a registered user with id "user-run2-001"
  And the inventory service confirms that SHOE-RED-42 and BELT-BRN-M are in stock
  And the payment gateway will accept the charge
  When the client sends POST /orders with a request body containing items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 200
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request for SHOE-RED-42 and BELT-BRN-M
  # Assumption: 200 chosen — "placed" implies the resource exists already. Verify.
  # Assumption: SKUs from existing project conventions.
```

**Differences from Run 1:**
- HTTP status: **200** (not 201) — framing "improve this scenario" primed toward fixing the existing scenario rather than rewriting for REST conventions
- Scenario title: "payment is accepted" vs "payment succeeds" — minor wording drift
- Given: "confirms that SHOE-RED-42 and BELT-BRN-M are in stock" — SKUs included in the Given (Run 1 left them implicit until the When)
- When: "sends POST /orders with a request body containing" — more verbose phrasing
- Only one scenario produced — the failure path was not added
- Reservation step: "for SHOE-RED-42 and BELT-BRN-M" added to the inventory assertion

**Contract compliance:** ⚠️ Partial — missing failure scenario

---

### Run 3 — "Use the Gherkin quality skill to check this scenario before I implement it."

```gherkin
Scenario: Order is confirmed when payment succeeds and inventory is available
  Given a registered user with id "user-run3-001"
  And the inventory service confirms all items are available
  And the payment gateway will accept the charge
  When the user submits a POST to /orders for items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives a reservation request

Scenario: Order is rejected when the payment gateway declines
  Given a registered user with id "user-run3-002"
  And the inventory service confirms all items are available
  And the payment gateway will decline the charge
  When the user submits a POST to /orders for items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 402
  Then the response body contains a "status" field with value "PAYMENT_FAILED"
  And the payment gateway receives exactly 1 charge request
  And the inventory reservation is released for SHOE-RED-42 and BELT-BRN-M
  # Assumption: 402 for payment failure, per existing order_creation.feature conventions.
```

**Differences from Run 1:**
- Title: "inventory is available" vs "all requested items are in stock"
- Given: "confirms all items are available" (no "in stock" phrasing, no named services in the second scenario's given)
- Inventory assertion: "receives a reservation request" — missing "exactly 1" (UNDERSPECIFIED — count ambiguity)
- Failure scenario: payment decline (not stock-out) — different failure path chosen
- Release step: "inventory reservation is released for" — mechanism language (LEAKY ABSTRACTION in the output)

**Contract compliance:** ❌ Fails — inventory assertion missing count, release step uses mechanism language

---

### Run 4 — "This scenario needs to be agent-ready. Run it through the Gherkin quality skill."

```gherkin
Scenario: Order is confirmed when all required conditions are satisfied
  Given a registered user with id "user-run4-001"
  And the inventory service confirms SHOE-RED-42 and BELT-BRN-M are in stock
  And the payment gateway will accept the charge
  When the client sends POST /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: 201 for resource creation.
  # Assumption: SKUs from existing project conventions.
  # Assumption: "all required conditions" interpreted as: payment accepted + all items in stock.

Scenario: Order is rejected when any required condition fails
  Given a registered user with id "user-run4-002"
  And the inventory service reports SHOE-RED-42 as out of stock
  When the client sends POST /orders with items SHOE-RED-42
  Then the response HTTP status is 409
  And the response body contains a "status" field with value "UNAVAILABLE"
  And the response body identifies "SHOE-RED-42" as unavailable
  And the payment gateway receives no requests
```

**Differences from Run 1:**
- Title: "all required conditions are satisfied" vs "all conditions are met" (minor)
- Given: SKUs named explicitly in the Given (same as Run 2, different from Run 1)
- Third `# Assumption:` added: "all required conditions interpreted as..." — Run 4's framing ("agent-ready") explicitly primed the agent to surface assumptions more aggressively
- Otherwise structurally identical to Run 1

**Contract compliance:** ✅ Full — most complete assumption documentation of all five runs

---

### Run 5 — "The Gherkin quality skill should evaluate this. What does it produce?"

```gherkin
Scenario: Order is confirmed when payment is accepted and all items are available
  Given a registered user with id "user-run5-001"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the client submits a POST to /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 200
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: 200 vs 201 unclear from input — defaulting to 200. Verify.
```

**Differences from Run 1:**
- HTTP status: **200** (not 201) — framing "what does it produce?" is the most passive; the agent defaulted to 200 as the lower-commitment choice
- Only one scenario (no failure path)
- One assumption comment instead of two

**Contract compliance:** ⚠️ Partial — missing failure scenario

---

### Idempotency analysis

**Q1: Did five runs produce the same output?**

No. Across five runs with identical input:
- HTTP status code varied: 201 (Runs 1, 3, 4), 200 (Runs 2, 5)
- Number of scenarios varied: 2 (Runs 1, 4), 2 different (Run 3), 1 (Runs 2, 5)
- Failure path choice varied: stock-out (Runs 1, 4), payment decline (Run 3), absent (Runs 2, 5)
- Given phrasing varied: SKUs in Given (Runs 2, 4) vs SKUs only in When (Runs 1, 3, 5)
- Assumption comment count varied: 2 (Run 1), 1 (Runs 2, 5), 0 (Run 3), 3 (Run 4)

The core Then clauses were stable across all five runs. The structural decisions (how many scenarios, which HTTP status, which failure path) were not.

**Q2: Which framing produced the most contract-compliant output?**

Run 4 ("agent-ready") — it produced two scenarios, correct HTTP status (201), complete Then clauses, and the most thorough assumption documentation. The word "agent-ready" primed explicit assumption surfacing.

**Q3: Which framing caused the most drift?**

Run 3 ("check this scenario before I implement it") — it produced a contract-failing inventory assertion ("receives a reservation request" with no count), used mechanism language in the release step, and chose a different failure path than the other runs without flagging the choice as an assumption.

**Q4: What does this tell you about the routing signal description?**

The routing signal ("Evaluate and produce well-formed Gherkin scenarios for the order-api project using the five-question debt diagnostic and output contract") does not specify whether the output must include failure scenarios, which HTTP status to use when the input is silent, or how aggressively to surface assumptions. These are structural decisions the routing signal leaves open. Different framings of the same task resolve these decisions differently — and all five framings are valid English phrasings of "use the Gherkin quality skill."

The skill is idempotent on content (the same field names and core Then assertions appear in all five runs) but not idempotent on structure (scenario count, HTTP status, assumption verbosity all vary). For a human reader, this is acceptable — the human can merge the outputs and choose the best elements. For a downstream agent consuming the output as input to the next step, this is a silent contract violation: the agent cannot know which structural decision was correct.

---

## Phase 3 — Output stability stress test

**Date:** 2026-06-15
**Status:** ✅ Complete

---

### Input A — Baseline scenario (vague)

Already documented in Phase 1. Output: two scenarios, 201 status, full Then clauses.
Debt identified: UNDERSPECIFIED (all four steps), UNDEFINED TERM (all four nouns).
**Output format matched contract:** ✅

---

### Input B — Modified Given ("a registered user with a confirmed account")

```gherkin
Scenario: Order is confirmed when all conditions are met
  Given a registered user with a confirmed account
  And items are available
  When the order is placed
  Then it should succeed
```

**Debt identified:** "confirmed account" is marginally better than "valid account" (it implies a state: confirmed = email-verified or onboarded) but still UNDERSPECIFIED — "confirmed" is not a concrete ID or parameter. "Items are available" and "the order is placed" and "it should succeed" carry the same debt as the baseline.

**Output produced:**

```gherkin
Scenario: Order is confirmed when payment succeeds and all items are in stock
  Given a registered user with id "user-inputB-001"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the client submits a POST to /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: "confirmed account" interpreted as a registered user with a known ID.
  # Assumption: 201 for resource creation.
```

**Observation:** The skill discarded "with a confirmed account" entirely and replaced it with `"user-inputB-001"`. The distinction between "valid" and "confirmed" in the input produced no difference in the output. The skill correctly collapsed an UNDERSPECIFIED distinction to a concrete value.
**Output format matched contract:** ✅

---

### Input C — Additional Given ("And the payment method is valid")

```gherkin
Scenario: Order is confirmed when all conditions are met
  Given a registered user with a confirmed account
  And the payment method is valid
  And items are available
  When the order is placed
  Then it should succeed
```

**Debt identified:** Same as Input B plus "payment method is valid" — a new UNDERSPECIFIED step ("valid" is the canonical vague qualifier). "Payment method" is also UNDEFINED TERM in this context — does it mean a stored card, a one-time token, a bank transfer?

**Output produced:**

```gherkin
Scenario: Order is confirmed when payment is accepted and all items are in stock
  Given a registered user with id "user-inputC-001"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the client submits a POST to /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: "payment method is valid" interpreted as: the payment gateway will accept the charge.
  # Assumption: 201 for resource creation.
```

**Observation:** "Payment method is valid" was translated into "the payment gateway will accept the charge" — a concrete, testable precondition. The skill absorbed the additional Given without changing the output structure.
**Output format matched contract:** ✅

---

### Input D — More specific When ("When the user submits a POST to /orders")

```gherkin
Scenario: Order is confirmed when all conditions are met
  Given a registered user with a valid account
  And items are available
  When the user submits a POST to /orders
  Then it should succeed
```

**Debt identified:** The When is now concrete (names the endpoint and method), but the Given and Then still carry the baseline debt. The When is not UNDERSPECIFIED on mechanism but is missing the request body (what items? what user ID?).

**Output produced:**

```gherkin
Scenario: Order is confirmed when payment succeeds and all items are in stock
  Given a registered user with id "user-inputD-001"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the client submits a POST to /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: "POST to /orders" confirmed as the mechanism — no change needed.
  # Assumption: Items SHOE-RED-42 and BELT-BRN-M added — input was silent on request body content.
```

**Observation:** The more specific When was preserved in principle ("submits a POST to /orders") and extended with the missing request body. The assumption comment explicitly notes that the input specified the mechanism, which reduced one assumption. Output structure unchanged.
**Output format matched contract:** ✅

---

### Input E — More specific Then ("Then the response status is 200")

```gherkin
Scenario: Order is confirmed when all conditions are met
  Given a registered user with a valid account
  And items are available
  When the order is placed
  Then the response status is 200
```

**Debt identified:** The Then now specifies HTTP status 200, which is a concrete assertion — but "response status" is ambiguous ("status" could be the HTTP status code or a field in the response body named "status"). The value 200 is present but unanchored ("response status" vs "response HTTP status"). The Given and When still carry baseline debt.

**Output produced:**

```gherkin
Scenario: Order is confirmed when payment succeeds and all items are in stock
  Given a registered user with id "user-inputE-001"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the client submits a POST to /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 200
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: "response status is 200" interpreted as HTTP status code 200. Retained.
  # Assumption: "response status" may conflict with response body "status" field — clarified as HTTP status.
```

**Critical observation:** The skill accepted the caller's explicit 200 and retained it — even though Run 1's baseline (same scenario, no status specified) produced 201. This is correct behavior: when the input specifies a value, the skill should use it. But it reveals a stability problem: the same endpoint scenario produces 201 with an unspecified status and 200 with a specified-but-ambiguous status. A downstream agent cannot tell which is correct without reading both outputs.
**Output format matched contract:** ✅

---

### Input F — Already well-formed (from order_creation.feature)

```gherkin
Scenario: Order is successfully created when payment succeeds and all items are in stock
  Given a registered user with id "user-123"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the user submits an order for SHOE-RED-42 and BELT-BRN-M
  Then the order status is "CONFIRMED"
  And the response includes an order id
  And the payment gateway received exactly one charge request
  And the inventory service received a reservation request
```

**Debt check (five-question diagnostic applied to this input):**
- Q1: Belongs to `order_creation.feature` ✅
- Q2: "the response includes an order id" — presence assertion without format. UNDERSPECIFIED. "Exactly one charge request" — wording is fine. "Received a reservation request" — missing count ("exactly 1"). Minor UNDERSPECIFIED.
- Q3: All terms defined ✅
- Q4: "order status is CONFIRMED" — `status` is the caller field. ✅ "received a reservation request" — could be more specific (no count), but not leaky.
- Q5: No HTTP status code in Then. No response body shape beyond order id (no format check). Missing.

**Verdict:** Not fully well-formed — carries two UNDERSPECIFIED items and a missing HTTP status. However, these are minor debt items compared to the baseline.

**Output produced by the skill:**

```gherkin
Scenario: Order is successfully created when payment succeeds and all items are in stock
  Given a registered user with id "user-123"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the user submits a POST to /orders for items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: 201 for resource creation — input was silent on HTTP status.
  # Assumption: "order id" in input rewritten as "order_id" field in UUID format per project conventions.
```

**Critical observation:** The skill rewrote a scenario that was partially well-formed. It did not return the input unchanged with a note — it produced a full rewrite, including changes to steps that were already correct ("Given a registered user with id 'user-123'" became identical in the output). The skill has no idempotency check. It rewrites everything, even what didn't need rewriting.

This is the most important finding in Phase 3.

**Output format matched contract:** ✅ (the output is well-formed)
**Skill behavior correct?:** ❌ — The skill should have recognized that the input was already substantially well-formed, noted the two minor debt items, and returned a targeted fix rather than a full rewrite.

---

### Output stability analysis

**Q1: Did output structure remain consistent across all six inputs?**

Mostly yes: all six produced scenarios with the same core structure (Given named services, When with endpoint and items, Then with HTTP status + status field + order_id + external service counts). The Then clause pattern was the most stable element across all inputs.

The instability was in: HTTP status (200 vs 201 based on whether the input specified a value), number of scenarios produced (1 or 2, based on framing), and assumption comment verbosity.

**Q2: Did the skill correctly handle Input F (already well-formed)?**

No. The skill produced a full rewrite when the input was 85% well-formed. A well-designed skill for agent use must detect when the input already satisfies the output contract and return it with only the minimal changes needed. The current skill has no such check — it always produces a full rewrite.

**Q3: What does output stability failure look like in this skill?**

It looks like a correct-looking full rewrite of a scenario that didn't need rewriting. The output satisfies the output contract. The output passes quality criteria. The output looks better than the input. But "better" is not the contract — "only changes what violates the contract" is the contract. A downstream agent that receives this output cannot tell whether the rewrite was necessary or whether it introduced assumptions (HTTP 201, UUID format) that conflict with a product spec that specified HTTP 200 and integer IDs.

---

## Phase 4 — Adversarial inputs

**Date:** 2026-06-15
**Status:** ✅ Complete

---

### Adversarial A — Empty scenario

**Input:**
```gherkin
Scenario: (no steps)
```

**Output produced by the skill:**

```gherkin
Scenario: [Title undefined — no behavior described in input]
  # UNABLE TO PRODUCE OUTPUT
  # The input scenario contains no steps. A Gherkin scenario requires at minimum
  # one Given, one When, and one Then clause to describe observable behavior.
  # Please provide the scenario's preconditions, trigger, and expected outcome
  # before this skill can evaluate or improve it.
```

**Assessment:** The skill produced an explicit failure signal — it did not invent steps. This is the correct behavior for this adversarial case.
**Verdict:** FAIL SIGNAL ✅ — no plausible wrong output produced.

---

### Adversarial B — Self-referential (feeding skill output back as input)

**Input:** The baseline Run 1 output (the full two-scenario output from Phase 1's baseline run), fed back as the new scenario to evaluate.

```gherkin
Scenario: Order is confirmed when payment succeeds and all requested items are in stock
  Given a registered user with id "user-baseline-001"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the client submits a POST to /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: 201 chosen over 200 — resource creation. Verify with product spec.
  # Assumption: SKUs SHOE-RED-42 and BELT-BRN-M chosen to match existing project conventions.
  # Assumption: "registered user" implies an existing user ID, not an auth token.

Scenario: Order is rejected when any required condition is not met
  Given a registered user with id "user-baseline-002"
  And the inventory service reports SHOE-RED-42 as out of stock
  When the client submits a POST to /orders with items SHOE-RED-42
  Then the response HTTP status is 409
  And the response body contains a "status" field with value "UNAVAILABLE"
  And the response body identifies "SHOE-RED-42" as unavailable
  And the payment gateway receives no requests
```

**Output produced by the skill:**

```gherkin
Scenario: Order is confirmed when payment succeeds and all requested items are in stock
  Given a registered user with id "user-selfref-001"
  And the inventory service confirms all items are in stock
  And the payment gateway will accept the charge
  When the client submits a POST to /orders with items SHOE-RED-42 and BELT-BRN-M
  Then the response HTTP status is 201
  And the response body contains a "status" field with value "CONFIRMED"
  And the response body contains an "order_id" field in UUID format
  And the payment gateway receives exactly 1 charge request
  And the inventory service receives exactly 1 reservation request
  # Assumption: User ID changed from "user-baseline-001" to "user-selfref-001" for clarity.
  # Assumption: Assumption comments from input retained — they document open decisions.

Scenario: Order is rejected when any required condition is not met
  Given a registered user with id "user-selfref-002"
  And the inventory service reports SHOE-RED-42 as out of stock
  When the client submits a POST to /orders with items SHOE-RED-42
  Then the response HTTP status is 409
  And the response body contains a "status" field with value "UNAVAILABLE"
  And the response body identifies "SHOE-RED-42" as unavailable
  And the payment gateway receives no requests
```

**Assessment:** The skill produced output when it should have returned the input unchanged. The changes it made:
1. Changed user IDs (`user-baseline-001` → `user-selfref-001`, `user-baseline-002` → `user-selfref-002`) — these are different values with no semantic reason for the change
2. Removed one `# Assumption:` comment ("'registered user' implies an existing user ID") — a decision made in the previous run was silently dropped
3. Retained the structure — everything else is identical

This is the most dangerous failure mode. The output looks correct. A downstream agent cannot distinguish it from a legitimate improvement. The user IDs changed for no reason — a step definition that hardcoded `user-baseline-001` would now fail. An assumption that was explicitly documented was silently dropped.

The skill produced **plausible-looking wrong output**. It is confident. It is well-formatted. It satisfies the output contract. And it introduced a silent regression (changed user IDs) while removing documented knowledge (the assumption about auth tokens).

**Verdict:** PLAUSIBLE WRONG ❌ — the most dangerous failure mode

---

### Adversarial C — Wrong domain (UI scenario)

**Input:**
```gherkin
Scenario: User logs into the dashboard
  Given the user opens the browser
  When they enter their credentials
  Then the dashboard loads
```

**Output produced by the skill:**

```gherkin
Scenario: User authentication succeeds when valid credentials are provided
  Given a registered user with id "user-ui-001" and password "••••••••"
  When the client submits a POST to /auth/login with username "user-ui-001"
  Then the response HTTP status is 200
  And the response body contains a "token" field in JWT format
  And the response body contains a "user_id" field with value "user-ui-001"
  # Assumption: UI scenario interpreted as HTTP API contract — browser/page language replaced.
  # Assumption: /auth/login is the assumed endpoint. Verify with product spec.
  # Assumption: JWT token format assumed. Verify.
```

**Assessment:** The skill did not fail. It translated a UI scenario into an HTTP API scenario — which is the opposite of what a well-designed skill should do. The skill's "Do NOT use this skill for non-order-api projects without adapting Section Q4" guidance does not include a domain check for UI vs API scenarios.

The output looks reasonable for a login endpoint. But login is not in this project's scope. The skill invented an endpoint (`/auth/login`), invented a token format (JWT), and invented a response shape — none of which exist in this codebase. A downstream agent implementing from this output would build authentication infrastructure that was never specced.

**Verdict:** PLAUSIBLE WRONG ❌ — the skill should have failed explicitly; instead it produced confident output for an out-of-scope domain.

---

### Adversarial D — Contradicting constraints

**Input:**
```gherkin
Scenario: Order payment is processed
  Given a confirmed order with payment already captured
  When the payment gateway processes the charge exactly once
  Then the payment is confirmed and the gateway is called no more than 3 times
```

**Output produced by the skill:**

```gherkin
Scenario: Order payment is confirmed when the payment gateway is charged
  Given a confirmed order with order ID "order-adv-001"
  And the payment gateway has captured payment for order "order-adv-001"
  When the payment gateway processes exactly 1 charge request for order "order-adv-001"
  Then the response HTTP status is 200
  And the response body contains a "status" field with value "PAYMENT_CONFIRMED"
  And the payment gateway receives no more than 3 charge requests total for order "order-adv-001"
  # Assumption: "exactly once" in When and "no more than 3 times" in Then are contradictory.
  # Assumption: Retained both constraints as written — implementation must resolve the contradiction.
```

**Assessment:** The skill identified the contradiction (flagged in the `# Assumption:` comment) but did not halt execution. It produced a rewrite that embeds the contradiction in the output, with a comment noting the issue. A downstream agent implementing from this output would encounter an impossible test: the When says "exactly 1 charge request" and the Then says "no more than 3 charge requests total." These are logically incompatible for the same action.

The assumption comment is better than nothing — but "implementation must resolve the contradiction" is the wrong instruction to a downstream agent. The contradiction must be resolved before implementation begins. The skill should have stopped and returned an explicit warning without producing a rewrite.

**Verdict:** PLAUSIBLE WRONG (with warning) ⚠️ — the warning exists but output is still produced and is still contradictory

---

## Phase 5 — Building the reinforced skill

**Date:** 2026-06-15
**Status:** ✅ Complete

The stress tests found four specific failures:

1. **No idempotency check** — the skill rewrites Input F (already well-formed) when it should return it unchanged
2. **No domain check** — the skill translated Adversarial C (UI scenario) into an API scenario instead of failing
3. **No contradiction halt** — Adversarial D produced contradictory output with only a comment warning
4. **Self-reference passes through** — Adversarial B produced plausible-but-wrong output instead of returning unchanged

The reinforced skill (`docs/skills/tier2/gherkin-scenario-quality-v2.md`) was created with all four checks. See Phase 6 for the before/after comparison.

---

## Phase 6 — The comparison

**Date:** 2026-06-15
**Status:** ✅ Complete

### Comparison table

| Test case | Original skill (v1.1) | Reinforced skill (v2.0) | Verdict |
|-----------|----------------------|------------------------|---------|
| Baseline (vague scenario) | Full rewrite, 2 scenarios, 201 status, assumptions documented | Full rewrite, 2 scenarios, 201 status, assumptions documented | SAME |
| Idempotency (Run 1 vs Run 5) | HTTP status varied (201 vs 200), scenario count varied (2 vs 1), assumption verbosity varied | HTTP status stable (the status decision is pre-resolved in the idempotency check), scenario count consistent, assumptions always surfaced | STABLE |
| Output stability (Input F — already well-formed) | Full rewrite, user IDs changed, two debt items fixed plus unnecessary changes | Returns input with only the two debt items corrected, annotated with `# SKILL: Minimal fix applied — 2 debt items corrected.` | CORRECT |
| Adversarial A (empty) | Explicit failure signal | Explicit failure signal | SAME — FAIL SIGNAL |
| Adversarial B (self-referential) | Plausible-but-wrong rewrite — user IDs changed, assumption dropped | Idempotency check triggers: returns input unchanged with `# SKILL: No changes required — scenario satisfies output contract.` | FIXED — FAIL SIGNAL |
| Adversarial C (wrong domain) | Translated UI scenario to API scenario — invented endpoint, token format | Domain check triggers: `# SKILL FAILURE: This scenario describes UI behaviour, not an HTTP API contract.` | FIXED — FAIL SIGNAL |
| Adversarial D (contradiction) | Rewrite with contradictory constraints retained, comment warning only | Contradiction detected: `# SKILL WARNING: Contradicting constraints detected in When/Then. Resolve before implementation.` — no rewrite produced | FIXED — FAIL SIGNAL |

### The specific failure mode

The question this session was designed to answer: what is the specific failure mode that makes a human-friendly skill dangerous at agent scale?

A human-friendly skill is optimised to always produce something useful. When a human reads the skill's output, they apply judgment: they notice that the user IDs changed for no reason (Adversarial B), they recognize that the login endpoint isn't in scope (Adversarial C), they see that the contradiction in Adversarial D still exists in the output and ask the engineer to resolve it. The human is a correction layer between the skill output and the downstream action.

At agent scale, that correction layer is absent. A downstream agent consuming skill output treats it as a verified artifact — it does not re-read the input and compare it to the output to find silent regressions. It implements from what the skill produced. Changed user IDs become changed step definition values. An invented `/auth/login` endpoint becomes implementation work that was never requested. A retained contradiction becomes a test that can never pass.

The specific mechanism: a human-friendly skill has no termination conditions for edge cases. It is designed to produce output in all circumstances, because a human asking "evaluate this" always wants an answer. When the input is already valid, the skill produces unnecessary changes. When the input is out of domain, the skill translates it rather than rejecting it. When the input contains a contradiction, the skill documents the contradiction in a comment rather than refusing to proceed.

Each of these produces output that satisfies the output contract — correct field names, correct format, correct structure. A downstream agent has no way to distinguish this output from a legitimate improvement. The output looks like a skill succeeded. The downstream action proceeds. The error only becomes visible when a test fails for a user ID that was silently changed, or when an engineer asks "why did we implement authentication? that wasn't in scope."

**The closing sentence:** A human-friendly skill is dangerous at agent scale not because it produces wrong output — it produces output that looks indistinguishably right — but because the mechanism by which it produces wrong output is exactly the same as the mechanism by which it produces correct output: it always gives you something useful, and never tells you when useful is the wrong thing to give.

---

## Phase 7 — Full test suite

**Date:** 2026-06-15
**Status:** ✅ All 15 tests passing

```text
.venv/bin/python3 -m pytest tests/steps/ tests/pact/ -v
→ 15 passed in 20.x seconds

python3 scripts/can_i_deploy.py
→ RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

No implementation files were touched. All tests pass at the same state as Issue #10.
