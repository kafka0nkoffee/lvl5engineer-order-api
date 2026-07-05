# Issue #18 — Runbooks as Infrastructure: What Agents Need That Humans Don't

> Written in real time during the session.

---

## Phase 1 — The runbook gap analysis

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Documented the precise difference between a human-facing and agent-facing runbook across five dimensions, using the payment gateway degradation scenario.

### What happened

The five-dimension analysis makes a point that is easy to state but hard to feel: the difference between a human-facing and agent-facing runbook is not a matter of detail or completeness. It is a matter of structure. A human reader has a runtime that fills in gaps. The reader interprets "check if widespread" by applying domain knowledge, experience, and judgment. An agent has none of these. It has the instructions. When the instructions are ambiguous, the agent does not pause and reflect — it infers. And inference in an on-call context produces the specific class of failure where the action taken is coherent, logical, and wrong.

---

**Dimension 1: Decision points**

Human-facing version's assumption: The operator knows how to assess the situation and will recognize when a threshold has been crossed.

Human-facing example: "If the problem is widespread, consider escalating to the payment gateway provider."

What an agent does when the assumption is not met: The agent interprets "widespread" as a binary decision with no named threshold. It may observe that 2 of 100 orders are failing, conclude that this is "not widespread" (because the majority succeed), and not escalate. Or it may observe that any orders are failing, conclude that this is "widespread" (because the product of the failure rate times the order volume is non-zero), and escalate immediately. Both inferences are internally consistent. Both can be wrong.

Specific production failure mode: An agent that does not escalate at 30% failure rate (because "most orders still succeed") allows a partial gateway outage to continue while inventory holds accumulate. When the holds expire (15 minutes per PAYMENT_PENDING order), orders that were pending but not completed are lost. The damage is not immediate — it accumulates silently.

---

**Dimension 2: Rollback steps**

Human-facing version's assumption: The operator knows which change to revert, knows how to verify the revert succeeded, and knows where to look to confirm it.

Human-facing example: "If you made configuration changes, revert them if the issue persists."

What an agent does when the assumption is not met: The agent must determine: which "configuration changes"? The last commit? All commits from the last hour? The commit that changed a specific file? "Revert" using which mechanism: `git revert`, `git reset`, restoring a file from backup? "If the issue persists" according to what measurement? The agent fills each of these gaps with inference. If it infers incorrectly — for example, if it uses `git reset --hard HEAD~1` instead of `git revert HEAD --no-edit` — it may discard uncommitted changes or revert a commit that was unrelated to the issue.

Specific production failure mode: An agent that uses `git reset --hard HEAD~1` to "revert" a configuration change will also silently remove any uncommitted findings notes written during the investigation. In this project, the findings file is the record of what was attempted. Losing it means the escalation has no incident history.

---

**Dimension 3: Escalation criteria**

Human-facing version's assumption: The operator knows what "persists" means, knows how long to wait, and knows who to escalate to.

Human-facing example: "Escalate if the issue persists or if you're unsure of the root cause."

What an agent does when the assumption is not met: "If you're unsure" is not a condition an agent can evaluate. An agent does not have uncertainty in the way a human does — it has a model of the situation and it acts on that model. If the model is wrong (because the runbook did not cover this failure mode), the agent is not "unsure" — it is wrong, and it does not know it is wrong. "Unsure" as an escalation trigger is invisible to an agent. The only escalation triggers an agent can evaluate are observable states: specific response codes, specific test failures, specific time thresholds.

Specific production failure mode: An agent that receives a symptom not covered by any runbook branch does not escalate — it infers a branch. If it infers incorrectly (for example, if it treats a contract violation as a timeout issue and follows the timeout mitigation branch), it may make changes that fix the symptom it inferred while leaving the real problem untouched — and active.

---

**Dimension 4: Environment assumptions**

Human-facing version's assumption: The operator knows which environment they are in and interprets all instructions accordingly.

Human-facing example (implicit): The entire runbook assumes the reader is operating on the correct service in the correct repository. This assumption is never stated.

What an agent does when the assumption is not met: An agent with access to multiple repositories, or operating in a session where the working directory is ambiguous, may execute runbook commands in the wrong repository. A `git revert HEAD --no-edit` in the wrong repository reverts the most recent commit in that repository — which may be unrelated to the payment gateway issue. There is no error message. The command succeeds. The wrong thing is reverted.

Specific production failure mode: An agent that reverts a commit in a shared infrastructure repository (because that was the working directory at the start of the session) rather than the order-api repository has just removed infrastructure changes that are unrelated to the current incident. The payment gateway issue is unresolved. A new infrastructure issue has been introduced. Both are now active.

---

**Dimension 5: Completion criteria**

Human-facing version's assumption: The operator knows what "functioning normally" looks like and knows which checks to run to confirm it.

Human-facing example: "Verify the service is functioning normally before closing the incident."

What an agent does when the assumption is not met: The agent runs some check and evaluates the output. If the check passes, the incident is closed. The agent's choice of which check to run determines whether the verification is meaningful. An agent might:
- Send a single successful GET /orders/{id} request and conclude the service is "functioning normally" — without checking whether new orders can be created
- Run the Gherkin suite but not the Pact suite — verifying behavioral tests but missing a contract drift
- Accept "all tests pass" as completion even when some tests were already failing before the incident (if the baseline was not documented)

Specific production failure mode: An agent that closes an incident after confirming one scenario passes has left an unverified system in an incident-closed state. If the fix resolved the timeout scenario but broke the payment-declined scenario (because a timeout change caused the stub delay to fall below the client timeout), the agent's verification did not catch the regression. The next order that is declined hits a broken code path.

---

### Why this matters

The five dimensions are not a taxonomy of runbook quality — they are a taxonomy of agent inference points. Every place where a human runbook says "check if," "consider," "if needed," or "verify" is a place where an agent must infer. The inferences are not random — they are coherent. The agent applies the information it has and reaches a conclusion that follows from that information. The conclusion is wrong when the information is insufficient. The damage is proportional to how consequential the action taken at that inference point was. The hardest class of failures is the one where the agent's action is plausible, produces no error, and makes the situation slightly worse in a way that is not immediately visible.

---

## Phase 2 — The human-facing runbook

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/runbooks/payment-gateway-degraded-human.md` — a realistic human-facing runbook that a competent on-call engineer would actually write and follow. Not a straw man.

### What happened

Writing a good human-facing runbook is not difficult. The standard structure (overview, symptoms, investigation, mitigation, rollback, escalation, post-incident) is well-understood. A competent engineer can write one in 30 minutes. The runbook I wrote is the kind of document that would pass review on a real team. It gives enough context to orient a new on-call engineer. It describes the failure mode accurately. It identifies the right investigation steps in the right order.

The judgment call analysis required was the hard part — not because the calls are obscure, but because they are so natural that they are invisible. A human reader reads "if the timeout is set aggressively, consider adjusting it" and immediately applies their knowledge of the codebase, the gateway's performance profile, and the test suite to inform their decision. The five judgment calls below are invisible to a human operator precisely because they are automatically filled in by context that the human carries. An agent carries none of it.

---

**Five judgment calls in the human-facing runbook:**

---

**1. "Check if the problem is widespread"**

Specific instruction quoted: "If the issue started shortly after a deployment to the order service or a change to the payment gateway configuration, that deployment is a likely cause."

Judgment call required: What counts as "shortly after"? 5 minutes? 2 hours? What if the issue started 4 hours after deployment but there were no other changes?

Failure mode if agent infers incorrectly: An agent that decides 4 hours is "not shortly after" disregards the deployment as a cause and looks elsewhere. If the issue was caused by a configuration change that only manifests under sustained load (which builds over 4 hours), the agent misses the root cause and applies a different mitigation. The real cause remains active.

---

**2. "Consider adjusting the timeout configuration if the gateway is responding slowly"**

Specific instruction quoted: "Consider adjusting the timeout configuration if the gateway's response time has increased significantly and legitimate orders are timing out unnecessarily."

Judgment call required: By how much to increase the timeout? The runbook says nothing about the relationship between `PAYMENT_TIMEOUT_SECONDS`, `MAX_PAYMENT_RETRIES`, and the worst-case latency constraint. It says nothing about the stub's `fixedDelayMilliseconds` or what happens when the timeout exceeds the stub delay.

Failure mode if agent infers incorrectly: **This is the specific instruction that earns Issue #18.** An agent that reads "the timeout is 5 seconds and the gateway is sometimes taking 6 seconds" increases `PAYMENT_TIMEOUT_SECONDS` to 7. The payment-timeout stub delays 6 seconds. The client timeout is now 7 seconds (7000ms). The stub responds at 6 seconds — before the 7-second client timeout fires. No `TimeoutException` is raised. The code receives HTTP 504 from the stub. The code's `if pay_resp.status_code == 200:` check fails. The code returns `PAYMENT_FAILED` instead of `PAYMENT_PENDING`. Scenario 5 fails. The agent has simultaneously (a) failed to fix the actual gateway degradation, (b) broken the timeout test scenario, and (c) changed the production code path for payment timeouts — all in one change that looks correct and produces no error during execution. The Gherkin test catches it, but only if the agent runs the test suite after the change. If the agent considers the fix applied and does not re-run the suite, the production code is broken and the incident is "closed."

---

**3. "Review recent changes to identify the root cause"**

Specific instruction quoted: "Review the changes in the most recent deployment."

Judgment call required: What does "most recent deployment" mean in a git repository with no formal deployment system? The last commit? The last commit to main? The last commit that touched a specific file? If there are 15 commits in the last 24 hours, how many does "most recent deployment" cover?

Failure mode if agent infers incorrectly: An agent that checks only the last commit misses a problematic change made 3 commits ago. An agent that checks the last 30 commits applies irrelevant context and may attribute the issue to an unrelated change.

---

**4. "Escalate if the issue persists"**

Specific instruction quoted: "Escalate to the engineering lead or the payment gateway provider if... the issue persists after investigation and standard mitigation."

Judgment call required: How long is "persists"? What counts as having completed "investigation and standard mitigation"? What if the issue is intermittent — does a 10-minute period with no failures count as "resolved"?

Failure mode if agent infers incorrectly: An agent that waits for a subjective "the issue has persisted long enough" may never escalate if the failure rate fluctuates. A 40% failure rate with intermittent recovery keeps the agent in a holding pattern indefinitely. Customers continue to experience failures. The runbook loop never exits.

---

**5. "Verify the service is functioning normally before closing"**

Specific instruction quoted: "Verify the service is functioning normally — orders are completing successfully and the payment gateway is responding within expected latency."

Judgment call required: What commands to run? What outputs confirm "functioning normally"? What is "expected latency"? Does a single successful order confirm the service is normal, or does a test suite need to pass?

Failure mode if agent infers incorrectly: An agent that manually tests one happy-path order and sees CONFIRMED treats the service as "functioning normally" — even if the timeout scenario, partial availability scenario, or payment-declined scenario are broken. The verification confirmed what the agent checked, not what needs to be verified.

---

## Phase 3 — The agent-facing runbook

**Date:** 2026-07-05
**Status:** ✅ Worked

### What I tried

Built `docs/runbooks/payment-gateway-degraded-agent.md` — a structured, agent-executable runbook with explicit decision trees, named commands, specific verification steps, and named completion criteria.

### What happened

The structural differences from the human-facing runbook are not cosmetic. Each structural element addresses a specific judgment call from Phase 2:

- **Pre-flight environment check (Section 1):** Addresses judgment calls 3 and 5 (root cause identification and verification). Every agent session starts by documenting baseline state — what was passing before any changes, what the contract state is. Without this, any subsequent test failure is ambiguous: is it a regression from this session, or was it already broken?

- **Explicit symptom decision tree (Section 2):** Addresses judgment call 1 (widespread determination). The runbook does not ask the agent to evaluate "how widespread." It asks the agent to match the observed response shape to a named branch. Five branches, four mitigation paths, one explicit catch-all (Branch E): if the symptom doesn't match, halt.

- **Worst-case latency formula in Step 2 (Section 3):** Addresses judgment call 2 (timeout adjustment). The runbook makes the constraint explicit: `PAYMENT_TIMEOUT_SECONDS × MAX_PAYMENT_RETRIES ≤ 12`. Any proposed timeout value must be checked against this formula before the change is made. No change that violates the formula can proceed.

- **"Obtain from gateway documentation, not from the stub file" in Step 3 (Section 3):** Addresses judgment call 2 specifically. The stub delay is not the gateway SLA. The runbook makes this distinction explicit — the decision requires external documentation, and if that documentation is unavailable, the decision cannot be made. The agent halts, not infers.

- **Named completion criteria (Section 7):** Addresses judgment call 5. Five specific checks, each with specific expected output. The incident is not closed until all five are green.

---

## Phase 4 — The gap analysis

**Date:** 2026-07-05
**Status:** ✅ Worked

| Dimension | Human-facing version | Agent-facing version | Production failure mode enabled by human version |
|---|---|---|---|
| Decision points | "If the problem is widespread, consider escalating" | Section 2: explicit five-branch decision tree; no inference required | Agent never escalates because "widespread" resolves to "not all orders fail" |
| Rollback steps | "Revert configuration changes if the issue persists" | Section 5: named commands (`git revert [hash] --no-edit`), verification step, explicit halt if revert fails | Agent uses `git reset --hard` instead of `git revert`, discards uncommitted findings notes |
| Escalation criteria | "Escalate if unsure or if the issue persists" | Section 6: five named HALT conditions; no judgment required | Agent cannot evaluate "unsure"; infers a branch for symptoms not covered by any branch; continues making changes |
| Environment assumptions | Implicit — assumes operator knows which repo and environment | Section 1 Step 1: explicit repo check before any action; HALT if wrong repo | Agent executes runbook commands in wrong repository; reverts unrelated commit in shared infrastructure repo |
| Completion criteria | "Verify the service is functioning normally" | Section 7: five named checks with specific expected outputs; incident not closed until all five pass | Agent runs one happy-path order, sees CONFIRMED, closes incident; timeout and declined scenarios remain broken |

---

## Phase 5 — Dry run results

**Date:** 2026-07-05
**Status:** ✅ Worked — one gap found and fixed

The agent-facing runbook was executed step by step against the current project state, using the existing payment-timeout stub (6000ms delay) as the simulated degraded gateway. Every command was run and its output documented.

---

### Pre-flight check outputs (Section 1)

**Step 1: Confirm correct repository**

Command: `git remote get-url origin`
Actual output: `https://github.com/kafka0nkoffee/lvl5engineer-order-api.git`
Contains "lvl5engineer-order-api": YES ✓
Result: PASS — proceed.

**Step 2: Confirm test suite baseline**

Command: `pytest tests/steps/ -v --tb=short`
Actual output: `11 passed, 3 warnings in 12.30s`
All tests passing: YES ✓
Result: PASS — proceed.

**Step 3: Document baseline contract state**

Command: `python3 scripts/can_i_deploy.py`
Actual output:
```
RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```
Result: PASS — proceed.

---

### Symptom identification (Section 2)

In the simulated scenario, the payment gateway is experiencing timeout behavior: orders placed with `payment_scenario: "timeout"` return:
```json
{
  "status": "PAYMENT_PENDING",
  "retry_count": 2,
  "inventory_hold_minutes": 15
}
```

Branch B matches: "IF orders are returning PAYMENT_PENDING with retry_count: 2 and inventory_hold_minutes: 15."

→ Proceed to Section 3: Gateway timeout mitigation.

---

### Section 3: Gateway timeout mitigation steps

**Step 1: Check current timeout configuration**

Command: `grep PAYMENT_TIMEOUT_SECONDS .env 2>/dev/null || grep PAYMENT_TIMEOUT_SECONDS app/main.py`
Actual output: `payment_timeout = float(os.environ.get("PAYMENT_TIMEOUT_SECONDS", "5"))`
Current value: 5 seconds

**Step 2: Check current retry configuration**

Command: `grep MAX_PAYMENT_RETRIES .env 2>/dev/null || grep MAX_PAYMENT_RETRIES app/main.py`
Actual output: `max_retries = int(os.environ.get("MAX_PAYMENT_RETRIES", "2"))`
Current value: 2 total attempts

Worst-case latency formula: `5 × 2 = 10 ≤ 12` ✓

**Step 3: Decision — adjust timeout or accept degraded mode?**

The runbook requires the gateway's documented SLA timeout from external documentation. In this project's test environment, no separate gateway documentation exists. The stub file (`wiremock/payment-mappings/payment-timeout.json`) shows `fixedDelayMilliseconds: 6000`, but the runbook explicitly states: "This must come from gateway documentation, not from the stub file." The stub delay is the test simulation of timeout behavior — it is not the gateway's SLA.

**Decision for the dry run:** The gateway SLA is unavailable from documentation in the test environment. Step 3 cannot be fully resolved. No timeout change was made. The dry run documents this decision point as a gap in the test environment context: in a real incident with a real gateway provider, the SLA timeout would be available from the provider's documentation. In the test environment, the stub delay serves as a proxy — but using it as such would require understanding that the stub delay must exceed the client timeout to trigger `TimeoutException`, and that increasing the client timeout above 6000ms would break Scenario 5.

**Step 4: Verification**

**GAP FOUND:** The original runbook command was:
```
pytest tests/steps/test_order_creation.py -v -k timeout
```
Actual output of this command:
```
collected 5 items / 5 deselected / 0 selected
(exit code 5 — no tests selected)
```

The `-k timeout` keyword does not match the test named `test_order_handling_is_graceful_when_the_payment_gateway_times_out` because the test name uses "times_out" (with underscore and past tense) not "timeout".

**Fix applied:** The runbook was updated to use the full test path:
```
pytest "tests/steps/test_order_creation.py::test_order_handling_is_graceful_when_the_payment_gateway_times_out" -v
```

After fix — actual output: `1 passed in 11.83s` ✓

This is the value of actually executing the dry run. The keyword filter produced exit code 5 (no tests selected) rather than a test failure — an ambiguous result that a runbook reader might interpret as "no timeout tests exist" or "the test framework is broken." Using the full test path produces an unambiguous result: PASSED.

---

### Section 4: Quick validation of gateway probe commands

The Section 4 investigation commands were also executed to verify their behavior outside an active pytest session:

`lsof -i :8091 | grep LISTEN` → no output (mock server not running)
`python3 -c "import httpx; r = httpx.post('http://localhost:8091/...')"` → `Unreachable: ConnectError: [Errno 61] Connection refused`

This is correct behavior: the mock server on port 8091 only runs inside an active pytest session (Invariant 5 — mock server lifecycle is owned by pytest session fixtures). Section 4's Step 2 documents this accurately. An on-call investigation that runs these probes outside a test session will see "unreachable" even when the server configuration is correct — which the runbook Step 1 explanation anticipates.

---

### Completion criteria check (Section 7)

**Criterion 1:** `pytest tests/steps/ -v` → 11 passed ✓
**Criterion 2:** `pytest tests/pact/ -v` → 4 passed ✓
**Criterion 3:** `python3 scripts/can_i_deploy.py` → "RESULT: ALL CONTRACTS VERIFIED" ✓
**Criterion 4:** PAYMENT_TIMEOUT_SECONDS: 5 (default), MAX_PAYMENT_RETRIES: 2 (default). Neither changed during this runbook ✓
**Criterion 5:** No code changes made during this dry run → no `ops:` commit required ✓

All five completion criteria met. The dry run is complete.

---

### Why this matters

The dry run produced one concrete finding: the `-k timeout` keyword filter selects zero tests in this project because the test name uses "times_out." This is not a subtle error — it is the kind of gap that only appears when the runbook is actually executed. A runbook that is written but never run is a runbook whose commands have never been validated. Runbook maintenance requires the same discipline as test maintenance: they must be executed, gaps must be found, and fixes must be applied before they are needed.

The most important gap the dry run did NOT find: Step 3's decision logic (check the gateway SLA timeout) works correctly for the real scenario it is written for. The structure — "obtain from external documentation, not the stub file" — prevents the specific dangerous inference described in Phase 2: an agent that uses the stub delay (6000ms) as the gateway's SLA timeout would conclude that increasing `PAYMENT_TIMEOUT_SECONDS` from 5 to 7 is correct, because 6000ms > 5000ms (the current timeout) suggests the client is too aggressive. The agent would be right about the comparison but wrong about the meaning. The stub delay is not the gateway's SLA — it is a simulation. The runbook prevents this inference by naming the source of the threshold explicitly.

---

## Phase 6 — Full suite verification

**Date:** 2026-07-05
**Status:** ✅ Worked

```text
pytest tests/steps/ -v → 11 passed
pytest tests/pact/ -v  → 4 passed
python3 scripts/can_i_deploy.py → RESULT: ALL CONTRACTS VERIFIED — safe to deploy
```

All 15 tests pass. No implementation changes were made during this session.

---

### Why this matters

The gap this session closes is specific. Issue #17 built evals that intercept agent intent before execution — pre-flight checks that run before a potentially risky action and ask: is this situation safe to proceed? The evals address the gap between "the agent wants to act" and "the action is safe." Runbooks address the adjacent gap: "the situation is already degraded, and the agent must act." In a degraded state, the agent cannot wait. It must make decisions. Those decisions require the same kind of explicit structure that evals provide for pre-action checks — explicit branches, named thresholds, verification steps with specific expected outputs.

The most important finding in this session is not the gap found in the dry run (the `-k timeout` keyword). It is the instruction in the human-facing runbook that reads: "Consider adjusting the timeout configuration if the gateway's response time has increased significantly." This sentence is the one that would cause an agent to take a damaging action that a human operator would not take. The human operator knows — from experience, from reading the codebase, from understanding the stub design — that increasing `PAYMENT_TIMEOUT_SECONDS` above 6 seconds changes the code path from `TimeoutException` to response handling. The agent does not know this. The agent reads "the timeout is 5 seconds, the gateway is taking 6 seconds, the runbook says to adjust the timeout," and sets `PAYMENT_TIMEOUT_SECONDS = 7`. The action is logical. It follows from the available information. It is wrong. And it breaks Scenario 5 without producing an error during execution.

The agent-facing runbook prevents this by doing two things. First, it requires the gateway's SLA timeout from documentation — not from the stub file. Second, it verifies after any change by running the full timeout scenario test with the specific command that exercises the actual code path. If the agent set `PAYMENT_TIMEOUT_SECONDS = 7`, the verification step would fail (stub responds at 6s before 7s timeout, code returns PAYMENT_FAILED, test expects PAYMENT_PENDING), and the runbook would instruct: revert immediately. The damage is caught before the runbook is closed. The instruction "verify after any change" is not abstract — it is a specific command with a specific expected output. That is the difference a runbook must provide for an agent that cannot fill gaps with judgment.
