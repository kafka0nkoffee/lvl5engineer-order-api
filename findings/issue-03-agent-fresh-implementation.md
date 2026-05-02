# Issue #3 — Agent Fresh Implementation From Spec
**Newsletter issue:** [I Gave the Agent the Spec and Walked Away. Here's What It Built.](#)
**Session date:** 2026-05-02
**Related phases:** Phase 2 (Write External Behavioural Scenarios)

---

## Behavioural contract derived from Gherkin alone
**Status:** ✅ Worked

### What I tried
Instructed Claude Code to read only the Gherkin feature file and build a fresh
implementation without reading the existing `app/main.py`.

### What happened
Before writing any code, the agent derived the complete API contract from the
scenarios — the order of operations, response shapes, status codes, and body
fields for all five scenarios:

```
POST /inventory/check/{inventory_scenario}
  → all available      → POST /payments/charge/{payment_scenario}
  → partial available  → return 207 PARTIAL_UNAVAILABLE (no charge)
  → all out of stock   → return 409 UNAVAILABLE (no charge)
```

Full response shape derived correctly:

| Scenario | status | status_code | Key body fields |
|---|---|---|---|
| Success | CONFIRMED | — | `order_id` |
| Payment declined | PAYMENT_FAILED | 402 | `decline_reason`, `inventory_released: true` |
| Out of stock | UNAVAILABLE | 409 | `unavailable_items: [sku]` |
| Partial stock | PARTIAL_UNAVAILABLE | 207 | `available_items`, `unavailable_items` |
| Payment timeout | PAYMENT_PENDING | 202 | `inventory_hold_minutes: 15`, `payment_pending: true`, `retry_count` |

### Root cause
N/A — this worked as intended.

### Why this matters
The agent read five plain-language scenarios and extracted a precise technical
contract without being told any of it explicitly. This is the spec doing its job.
A well-written Gherkin scenario isn't just documentation — it's a complete
specification that a machine can reason from. The quality of the output here was
a direct function of the quality of the input.

---

## Timeout and retry logic — correctly reasoned without hints
**Status:** ✅ Worked

### What I tried
Let the agent figure out the timeout and retry behaviour from scenario 5 alone.

### What happened
The agent correctly reasoned:
- `PAYMENT_TIMEOUT_SECONDS=5` — per-attempt HTTP client timeout
- `MAX_PAYMENT_RETRIES=2` — total attempt cap, not retries on top of the first attempt
- Worst-case wall time: 2 attempts × 5s = 10s, within the 12s scenario contract
- WireMock stub delay of 6000ms — deliberately longer than the 5s client timeout

### Root cause
N/A — this worked as intended.

### Why this matters
The `fixedDelayMilliseconds: 6000` detail is subtle. If the mock delay were shorter
than the client timeout, the test would be testing the mock responding slowly rather
than the client giving up. The agent caught this distinction without being prompted.
Scenario 5 is the one most tutorials skip — and it's the one that bites you in
production. A spec that forces you to think through timeout behaviour before building
is doing its most important work here.

---

## Hard-coded environment path — portability bug in original test setup
**Status:** ❌ Found in existing code → ✅ Fixed

### What I tried
The agent ran the test suite against its fresh implementation on a clean environment.

### What happened
Tests failed with confusing errors. The agent traced the failure to a hard-coded path
in the original test setup:

```python
# Original — breaks silently on any machine but the one it was written on
sys.path.insert(0, "/home/claude/order-api")
```

On any other machine this silently started mock servers with no stubs loaded, causing
every payment call to return 404 and every inventory call to return 404 — triggering
wrong branches throughout the test suite.

### Root cause
The path was written for the specific environment where the original code was built
and never made machine-portable.

### The fix
```python
# Fixed — computed dynamically from the test file's own location
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

### Why this matters
This bug was in the human-written code, not the agent-written code. The agent found
it because it was running on a different environment where the assumption failed
immediately. This is one of the underappreciated benefits of Level 4 development —
when an agent implements on a clean environment, your implicit assumptions get exposed
right away rather than surviving until a new team member joins or a CI environment
differs from your local machine. The clean environment isn't a limitation. It's a
diagnostic tool.
