# ADR-002: Notification delivery decoupled from order confirmation

**Status:** Accepted
**Date:** 2026-06-07 (Issue #7 — established and documented)
**Deciders:** Human author (newsletter)
**Covered code paths:** `app/main.py:_fire_notification()` and the call to it in `create_order()`

---

## Context

When an order is confirmed, the order service sends a notification to a notification service
(`POST /notifications/order-confirmed`). This call can be implemented in two ways:

**Synchronous (blocking):** The order confirmation response is held until the notification
service returns a success response. If the notification service is slow or unavailable, order
confirmation is delayed or fails.

**Asynchronous (fire-and-forget):** The notification call is started in a background thread.
The order confirmation response is returned immediately. The notification service's response
is not checked. Notification failures are discarded silently.

The key question is: which service's failure mode is worse?

- **Notification service outage with synchronous delivery:** All order confirmations fail.
  Customers cannot place orders. The notification service — a non-critical communication
  channel — has become a blocking dependency for the core transaction.

- **Notification service outage with fire-and-forget:** Notifications are not delivered.
  Customers are not notified of their order confirmation. Orders still succeed. The
  notification failure can be observed in logs and retried independently of the order flow.

These are different failure modes with very different business consequences.

---

## Decision

The notification service call must not block the order confirmation response. Order
confirmation success must not depend on notification delivery success.

Implementation:
- The notification call runs in a daemon thread (`threading.Thread(target=_send, daemon=True)`)
- All exceptions within the thread are caught and discarded silently
- The order confirmation response is returned before the notification call completes
- No retry logic for the notification call exists in the order service
- No success verification for the notification call exists in the order service

The notification service is responsible for its own delivery guarantees. The order service
guarantees only that it attempts to send a notification — not that the notification is
received or processed.

---

## Consequences

**Positive:**
- Order confirmation reliability is completely independent of notification service availability
- A notification service outage does not affect the core order transaction
- The order confirmation response time is not affected by notification service latency
- Customers can place orders even when the notification system is degraded

**Negative:**
- Notification delivery is not guaranteed by the order service
- Notification failures are silent — they produce no error, no retry, no alert from the
  order service (monitoring must be on the notification service side)
- There is no way for the order service to know whether a notification was delivered
- If delivery guarantees are required, they must be implemented in the notification service
  (with its own retry queue, dead-letter handling, etc.)

---

## Invariant statement

**The notification service call must not block the order confirmation response. Order
confirmation success must not depend on notification delivery success.**

The order service `_fire_notification()` function must:
1. Return before the notification HTTP call completes
2. Not raise exceptions if the notification call fails
3. Not check the notification response before the order confirmation is returned

---

## Dangerous improvements

These are changes that appear to improve reliability but violate this decision. An agent
encountering a task that resembles any of these must read this ADR before proceeding.

**1. Making the notification call synchronous for "more reliable delivery"**

Appears to guarantee delivery. Violates the invariant by coupling order confirmation
latency to notification service latency. If the notification service has a p99 of 500ms,
order confirmation p99 increases by 500ms. If the notification service goes down, order
confirmation fails. The correct improvement is to add reliability to the notification
service, not to block the order service on it.

**2. Adding retry logic in the order service for failed notification calls**

Appears to improve delivery rate. If implemented synchronously (retry before returning),
violates the invariant by blocking the order confirmation. If implemented in the background
thread, does not violate the invariant but creates an infinite-retry risk if the
notification service is persistently unavailable. Retry logic for notification delivery
belongs in the notification service, not the order service.

**3. Changing the order confirmation response to PENDING until notification delivery
is verified**

Appears to make the system more observable. Violates the invariant completely — order
confirmation status now depends on notification delivery status. A PENDING order is
not a CONFIRMED order. This change couples the order state machine to the notification
service in a fundamental way.

**4. Adding a notification delivery check as a step in the order confirmation flow
(e.g., polling a status endpoint before returning CONFIRMED)**

Appears to add observability without fully blocking. Violates the invariant: the order
confirmation response is now delayed by at least one additional HTTP call (the status
check). This is synchronous coupling with extra steps.

---

## Agent check

Answer all three questions before modifying `_fire_notification()` or the notification
call in `create_order()`:

**Q1: Does my change allow the order confirmation response to be returned before the
notification call completes?**

If the order confirmation HTTP response is sent to the client before the notification
HTTP request has received a response from the notification service, the answer is YES.
If the order confirmation response is held until the notification call completes (or
fails), the answer is NO.

Answer must be YES to proceed.

**Q2: Does my change allow the order confirmation status to be CONFIRMED even when the
notification service is unavailable (returning 503 or connection refused)?**

Simulate notification service unavailability. If the order still returns CONFIRMED with
a notification service that is down, the answer is YES.

Answer must be YES to proceed.

**Q3: Do both notification service scenarios in `notification_service.feature` still pass
without modification?**

Specifically: does "Order is confirmed even when notification service is unavailable"
still pass? This scenario directly tests the decoupling invariant — it confirms that
the order remains CONFIRMED when the notification service fails.

Answer must be YES to proceed.

---

## Consequence table

These test outcomes indicate an ADR-002 violation. If you observe any of the following,
review this ADR before committing:

| Observation | Violation indicated |
|---|---|
| `notification_service.feature` Scenario 2 ("order confirmed when notification fails") fails | Order confirmation now depends on notification success |
| Order confirmation response time increases when notification service is slow | Notification call is now blocking |
| Order confirmation returns a non-CONFIRMED status when notification service is unavailable | Order state now coupled to notification state |
| `_fire_notification()` now returns a value that is checked in `create_order()` | Notification result is affecting order outcome |

If `notification_service.feature` Scenario 2 requires modification to pass after your
change: the spec was changed to accommodate the violation. This is a spec violation, not
a code fix. Do not modify the notification service scenarios to make a synchronous
implementation pass.
