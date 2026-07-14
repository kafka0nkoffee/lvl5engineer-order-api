---
type: Methodology
title: "Skill: Step Definition Style"
description: "Applies consistent style conventions to pytest-bdd step definitions in tests/steps/, covering naming, scoping, and fixture patterns."
tags: [tier-2, skill, step-definitions, pytest-bdd, testing]
timestamp: 2026-06-16
---

# Skill: Step Definition Style

**Tier:** 2 — Domain methodology
**Version:** 1.0
**Last updated:** 2026-06-16 (Issue #13)
**Project:** lvl5engineer-order-api

---

## Description

Write pytest-bdd step definitions for order-api using the fixture-chaining pattern and assertion conventions.

---

## When to use this skill

Use this skill when:
- You are creating a new step definition file for a feature file in this project
- You are adding new step definitions to an existing step file in `tests/steps/`
- You need to implement the pytest-bdd steps that back a Gherkin scenario

Do NOT use this skill when:
- You are writing the Gherkin feature file — use gherkin-scenario-quality-v2.md
- You are implementing application logic in `app/main.py`
- You are writing step definitions for a service other than order-api (apply the principles
  but do not apply the order-api-specific fixture conventions directly)

---

## Methodology

### Convention 1 — File structure and imports

Every step definition file follows this import block exactly:

```python
import time, pytest, requests, os, sys, json
from pytest_bdd import scenarios, given, when, then, parsers

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

scenarios("../features/[feature_file_name].feature")
```

The `scenarios()` call immediately follows the imports. It binds the step file to exactly
one feature file. Do not bind a step file to multiple feature files.

Port constants are defined at module level after the scenarios binding:

```python
API_PORT          = 8093
PAYMENT_PORT      = 8091
INVENTORY_PORT    = 8092
NOTIFICATION_PORT = 8094
```

Include only the ports used by the scenarios in this file. Do not import ports that are
unused.

### Convention 2 — Section separator comments

Separate Given, When, and Then definitions with section separators:

```python
# ── Given ─────────────────────────────────────────────────────────────────────

# ── When ──────────────────────────────────────────────────────────────────────

# ── Then ──────────────────────────────────────────────────────────────────────
```

Use em-dashes (──), not hyphens or equals signs. The separators are exactly this width.
All Given definitions go between the Given and When separators, in the same order as they
appear in the feature file.

### Convention 3 — Fixture chaining (the core pattern)

Given steps do not call the API or external services. They return a string key that
identifies which mock stub to use. This key is passed to the When step via pytest fixture
chaining.

**Given pattern:**

```python
@given("the payment gateway will accept the charge", target_fixture="payment_scenario")
def pay_success(): return "success"

@given("the payment gateway will decline the charge", target_fixture="payment_scenario")
def pay_declined(): return "declined"
```

The `target_fixture` name is the fixture consumed by the When step. The return value is a
short string key that matches a stub scenario in the mock server's routing logic. The keys
are: `"success"`, `"declined"`, `"timeout"`, `"out-of-stock"`, `"partial"`, `"all-available"`,
`"unavailable"`. Use these exact strings — they are matched by the mock server.

When a Given step needs to pass structured data (a user ID, an order ID), use `parsers.parse`:

```python
@given(parsers.parse('a registered user with id "{user_id}"'), target_fixture="user_id")
def registered_user(user_id): return user_id
```

**Why fixture chaining:** Given steps must not call the API. They set up the scenario
context that the When step uses when it does call the API. An agent that puts API calls
in Given steps creates scenarios that partially execute before the When clause — which
makes test failures impossible to diagnose.

### Convention 4 — When steps and the response dict

When steps call the order API and return a dict with two keys:

```python
@when("the user submits an order for SHOE-RED-42", target_fixture="response")
def submit_one(user_id, payment_scenario, inventory_scenario, notification_scenario):
    t0 = time.time()
    r = requests.post(
        f"http://localhost:{API_PORT}/orders",
        json={
            "user_id": user_id,
            "items": [{"sku": "SHOE-RED-42", "quantity": 1, "unit_price": 89.99}],
            "payment_scenario": payment_scenario,
            "inventory_scenario": inventory_scenario,
            "notification_scenario": notification_scenario,
        },
        timeout=20,
    )
    return {"response": r, "elapsed": time.time() - t0}
```

The `target_fixture="response"` name is standard — all Then steps receive `response` as
their fixture. The dict always has two keys: `"response"` (the requests.Response object)
and `"elapsed"` (float seconds). Do not add additional keys.

For shared When logic used by multiple scenarios (e.g., different SKU combinations), extract
to a private helper function:

```python
def _post_order(user_id, payment_scenario, inventory_scenario, skus,
                notification_scenario="success"):
    t0 = time.time()
    items = [{"sku": s, "quantity": 1,
              "unit_price": 89.99 if "SHOE" in s else 44.98} for s in skus]
    r = requests.post(f"http://localhost:{API_PORT}/orders",
                      json={"user_id": user_id, "items": items,
                            "payment_scenario": payment_scenario,
                            "inventory_scenario": inventory_scenario,
                            "notification_scenario": notification_scenario},
                      timeout=20)
    return {"response": r, "elapsed": time.time() - t0}
```

Helper functions are prefixed with `_` and defined before the `@when` decorators that use
them. Do not name helper functions with the same name as any fixture.

### Convention 5 — Then steps and assertion messages

Every assertion must include an f-string diagnostic message showing the actual value:

```python
@then(parsers.parse('the order status is "{expected}"'))
def check_status(response, expected):
    b = response["response"].json()
    assert b["status"] == expected, f"Expected {expected}, got {b['status']}\n{b}"
```

The message pattern is: `f"Expected {expected}, got {actual}\n{full_body}"`. The `\n{b}`
at the end dumps the full response body — this is essential for diagnosing failures in CI
where you cannot inspect the live process.

Do not write: `assert b["status"] == expected` with no message.
Do not write: `assert b["status"] == expected, "Status mismatch"` with no values.

For mock server log assertions (payment/inventory/notification call counts), use the
shared fixtures from conftest.py (`payment_log_shared`, `inventory_log_shared`,
`notification_log_shared`):

```python
@then("the payment gateway received exactly one charge request")
def payment_called_once(payment_log_shared):
    calls = payment_log_shared.all()
    pay_calls = [c for c in calls if c["path"].startswith("/payments/")]
    assert len(pay_calls) == 1, \
        f"Expected 1 payment call, got {len(pay_calls)}: {calls}"
```

### Convention 6 — Sleep before async assertions

Fire-and-forget operations (notifications sent in a background thread) are not complete
when the API response returns. Before asserting that a background operation occurred, sleep:

```python
@then("the notification service receives a confirmation request")
def notif_called(response, notification_log_shared):
    time.sleep(0.3)
    calls = notification_log_shared.any_calls_matching("/notifications/order-confirmed")
    assert calls, f"Expected notification call, got: {notification_log_shared.all()}"
```

Use exactly 0.3 seconds. This value was derived from profiling the notification thread
startup time on the development machine. Do not use a longer sleep "to be safe" — 0.3s
introduces 0.3s of test runtime per async assertion; a longer value multiplies this cost.
Do not use a shorter sleep — it causes intermittent failures on slower machines.

The 0.3-second sleep applies only to fire-and-forget assertions. Synchronous API assertions
do not need a sleep.

---

## Output contract

What this skill must produce:

- A Python file (`tests/steps/test_{feature_name}.py`) with:
  - Correct import block (all six imports, PROJECT_ROOT setup, scenarios binding)
  - Port constants for services used
  - Three section separator comments in correct order (Given / When / Then)
  - All Given steps use `target_fixture`
  - All When steps that call the API return `{"response": r, "elapsed": ...}` with
    `target_fixture="response"`
  - All Then steps include an assertion message with the actual value in an f-string
  - Fire-and-forget assertions preceded by `time.sleep(0.3)`

What this skill must NOT produce:

- API calls in Given steps
- Then steps without assertion messages
- Hard-coded fixture values in Then steps (values should come from fixtures, not literals)
- Imports that are not used
- Step definitions that duplicate existing definitions in another step file
  (reuse shared step definitions from conftest.py instead)

---

## Quality criteria

Before returning the step file:

1. **Fixture chains complete**: every `target_fixture` returned by a Given step is consumed
   by a When or Then step.
2. **Response dict consistent**: every When step that calls the API returns the two-key dict.
3. **Assertion messages present**: every `assert` statement has a message argument.
4. **No Given-level API calls**: search for `requests.post`, `requests.get` in Given
   functions — there should be none.
5. **Sleep placement correct**: `time.sleep(0.3)` appears only before fire-and-forget
   assertions, not before synchronous assertions.

---

## Edge cases and failure modes

**Parameterized steps (multiple scenarios with different values):** Use `parsers.parse`
with typed parameters. Example: `parsers.parse("response is returned within {seconds:d}
seconds")`. The `:d` suffix parses as integer; `:f` as float; default is string.

**Shared step text across feature files:** If two feature files use the same step text
(e.g., `a registered user with id "user-123"`), define the step once in conftest.py and
import it. Do not duplicate step definitions across files — pytest-bdd will raise a
`StepDefinitionNotFoundError` if the same step text is defined twice in the same session.

**Step definition for a non-order-api service:** Do not apply the order-api-specific fixture
chaining keys ("success", "declined") to a different service. Apply the principle (Given
returns a key; When uses it) with keys appropriate to the target service.

**Feature file not yet written:** Do not write step definitions for a feature file that
does not exist. The `scenarios()` call will fail at collection time. Write the feature file
first using gherkin-scenario-quality-v2.md.

---

## Version history

| Version | Change | Issue |
|---------|--------|-------|
| 1.0 | Initial skill — formalizes five implicit step definition conventions | #13 |

---

## Reference

The conventions in this skill are derived from the four existing step files:
- `tests/steps/test_order_creation.py`
- `tests/steps/test_order_status_good.py`
- `tests/steps/test_order_status_bad.py`
- `tests/steps/test_notification_service.py`
- `tests/steps/conftest.py` (shared session-scoped fixtures)

For the Gherkin scenarios that these steps implement, see:
`docs/skills/tier2/gherkin-scenario-quality-v2.md`
