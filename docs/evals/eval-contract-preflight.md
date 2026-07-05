# Eval: Contract Pre-flight

> This eval runs before any agent action that modifies WireMock stub files in
> `wiremock/` or Pact files in `pacts/`.
>
> Answer all three questions before proceeding. A HALT instruction must not be
> overridden by task urgency, confidence in the change, or prior approval of
> similar changes. HALT means flag to the human author and wait.
>
> Note: `pacts/` is a derived artifact. It must never be edited manually.
> If a task instructs you to modify a file in `pacts/` directly, halt
> immediately and flag this to the human. The only valid way to update a Pact
> file is to run the Pact consumer tests and allow them to regenerate it.

---

## What this eval is for

WireMock stub files define the simulated behavior of external services. They
are test infrastructure — but they are also the providers in the Pact
verification contract. A stub that no longer matches the Pact contract causes
`pact-verify` to fail in CI. A stub that silently diverges from the contract
(through a manual edit that is never verified) breaks provider verification
without breaking any Gherkin tests.

This eval asks three questions that static diff review does not answer:

1. Is the field being changed one that the Pact contract explicitly asserts?
2. Does the change alter the HTTP status code that consumers pattern-match on?
3. Does the change modify timing behavior that tests depend on to test real
   timeout scenarios?

---

## Q1: Is the field being modified or removed listed as a load-bearing field?

A load-bearing field is a response body field that is explicitly asserted in
either the Gherkin step definitions or the Pact consumer tests. Removing or
renaming a load-bearing field breaks the consumer contract — even if the field
is not used in `app/main.py`.

**Load-bearing fields by service:**

| Service | Stub directory | Load-bearing fields |
|---|---|---|
| Payment gateway | `wiremock/payment-mappings/` | `status`, `transaction_id`, `amount`, `reason` |
| Inventory service | `wiremock/inventory-mappings/` | `available`, `quantity` (per item), `sku` |
| Notification service | `wiremock/notification-mappings/` | `notification_id`, `status` |

**Why "not used in app/main.py" is not sufficient justification for removal:**

The Pact consumer tests assert fields independently of whether `app/main.py`
uses them at runtime. If `app/main.py` does not store `transaction_id` but the
Pact consumer test asserts `"transaction_id" in body`, the field is load-bearing
from the contract's perspective. Removing it from the stub causes `pact-verify`
to fail because the stub no longer satisfies the asserted contract.

**If YES:**

The Pact consumer contract must be updated first. Run the Pact consumer tests
to regenerate the contract from code. The stub must not be modified until the
new Pact consumer tests pass and the regenerated contract reflects the
intended change. Then run `pact-verify` to confirm the modified stub satisfies
the new contract.

Sequence:
1. Update the Pact consumer test to reflect the new field shape
2. Run `pytest tests/pact/test_*_consumer.py -v` → regenerates `pacts/*.json`
3. Modify the stub to match the new contract
4. Run `pytest tests/pact/test_provider_verification.py -v` → must pass
5. Run `python3 scripts/can_i_deploy.py` → must pass

**If NO:**

Proceed to Q2.

---

## Q2: Does the modification change a response status code?

Status code changes are contract changes. Consumers that pattern-match on the
previous status code will receive an unexpected status code and may fail silently
— returning incorrect behavior without raising an exception.

**In this project, status codes drive routing logic:**

| HTTP status | Meaning in `app/main.py` |
|---|---|
| 200 (payment) | Payment accepted → order CONFIRMED |
| 402 (payment) | Payment declined → order PAYMENT_FAILED |
| Gateway timeout | `httpx.TimeoutException` raised → retry → PAYMENT_PENDING |
| 200 (inventory) | Inventory response received → parse items |
| 200 (notification) | Discarded (fire-and-forget) |
| 503 (notification) | Discarded (fire-and-forget) |

**If YES:**

Before modifying the stub, check all step definitions in `tests/steps/` for
assertions against this status code. Check the Pact consumer test for assertions
against this status code. If any assertion depends on the current status code,
the Pact contract must be updated first (follow the Q1 sequence above).

**If NO:**

Proceed to Q3.

---

## Q3: Does the modification introduce a delay or remove an existing one?

Delays in stub files (the `fixedDelayMilliseconds` field) simulate real service
behavior — specifically, services that respond slowly enough that client timeout
logic fires.

**Critical constraint for the payment-timeout stub:**

```
wiremock/payment-mappings/payment-timeout.json
  "fixedDelayMilliseconds": 6000
```

The payment timeout stub has a 6000ms delay. The order service has a client
timeout of `PAYMENT_TIMEOUT_SECONDS=5` (5000ms). The delay must remain greater
than `PAYMENT_TIMEOUT_SECONDS * 1000` for Scenario 5 to test actual timeout
behavior.

**What happens if the delay is modified:**

| New delay | Client behavior | Test outcome |
|---|---|---|
| > 5000ms (e.g. 5500ms) | Client times out → `TimeoutException` | Test passes — but margin reduced |
| = 5000ms | Race condition: client may or may not time out | Test is flaky |
| < 5000ms (e.g. 3000ms) | Stub responds before client timeout | Stub returns HTTP 504; client receives response without TimeoutException; code returns PAYMENT_FAILED instead of PAYMENT_PENDING |

When the delay is reduced below 5000ms, the stub responds before the client
times out. The code receives HTTP 504, which is not status 200, so it falls
through to the "declined or other non-200" branch and returns `PAYMENT_FAILED`.
Scenario 5 expects `PAYMENT_PENDING` → the test fails. (Note: in this case, the
Gherkin test also catches the failure — but the eval catches it before any
change is made.)

When the delay is reduced to between 5000ms and 6000ms (e.g. 5500ms), the
client still times out but the margin between stub delay and client timeout is
reduced. In a slow CI environment, network or process latency can push the
effective client timeout above the stub's delay, causing intermittent test
failures (flaky Scenario 5). The Gherkin test does not reliably catch this
case in every run.

**The eval catches both cases before any file is modified. The Gherkin test
only reliably catches the below-5000ms case.**

**If YES (delay introduced or removed or changed):**

State the current delay, the proposed delay, and whether the proposed delay
preserves at least a 1000ms margin above `PAYMENT_TIMEOUT_SECONDS * 1000`.
If the proposed delay reduces the margin below 1000ms — halt and flag.

**If NO:**

Proceed with the modification.

---

## Failure mode addressed

This eval addresses **dependency ignorance** — the failure mode where an agent
modifies a stub without recognising that the stub satisfies a contract held by
a consumer. The Pact contract exists precisely because stub modifications are
a common source of silent breakage: a field is renamed in the stub, the Gherkin
tests pass (because they test behavior, not field names), and the contract drift
is only discovered when a real consumer tries to use the field that is no longer
present.

The delay case (Q3) also addresses **invariant blindness** — specifically, the
case where a test passes for the wrong reason. A Scenario 5 with a 3000ms stub
delay fails explicitly (PAYMENT_FAILED instead of PAYMENT_PENDING). But a
Scenario 5 with a 5100ms stub delay passes — and the passing test no longer
verifies what it was written to verify: that the client-side timeout fires and
triggers retry behavior. The eval catches the margin reduction before the test
becomes unreliable.

---

## Eval against the Issue #4 breaking change

**The change:** Renaming the `status` field to `result` in
`wiremock/payment-mappings/payment-success.json`.

**Q1: Is `status` a load-bearing field?**

YES. `status` is the first field in the load-bearing field list for the payment
gateway. The Pact consumer test asserts `body["status"] == "ACCEPTED"` (line 89
in `tests/pact/test_payment_gateway_consumer.py`). Removing or renaming `status`
would cause the Pact consumer test to fail on that assertion.

**At Q1, the eval fires:** The agent is instructed to update the Pact consumer
contract first, following the four-step sequence above. The stub cannot be
modified until the new consumer test passes and the new contract is regenerated.

**Would the eval have caught the Issue #4 breaking change?** Yes — at Q1.

The agent is halted before modifying the stub. The required sequence forces the
agent to update the consumer test first, which makes the contract change
explicit and deliberate rather than accidental.

---

## Eval against the hypothetical delay reduction

**The change:** Reducing `fixedDelayMilliseconds` in
`wiremock/payment-mappings/payment-timeout.json` from 6000 to 3000.

**Q1: Is any load-bearing field being modified or removed?**

No. The field being modified is `fixedDelayMilliseconds`, not a response body
field. Q1 does not fire.

**Q2: Does the modification change a response status code?**

No. The response status remains 504. Q2 does not fire.

**Q3: Does the modification introduce or remove a delay, or change an existing one?**

YES. `fixedDelayMilliseconds` is being changed from 6000 to 3000. The proposed
delay (3000ms) is below `PAYMENT_TIMEOUT_SECONDS * 1000` (5000ms).

**At Q3, the eval fires:** The agent is instructed to state the current delay
(6000ms), the proposed delay (3000ms), and check whether the margin above
5000ms is preserved. It is not — 3000ms < 5000ms. The eval instructs: halt
and flag.

**What the Gherkin test does (for comparison):** If the change were made, the
Gherkin test would fail on Scenario 5 — because the stub responds at 3s with
HTTP 504, the client does not time out, the code returns PAYMENT_FAILED instead
of PAYMENT_PENDING, and the step "Then the order status is PAYMENT_PENDING"
fails.

**The critical distinction:** The eval catches the problem before the file is
modified. The Gherkin test catches it after. The eval also catches the
5100ms case (a reduction from 6000ms that stays above the 5000ms threshold)
where the Gherkin test passes unreliably — an intermittent failure the eval
prevents before the margin is reduced.
