# BAD SPEC FILE — order_status_bad.feature
#
# This file contains deliberately bad Gherkin scenarios for GET /orders/{order_id}/status.
# Both scenarios are syntactically valid and will produce passing tests.
# Neither scenario is a good behavioural specification. Here is why:
#
# === Scenario 1: "Retrieving status for a confirmed order" ===
#
# This is a LEAKY SPEC. The problem is in the Then clause:
#
#   Then the response should contain the db_status field set to "CONFIRMED"
#   And the order_created_at timestamp should be populated from the order record
#
# "db_status" is an implementation detail — it names the field as it exists
# in storage, not as it should appear in the API response. A caller has no
# business knowing that the API has a concept called "db_status". If the field
# is renamed in the database (e.g. to "state" or "lifecycle_status"), the spec
# now fails for the wrong reason — not because the behaviour changed, but because
# the internal name changed. The spec has locked the implementation to a schema
# choice that should be free to evolve independently.
#
# "populated from the order record" is also leaky — it describes how the value
# is obtained (from a record, implying a database read) rather than what the
# caller receives. It presupposes a persistence layer and a specific query shape.
#
# What the spec should say: what field name the caller sees, what value it
# contains, and nothing about where that value comes from internally.
#
# === Scenario 2: "Retrieving status for an order that does not exist" ===
#
# This is a VAGUE GIVEN. The problem is in the Given clause:
#
#   Given an order that has not been placed
#
# "An order that has not been placed" forces the agent to make at least two
# silent assumptions:
#
# ASSUMPTION A: What is the format of the order_id being looked up?
# The scenario passes a value for {order_id} but never specifies whether it
# should be a well-formed UUID, a random string, a known-bad format, or an
# ID that was once valid but has since been deleted. Each of these is a
# distinct situation with potentially different handling:
#   - Never-existed UUID → 404
#   - Malformed ID → 422
#   - Expired/deleted order → 410 Gone vs 404 Not Found
#
# ASSUMPTION B: What does "not been placed" mean in terms of system state?
# Does it mean the order ID was never created? Or that the order was created
# but not yet confirmed? "Not been placed" is ambiguous — placement could
# mean order creation, payment confirmation, or fulfilment dispatch, depending
# on which part of the system you're in.
#
# Both assumptions are plausible. The dangerous one is Assumption A: an agent
# that treats all of these as "return 404" will pass the test, but a client
# that sends a malformed ID expecting a 422 will get a 404 and interpret it
# as "the server doesn't know about this order" rather than "the ID you sent
# is not a valid format." That is a meaningful difference for error handling.

Feature: Order status retrieval (bad specs — for newsletter demonstration)

  Scenario: Retrieving status for a confirmed order
    Given an order has been created and its db_status is "CONFIRMED"
    When the client calls GET /orders/{order_id}/status
    Then the response status code should be 200
    And the response should contain the db_status field set to "CONFIRMED"
    And the order_created_at timestamp is a non-empty string

  Scenario: Retrieving status for an order that does not exist
    Given an order that has not been placed
    When the client calls GET /orders/nonexistent-id/status
    Then the response status code should be 404
