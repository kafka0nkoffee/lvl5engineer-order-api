# Runbook: Payment Gateway Degraded

**Service:** Order API (port 8093)
**Trigger:** Payment gateway (port 8091) responding slowly, returning intermittent errors, or timing out
**Severity:** High — orders are failing or pending at the payment step

---

## Overview

This runbook covers the scenario where the payment gateway is degraded: orders are timing out at the payment step, returning unexpected errors, or not completing successfully. The order service handles payment timeouts gracefully (returning `PAYMENT_PENDING` with an inventory hold), so a degraded gateway does not necessarily mean immediate revenue loss. However, persistent degradation means orders are not being confirmed, which requires customer intervention.

The order service calls the payment gateway synchronously with a retry cap. If the gateway times out on both attempts, the order returns `PAYMENT_PENDING`. If the gateway declines, the order returns `PAYMENT_FAILED`. Intermittent gateway errors will appear as a mix of these outcomes.

---

## Symptoms

- Orders returning `PAYMENT_PENDING` more frequently than normal
- Orders returning `PAYMENT_FAILED` with no clear pattern (not a single customer or card)
- POST /orders completing slowly (approaching or exceeding 10 seconds)
- Payment gateway health check failing or returning 5xx responses
- Elevated error rates in payment gateway logs

---

## Before you start

Confirm you have access to:
- The order API application logs
- The payment gateway status page or health endpoint
- SSH or console access to the server running the order API
- The ability to restart or reconfigure the order service

---

## Investigation steps

### 1. Confirm the issue is the payment gateway, not the order service

Check if the order API is responding normally to requests that do not involve payment — for example, a GET /orders request for a known order ID. If the API itself is unresponsive, this is an order service issue, not a gateway issue. Stop here and escalate to the on-call for the order service infrastructure.

### 2. Establish when the issue started

Check recent deployments. If the issue started shortly after a deployment to the order service or a change to the payment gateway configuration, that deployment is a likely cause. Note the deployment time and the first occurrence of payment failures.

### 3. Check the payment gateway status

Review the payment gateway's status page or health endpoint. If the gateway is reporting an outage or degraded performance, this is an upstream issue outside the order service's control. Contact the payment gateway provider or your account team.

### 4. Identify the failure pattern

Review payment error logs to determine whether:
- All payment attempts are failing (gateway unreachable)
- A percentage of attempts are failing (gateway intermittently degraded)
- Specific amounts or card types are failing (merchant configuration issue)
- Failures are concentrated in a specific time window (transient event)

Document the approximate failure rate before proceeding.

### 5. Check the timeout configuration

Review the order service's timeout configuration. If the payment gateway has recently slowed down — responding in 4–6 seconds instead of its normal 1–2 seconds — and the order service timeout is set aggressively, legitimate requests may be timing out unnecessarily. Check the current timeout setting and consider whether it matches the gateway's current response profile.

### 6. Check the retry configuration

The order service retries failed payment attempts a limited number of times. Confirm the retry count is configured correctly. Too many retries extend the worst-case response time. Too few retries reduce resilience to transient errors.

---

## Mitigation steps

### If the gateway is temporarily unreachable

Check if the issue is transient. Payment gateways occasionally have brief outages of 1–5 minutes. If orders are returning `PAYMENT_PENDING`, the inventory hold provides a buffer. Monitor the situation for 10–15 minutes before making changes.

If the gateway remains unreachable, contact the gateway provider. There is no mitigation within the order service for a complete gateway outage — the service will continue to queue orders as `PAYMENT_PENDING` until the gateway recovers.

### If the gateway is responding slowly but not failing

Consider adjusting the timeout configuration if the gateway's response time has increased significantly and legitimate orders are timing out unnecessarily. A longer timeout allows the gateway more time to respond but increases the worst-case response time for the order API.

Any configuration change should be tested carefully. Make one change at a time. Monitor the effect before making additional changes.

### If the issue started after a recent deployment

Review the changes in the most recent deployment. If a configuration change, dependency update, or code change could have affected payment gateway behavior, consider reverting the deployment and observing whether the issue resolves.

If you revert, confirm the issue is resolved before closing the incident.

---

## Rollback

If mitigation steps involved configuration or code changes that did not resolve the issue, revert those changes. Use version control to identify what was changed and restore the previous state. Verify that the revert was applied correctly before continuing investigation.

---

## Escalation

Escalate to the engineering lead or the payment gateway provider if:
- The issue persists after investigation and standard mitigation
- You cannot identify the root cause
- The failure rate is high and orders are accumulating in `PAYMENT_PENDING` state
- You have made changes that worsened the issue

When escalating, include: the failure rate, when the issue started, what you have already tried, and the current system state.

---

## Post-incident

After the incident is resolved:
- Document what caused the issue and how it was resolved
- Check whether any configuration changes made during the incident should be made permanent or reverted
- Review whether the timeout and retry configuration is appropriate for the gateway's normal performance profile
- Verify the service is functioning normally — orders are completing successfully and the payment gateway is responding within expected latency
