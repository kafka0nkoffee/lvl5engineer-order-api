# Issue #5 — The Spec That Doesn't Lie

**Date:** 2026-06-02
**Session:** Demonstrating how spec quality determines implementation quality, not just test pass/fail

---

## Phase 1 — Writing deliberately bad Gherkin scenarios

**Date:** 2026-06-02
**Status:** ✅ Worked (as intended — bad specs are easy to write)

### What I tried

Wrote two bad Gherkin scenarios for `GET /orders/{order_id}/status` in
`tests/features/order_status_bad.feature`. The goal was to produce specs that are
syntactically valid, produce passing tests, but leave the agent with decisions to
make that the spec should have made for it.

### What happened

Both scenarios were written without difficulty. This is itself a finding: bad specs
are hard to spot when you're writing them because they feel complete. The leaky spec
references implementation details that sound like reasonable description. The vague
Given sounds specific enough on first read.

### Root cause

Gherkin is a human-readable format, so it is easy to write prose that *sounds*
like a precise behavioural contract but is actually a paraphrase of the author's
internal mental model. The agent then has to reconstruct that model from the paraphrase.

### The fix

N/A — this phase is intentional. See Phase 3 for the rewrite.

### Why this matters

The hardest thing about writing good specs isn't the syntax — it's recognising that
the reader (agent or human) doesn't share your mental model of the system. A scenario
that describes implementation details feels precise because you wrote the implementation.
A Given that feels obvious to you will be filled in differently by every reader who
hasn't seen the code.

---

## Phase 2 — Implementing from bad specs

**Date:** 2026-06-02
**Status:** ✅ Worked (tests pass — this is the point)

### What I tried

Implemented `GET /orders/{order_id}/status` in `app/main.py` based solely on
`tests/features/order_status_bad.feature`. Wrote step definitions in
`tests/steps/test_order_status_bad.py` and ran the test suite.

### What happened

```
============================= test session starts ==============================
platform darwin -- Python 3.14.0, pytest-9.0.3, pluggy-1.6.0
collected 2 items

tests/steps/test_order_status_bad.py::test_retrieving_status_for_a_confirmed_order PASSED [ 50%]
tests/steps/test_order_status_bad.py::test_retrieving_status_for_an_order_that_does_not_exist PASSED [100%]

========================= 2 passed, 1 warning in 0.34s =========================
```

Both pass. Nothing in the output signals that anything is wrong. This is the point.

### Bad-spec implementation (from app/main.py at this point)

```python
@app.get("/orders/{order_id}/status")
def get_order_status(order_id: str):
    order = _orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": order_id,
        "db_status": order["db_status"],
        "order_created_at": order["order_created_at"],
    }
```

### Silent assumptions made by the bad-spec implementation

**Assumption 1: The order store is in-memory (a dict)**
The spec says nothing about persistence. An in-memory dict is the simplest possible
thing that makes the tests pass. In production, orders are persisted. The assumption
is correct for tests, dangerous for production — the in-memory store vanishes on
restart and is not shared across worker processes.

**Assumption 2: A missing order_id returns 404**
The spec describes what happens when an order exists. It says nothing about what
happens when it doesn't. 404 is a defensible guess. But the spec could also have
intended 422 (malformed request), 403 (unauthorised), or a generic 200 with a
`NOT_FOUND` status field — all of which have different client-handling implications.

**Assumption 3: The field is named `db_status` in the response**
The spec says `db_status` — so the agent uses `db_status`. It never questions whether
this is an internal name leaking into the API. It satisfies the spec literally.

**Assumption 4: The timestamp field is named `order_created_at` and has no format requirement**
The spec says "populated from the order record." The agent chooses `order_created_at`
as the field name and returns an ISO string because that's what `datetime.utcnow().isoformat()`
produces. But the spec never mandated ISO 8601. The step definition checked only that
the field is non-empty and a string — so any format would pass.

**Are these assumptions correct, defensible, or dangerous?**

| Assumption | Verdict |
|---|---|
| In-memory store | Correct for tests, dangerous in production |
| 404 for missing ID | Defensible, but not specified |
| `db_status` field name | Technically correct per spec — but the spec is wrong |
| Unspecified timestamp format | Dangerous — any string passes, including garbage |

---

## Phase 3 — Rewriting the specs

**Date:** 2026-06-02
**Status:** ✅ Worked

### What I tried

Rewrote both scenarios in `tests/features/order_status_good.feature`. Same endpoint,
same two situations, but with implementation detail removed and all implicit state
made explicit.

### What happened

Writing the good spec forced decisions that the bad spec had silently delegated to
the agent:

- What field name should the caller see? (`status`, not `db_status`)
- What is the timestamp field called from the caller's perspective? (`placed_at`)
- What format must the timestamp be in? (ISO 8601, explicitly asserted)
- Should the response echo the `order_id`? (Yes — specified as a contract obligation)
- What exactly is "an order that has not been placed"? (A well-formed UUID with no
  corresponding record in the system)
- What should the 404 response body look like? (Must contain an `error` field)

Each of these was an assumption in the bad spec. Each is now a concrete requirement.

### Root cause

The bad spec was written from the implementation's perspective — it described what
the code did. The good spec was written from the caller's perspective — it describes
what the caller can rely on. The two perspectives produce very different Gherkin even
when describing the same outcome.

---

## Phase 4 — Implementing from good specs

**Date:** 2026-06-02
**Status:** ✅ Worked (good spec tests pass; bad spec tests partially fail)

### What I tried

Removed the bad-spec implementation and rebuilt `GET /orders/{order_id}/status`
from scratch using only `tests/features/order_status_good.feature`. Wrote step
definitions in `tests/steps/test_order_status_good.py`.

Then ran the bad-spec tests against the new implementation to see what breaks.

### Good spec tests passing

```
============================= test session starts ==============================
collected 2 items

tests/steps/test_order_status_good.py::test_confirmed_order_status_returns_status_and_timestamp PASSED [ 50%]
tests/steps/test_order_status_good.py::test_unknown_order_id_returns_404_with_error_message PASSED [100%]

============================== 2 passed in 0.17s ===============================
```

### Bad spec tests against new implementation

```
============================= test session starts ==============================
collected 2 items

tests/steps/test_order_status_bad.py::test_retrieving_status_for_a_confirmed_order FAILED [ 50%]
tests/steps/test_order_status_bad.py::test_retrieving_status_for_an_order_that_does_not_exist PASSED [100%]

FAILURES
_________________ test_retrieving_status_for_a_confirmed_order _________________

    @then(parsers.parse('the response should contain the db_status field set to "{expected}"'))
    def check_db_status(expected):
        body = _response["result"].json()
>       assert body["db_status"] == expected
               ^^^^^^^^^^^^^^^^^
E       KeyError: 'db_status'

tests/steps/test_order_status_bad.py:58: KeyError
==================== 1 failed, 1 passed, 1 warning in 0.21s ====================
```

The bad-spec leaky test (`db_status`) fails against the good implementation.
The bad-spec vague test (404 for missing) passes — because the good spec happened
to reach the same conclusion, but for an explicit reason this time.

This asymmetry is instructive: the vague Given produced the right answer by coincidence.
The leaky Then produced the wrong field name by construction.

---

## Phase 5 — The comparison

**Date:** 2026-06-02
**Status:** ✅

### Implementation 1: built from bad spec

```python
@app.get("/orders/{order_id}/status")
def get_order_status(order_id: str):
    order = _orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": order_id,
        "db_status": order["db_status"],        # named after the storage field
        "order_created_at": order["order_created_at"],  # named after the record field
    }
```

### Implementation 2: built from good spec

```python
@app.get("/orders/{order_id}/status")
def get_order_status(order_id: str):
    order = _orders.get(order_id)
    if order is None:
        return JSONResponse(status_code=404, content={"error": "Order not found"})
    return {
        "order_id": order_id,
        "status": order["db_status"],           # named for the caller's domain
        "placed_at": order["order_created_at"], # named for the caller's domain
    }
```

### Assumption-by-assumption comparison

**Assumption 1: Field name `db_status` vs `status`**

The bad spec named the field `db_status`. The agent used that name literally.
The good spec named the field `status` — the caller's concept, not the storage concept.

These are different APIs. A mobile client built against the bad implementation would
send `db_status` in display logic, error handling, and conditional rendering. When
the endpoint is refactored under the good spec (or when the team decides `db_status`
is an embarrassing name and renames it), every client breaks.

**Assumption 2: Timestamp field name and format**

Bad spec: `order_created_at`, format unspecified, checked only for non-emptiness.
Good spec: `placed_at`, format must be ISO 8601, asserted by `datetime.fromisoformat()`.

A client relying on `order_created_at` being parseable as a date would work — until
a different agent, satisfying the same bad spec, returns a Unix timestamp integer
instead. The bad spec allows it. The bad-spec step definition allows it. The good
spec's step definition would fail immediately.

**Assumption 3: 404 response body structure**

Bad spec: `HTTPException(status_code=404, detail="Order not found")` — FastAPI wraps
this as `{"detail": "Order not found"}`. No `error` field.

Good spec: `JSONResponse(status_code=404, content={"error": "Order not found"})` —
returns `{"error": "Order not found"}` directly.

A client checking `response.json()["error"]` would get a `KeyError` on the bad
implementation. This is the vague Given's practical consequence: it said nothing
about the 404 body shape, so the agent chose the default FastAPI shape, which is
`detail`, not `error`.

**Production scenario where the bad assumption causes a problem**

The mobile team ships a version that displays `order.db_status` in the order history
screen. Three months later, a refactor renames the field to `status` (the obviously
correct name — the old name was always weird). The mobile app goes dark on order
history for all users running the old version. The fix is a forced app update.
The root cause traces back to a spec that named an internal concept instead of the
observable one.

### Why this matters

Both implementations pass their own test suites. That is the trap. If you run the
bad-spec tests against the bad-spec implementation, you get green. If you run the
good-spec tests against the good-spec implementation, you get green. The difference
only surfaces when you cross-run — and in production, you never cross-run. You ship
the bad implementation, it passes CI, and the problem lands in a client exception
report six months later.

The concrete difference is this: the bad-spec implementation returns `db_status` and
`order_created_at` with no format guarantee. The good-spec implementation returns
`status` and `placed_at` with a mandatory ISO 8601 format. These are not the same
API. An agent given the bad spec had no way to know that `db_status` was wrong —
the spec said `db_status`. An agent given the good spec had no choice but to produce
`status` — the spec said `status`. Spec quality is not about whether tests pass. It
is about how much of the implementation the spec author wrote versus how much was
silently delegated to the agent. Every silent delegation is a place where two agents
given the same spec produce different code — code that both passes, but disagrees on
the contract. At scale, that disagreement is the system.

---

## Phase 6 — Full suite regression

**Date:** 2026-06-02
**Status:** ✅

### What I tried

Ran `pytest tests/steps/test_order_creation.py -v` to confirm all 5 original
scenarios still pass with the new endpoint added.

### What happened

```
============================= test session starts ==============================
platform darwin -- Python 3.14.0, pytest-9.0.3, pluggy-1.6.0
collected 5 items

tests/steps/test_order_creation.py::test_order_is_successfully_created_when_payment_succeeds_and_all_items_are_in_stock PASSED [ 20%]
tests/steps/test_order_creation.py::test_order_is_rejected_when_payment_is_declined PASSED [ 40%]
tests/steps/test_order_creation.py::test_order_is_rejected_when_an_item_is_out_of_stock PASSED [ 60%]
tests/steps/test_order_creation.py::test_order_surfaces_partial_unavailability_without_autoconfirming PASSED [ 80%]
tests/steps/test_order_creation.py::test_order_handling_is_graceful_when_the_payment_gateway_times_out PASSED [100%]

======================== 5 passed, 1 warning in 12.03s =========================
```

All 5 original scenarios pass. The new endpoint did not break any existing behaviour.

### Root cause

The new endpoint is additive — a GET on a new path. The existing POST /orders
behaviour is unchanged. The only modification to the create path was seeding the
in-memory order store when an order is confirmed, which is a new side effect that
the existing tests do not observe (they only check the POST response body).

### Why this matters

Additive changes to an API that is tested at the HTTP level are low regression risk
precisely because HTTP tests are path-scoped. The value of the Gherkin suite here
is not regression detection (the new endpoint can't break old paths) — it is
documentation. Any future agent reading these scenarios knows exactly what POST
/orders must return and what invariants must hold. The spec is the memory.
