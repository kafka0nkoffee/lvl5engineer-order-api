# GOOD SPEC FILE — order_status_good.feature
#
# This file rewrites the same two scenarios from order_status_bad.feature.
# Same endpoint. Same two situations. Different spec quality.
#
# Here is what changed and why each change matters:
#
# === Scenario 1 rewrite: "Confirmed order status returns status and timestamp" ===
#
# CHANGE: Removed "db_status" — replaced with "status"
# WHY: "db_status" exposes internal naming. The field the caller sees should be
# named for the caller's domain ("status"), not the storage layer's domain
# ("db_status"). This lets the implementation rename its internal field without
# breaking the API contract. The spec now constrains the output, not the internals.
#
# CHANGE: Removed "populated from the order record"
# WHY: "Populated from the order record" describes mechanism, not outcome. The spec
# should say what format the timestamp takes and what it represents, not where it
# comes from. Replaced with an explicit ISO 8601 format assertion and a field name
# that reflects the caller's perspective ("placed_at" instead of "order_created_at").
#
# CHANGE: Added "And the response includes the order_id"
# WHY: A status response that doesn't echo the order_id forces the caller to track
# which response belongs to which request when making concurrent calls. The bad spec
# never mentioned this field. The good spec makes it explicit because it is part of
# the observable contract.
#
# === Scenario 2 rewrite: "Unknown order ID returns 404 with error message" ===
#
# CHANGE: Replaced "an order that has not been placed" with an explicit UUID setup
# WHY: "Has not been placed" is ambiguous — it could mean never-created, deleted,
# expired, or draft. The rewrite uses "a valid order ID that does not correspond
# to any order in the system" to make the exact system state unambiguous. The agent
# no longer needs to guess what "not been placed" means.
#
# CHANGE: Added "And the response body contains an error field"
# WHY: The bad spec only checked the status code. A 404 with no body is a 404.
# A 404 with a structured error is a usable API. The good spec makes the error
# field an explicit contract requirement, so callers can rely on it.
#
# CHANGE: Used a well-formed UUID as the unknown ID
# WHY: The bad spec used "nonexistent-id" — a string that is not a valid UUID.
# An agent implementing ID validation could reasonably return 422 for that input
# instead of 404, and the bad spec would fail for a different reason than intended.
# The good spec removes this ambiguity by using a correctly-formatted UUID that
# simply doesn't exist in the system.

Feature: Order status retrieval (good specs — behavioural contract)

  Scenario: Confirmed order status returns status and timestamp
    Given an order was created via POST /orders and confirmed with order ID "aaa00000-0000-0000-0000-000000000001"
    When a client requests the status of order "aaa00000-0000-0000-0000-000000000001"
    Then the response HTTP status is 200
    And the response body contains a "status" field with value "CONFIRMED"
    And the response body contains a "placed_at" field in ISO 8601 format
    And the response body contains an "order_id" field with value "aaa00000-0000-0000-0000-000000000001"

  Scenario: Unknown order ID returns 404 with error message
    Given no order exists with ID "ffffffff-ffff-ffff-ffff-ffffffffffff"
    When a client requests the status of order "ffffffff-ffff-ffff-ffff-ffffffffffff"
    Then the response HTTP status is 404
    And the response body contains an "error" field
