# Issue #2 — WireMock + Gherkin BDD Setup
**Newsletter issue:** [The Bottleneck Moved. Did You Notice?](#)
**Session date:** 2026-05-01
**Related phases:** Phase 1 (Simulate External Dependencies), Phase 2 (Write External Behavioural Scenarios)

---

## Shared call log bug — payment calls not being verified
**Status:** ❌ Failed → ✅ Fixed

### What I tried
Started with a single `MockServer` class holding a class-level call log shared across
both the payment and inventory mock servers.

### What happened
The inventory call was being recorded correctly but the payment call wasn't showing up
in verification assertions. The test for "payment gateway received exactly one charge
request" was failing even when the payment server was being called.

### Root cause
Both mock servers (payment on port 8081, inventory on 8082) were recording into the
same shared list. Because the inventory server matched first on some requests, its
calls were overwriting the position in the log that the payment assertion was checking.

### The fix
Gave each mock server instance its own `MockCallLog` object rather than sharing a
class-level singleton:

```python
def start_mock_server(port: int, mappings_dir: str) -> tuple[HTTPServer, MockCallLog]:
    stubs = [json.loads(f.read_text()) for f in Path(mappings_dir).glob("*.json")]
    log = MockCallLog()  # ← per-instance, not shared
    handler = make_handler(stubs, log)
    server = HTTPServer(("localhost", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, log
```

### Why this matters
This mirrors exactly how real WireMock works in production — you run separate WireMock
instances per service, each with its own request journal. The shared singleton was a
shortcut that obscured a real architectural decision. When you're running multiple mock
services in a test suite, their call logs must be isolated or your assertions become
meaningless. The fix isn't just about making the test pass — it's about making the
test mean what it says.

---

## 404 passthrough silent success — unmatched stubs treated as success
**Status:** ❌ Failed → ✅ Fixed

### What I tried
When a request came in that no WireMock stub could match, the mock server returned a
404 with `{"error": "No stub matched"}`. The API called `pay.json()` on this response
and treated the result as a successful payment.

### What happened
Tests were passing even when the mock wasn't configured correctly. An order was being
confirmed with an `order_id` despite no real payment stub having been matched.

### Root cause
A 404 is not an exception in `httpx` — it's just a response. The original API code
didn't check the status code before parsing the response body.

### The fix
Added an explicit check after every downstream call:

```python
pay = httpx.post(f"{PAYMENT_URL}/payments/charge/{scenario}", ...)
if pay.status_code == 404:
    raise HTTPException(503, f"Payment scenario not found: {scenario}")
payment_result = pay.json()
```

### Why this matters
A misconfigured mock would have made every test pass while hiding that the real
service path was broken. This is genuinely dangerous — not a test annoyance but a
false signal that your integration works when it doesn't. Always explicitly check
the response status from a mock. Unmatched stubs should be loud, not silent.

---

## pytest-bdd fixture wiring gap — missing payment_scenario for scenarios 3 and 4
**Status:** ❌ Failed → ✅ Fixed

### What I tried
Scenarios 3 (out of stock) and 4 (partial availability) don't define a payment
scenario in their Given clauses because the payment gateway should never be called.
pytest-bdd still expected the `payment_scenario` fixture to exist.

### What happened
Tests for scenarios 3 and 4 errored out before even running — fixture not found.

### Root cause
The test wiring assumed every scenario would define a payment scenario. The spec was
correct. The step definitions had a gap.

### The fix
Added a default fixture that returns `"success"` and is overridden by specific
Given steps when needed:

```python
@pytest.fixture
def payment_scenario():
    """Default — overridden by specific Given steps."""
    return "success"
```

### Why this matters
The Gherkin spec said exactly the right thing — scenarios 3 and 4 shouldn't mention
payment because payment is irrelevant to them. The error was in the test wiring, not
the spec. This distinction matters: when a test fails, always ask whether the spec
is wrong or the implementation of the spec is wrong. They are different problems
with different fixes.
