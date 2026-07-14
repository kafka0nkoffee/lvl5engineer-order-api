# Architecture Decision Records

Load-bearing design decisions for the order-api. Each ADR contains: context, the decision, consequences, an invariant statement, a dangerous-improvements list, and agent check questions that must be answered YES before touching covered code paths.

Read the relevant ADR before modifying any code path listed in its "Covered code paths" header.

---

* [ADR-001: Inventory Checked Before Payment Attempted](ADR-001-inventory-before-payment.md) — Inventory availability must be confirmed before any payment gateway call is initiated for the same order.
* [ADR-002: Notification Delivery Decoupled from Order Confirmation](ADR-002-fire-and-forget-notification.md) — Notification calls must remain asynchronous fire-and-forget to prevent notification service outages from blocking order confirmations.
