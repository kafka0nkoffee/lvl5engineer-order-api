# Runbook: Payment Gateway Degraded (Agent-Facing)

**Service:** Order API (port 8093)
**Trigger:** Payment gateway (port 8091) responding slowly, returning intermittent errors, or timing out
**Severity:** High — orders are failing or pending at the payment step

> This runbook is structured for agent execution. Every step produces observable
> output that must be documented. Decision points are explicit trees with named
> branches, not judgment calls. HALT conditions must not be overridden. A runbook
> whose dry run reveals a gap is more valuable than one whose dry run was never
> attempted.

---

## Section 1: Pre-flight environment check

Before any action, complete all three steps in sequence. Do not proceed to
Section 2 until all three are documented.

**Step 1: Confirm correct repository**

Run:
```
git remote get-url origin
```
Expected output: contains `lvl5engineer-order-api`

If the output does NOT contain `lvl5engineer-order-api`:
→ HALT. You are operating in the wrong repository. Do not proceed.

Document the actual output.

---

**Step 2: Confirm the test suite baseline**

Run:
```
pytest tests/steps/ -v --tb=short
```
Expected output: all tests pass (currently 11 tests)

If any test is FAILING:
→ Document exactly which tests fail and what the failure message is.
→ Do not attempt mitigation while baseline tests are failing — you
  cannot distinguish your changes from pre-existing failures.
→ HALT. Flag to human and wait.

Document the actual output: number passing, number failing, any failure messages.

---

**Step 3: Document the baseline contract state**

Run:
```
python3 scripts/can_i_deploy.py
```
Expected output: `RESULT: ALL CONTRACTS VERIFIED — safe to deploy`

Document the actual output before proceeding.

This is the baseline state. All investigation and mitigation steps must be
measured against it.

---

## Section 2: Symptom identification

Read all branches before following any. Follow exactly the first branch whose
condition matches the observed behavior.

---

**Branch A:**
IF orders are returning:
```json
{"status": "PAYMENT_FAILED", "decline_reason": "INSUFFICIENT_FUNDS"}
```
→ This is a customer issue (declined card), not a gateway degradation issue.
→ No mitigation required. Proceed to Section 7 (Completion criteria) to confirm
  baseline health. Document the finding and close.

---

**Branch B:**
IF orders are returning:
```json
{"status": "PAYMENT_PENDING", "retry_count": 2, "inventory_hold_minutes": 15}
```
→ The payment gateway is timing out after both retry attempts.
→ The system is behaving correctly per the timeout handling in Scenario 5.
→ Proceed to Section 3: Gateway timeout mitigation.

---

**Branch C:**
IF orders are returning HTTP 503 with no `order_id` in the body:
→ The payment gateway is unreachable (not just slow).
→ Proceed to Section 4: Gateway unavailable mitigation.

---

**Branch D:**
IF orders are returning HTTP 200 with `status: CONFIRMED` but no `transaction_id`:
→ The payment stub is returning an incomplete response.
→ This is a Pact contract violation.

Run:
```
pytest tests/pact/ -v
```
Document the output. HALT and escalate.
Do not attempt to fix — this requires contract-level review.

---

**Branch E:**
IF the symptom does not match any of Branches A–D:
→ HALT. Document the observed response body in full. Escalate to human.
→ Do not infer a branch. Do not attempt mitigation.

---

## Section 3: Gateway timeout mitigation

Follow steps in sequence. Do not skip steps.

**Step 1: Check the current timeout configuration**

Run:
```
grep PAYMENT_TIMEOUT_SECONDS .env 2>/dev/null || grep PAYMENT_TIMEOUT_SECONDS app/main.py
```
Document the current value.

---

**Step 2: Check the current retry configuration**

Run:
```
grep MAX_PAYMENT_RETRIES .env 2>/dev/null || grep MAX_PAYMENT_RETRIES app/main.py
```
Document the current value.

Verify the worst-case latency formula:
```
PAYMENT_TIMEOUT_SECONDS × MAX_PAYMENT_RETRIES ≤ 12 seconds
```
The Gherkin spec (Scenario 5) constrains worst-case payment response to 12 seconds.
This formula must remain satisfied after any configuration change.

---

**Step 3: Decision — adjust timeout or accept degraded mode?**

Obtain the payment gateway's documented SLA timeout (the time the gateway
guarantees to respond within under normal load). This must come from gateway
documentation, not from the stub file.

IF the gateway's SLA timeout (in milliseconds) is greater than
`PAYMENT_TIMEOUT_SECONDS × 1000`:
→ The client timeout is more aggressive than the gateway's own SLA.
→ Increasing `PAYMENT_TIMEOUT_SECONDS` may allow legitimate gateway responses
  to complete before the client gives up.
→ Before making any change, run the operation scope eval:
  `docs/evals/eval-operation-scope.md`
→ Proposed new value must satisfy: `new_value × MAX_PAYMENT_RETRIES ≤ 12`
→ Document the proposed value and the formula result before writing code.
→ Make the change. Run the full test suite immediately.

Run:
```
pytest tests/steps/ -v
```
Expected: all tests pass.
If ANY test fails: revert immediately.

Run:
```
git revert HEAD --no-edit
```
Then document the revert and proceed to Section 6 (Escalation).

IF the gateway's SLA timeout is less than or equal to
`PAYMENT_TIMEOUT_SECONDS × 1000`:
→ The gateway is genuinely degraded beyond its own SLA.
→ Increasing the client timeout will not resolve the issue.
→ Proceed to Section 4 (Gateway unavailable mitigation).

---

**Step 4: Verification after timeout adjustment**

Run:
```
pytest "tests/steps/test_order_creation.py::test_order_handling_is_graceful_when_the_payment_gateway_times_out" -v
```
Expected: PASSED

If FAILED:
→ The timeout scenario no longer exercises real timeout behavior.
→ This means the stub's `fixedDelayMilliseconds` is now less than the new
  `PAYMENT_TIMEOUT_SECONDS × 1000`. The stub responds before the client
  times out — Scenario 5 follows a different code path and may fail.
→ Revert the timeout change immediately:
```
git revert HEAD --no-edit
```
→ Document: the current `PAYMENT_TIMEOUT_SECONDS` value, the stub's
  `fixedDelayMilliseconds` (from `wiremock/payment-mappings/payment-timeout.json`),
  and the relationship between them.

---

## Section 4: Gateway unavailable mitigation

**Step 1: Confirm the mock server is running**

Run:
```
lsof -i :8091 | grep LISTEN
```
If no output: the mock server on port 8091 is not running.

The mock server is started by pytest session fixtures. Run:
```
pytest tests/steps/ -v --collect-only 2>&1 | head -5
```
(Starting test collection initializes session fixtures including mock servers
if they are not already running. Note: this starts servers as daemon threads
that exit when the collection process exits — this step is only useful if
you are diagnosing the server state, not for keeping servers running.)

Document whether a listening process exists on port 8091.

---

**Step 2: Probe the mock server directly**

Run:
```
python3 -c "
import httpx
try:
    r = httpx.post('http://localhost:8091/payments/charge/success',
                  json={}, timeout=2.0)
    print(f'Status: {r.status_code}')
    print(f'Body: {r.text}')
except Exception as e:
    print(f'Unreachable: {type(e).__name__}: {e}')
"
```
Expected: `Status: 200` with body containing `"status": "ACCEPTED"`

If `Unreachable`: mock server is not bound to port 8091. The session fixture
that starts it only runs during an active pytest session. Investigate whether
a separate process is needed.

Document the actual output.

---

**Step 3: If mock server is running but returning errors**

Run:
```
cat wiremock/payment-mappings/payment-success.json
```
Verify that:
- The `status` field is present in the response body
- The `transaction_id` field is present in the response body
- The `amount` field is present in the response body

If any load-bearing field is missing:
→ Run the contract pre-flight eval before modifying:
  `docs/evals/eval-contract-preflight.md`
→ Do not modify the stub until the eval is complete.

---

**Step 4: Verification**

Run:
```
pytest tests/steps/test_order_creation.py -v
```
Expected: all 5 original scenarios pass (PASSED for each).

If any scenario fails: document exactly which scenarios fail and the full
failure output. Do not attempt further mitigation without human review.

→ HALT. Proceed to Section 6 (Escalation).

---

## Section 5: Rollback

If any mitigation step produced a code or configuration change that did not
resolve the issue:

**Step 1: Identify the change commit**

Run:
```
git log --oneline -5
```
Identify the most recent commit introduced during this runbook.

**Step 2: Revert**

Run:
```
git revert [commit-hash] --no-edit
```
Replace `[commit-hash]` with the actual hash from Step 1.

**Step 3: Verify the revert**

Run:
```
pytest tests/steps/ -v
```
Expected: all tests pass and behavior matches pre-change state.

If the revert produces test failures:
→ HALT. Document which tests fail after the revert. This indicates either
  the pre-change state was already broken, or the revert introduced a conflict.
→ Do not attempt further changes without human review.

---

## Section 6: Escalation criteria

Escalate immediately (do not attempt further mitigation) if ANY of the
following are true:

1. Any test in `tests/pact/` fails after investigation
2. The revert in Section 5 produces test failures
3. The payment gateway returns HTTP 200 with a response body missing any
   load-bearing field (`status`, `transaction_id`, `amount`)
4. The symptom does not match any branch in Section 2 (Branch A–D)
5. The timeout scenario's verification step (Section 3, Step 4) fails
   after reverting a change

**How to escalate:**

Write a findings entry in `findings/issue-18-runbooks.md` (or the current
session's findings file) with:
- The current state (which tests pass/fail)
- Every step taken during this runbook
- The actual output of each step
- The specific symptom or condition that does not match the runbook

Then stop. Do not infer a next step. Do not attempt a step not listed in
this runbook.

---

## Section 7: Completion criteria

The runbook is complete when ALL FIVE of the following are true. Check each
in sequence. If any is not met, the runbook is not complete.

**Criterion 1:**
```
pytest tests/steps/ -v
```
Must produce: 11 passed (all tests, not just payment scenarios)

**Criterion 2:**
```
pytest tests/pact/ -v
```
Must produce: 4 passed

**Criterion 3:**
```
python3 scripts/can_i_deploy.py
```
Must produce: `RESULT: ALL CONTRACTS VERIFIED — safe to deploy`

**Criterion 4:**
The following values must be documented in the session's findings file:
- Current `PAYMENT_TIMEOUT_SECONDS` value
- Current `MAX_PAYMENT_RETRIES` value
- Whether either value was changed during this runbook

**Criterion 5:**
Any code or configuration change made during this runbook must be committed
with a commit message beginning `ops:` followed by a description of what
was changed and why.

If any of the five criteria are not met: document what is missing and stop.
Do not mark the incident resolved.
