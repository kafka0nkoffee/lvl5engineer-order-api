Feature: Order Creation

  Scenario: Order is successfully created when payment succeeds and all items are in stock
    Given a registered user with id "user-123"
    And the inventory service confirms all items are in stock
    And the payment gateway will accept the charge
    When the user submits an order for SHOE-RED-42 and BELT-BRN-M
    Then the order status is "CONFIRMED"
    And the response includes an order id
    And the payment gateway received exactly one charge request
    And the inventory service received a reservation request

  Scenario: Order is rejected when payment is declined
    Given a registered user with id "user-456"
    And the inventory service confirms all items are in stock
    And the payment gateway will decline the charge
    When the user submits an order for SHOE-RED-42 and BELT-BRN-M
    Then the order status is "PAYMENT_FAILED"
    And the response status code is 402
    And the response includes the decline reason "INSUFFICIENT_FUNDS"
    And the inventory reservation is released
    And no order id is issued

  Scenario: Order is rejected when an item is out of stock
    Given a registered user with id "user-789"
    And the inventory service reports SHOE-RED-42 is out of stock
    When the user submits an order for SHOE-RED-42
    Then the order status is "UNAVAILABLE"
    And the response status code is 409
    And the response identifies SHOE-RED-42 as unavailable
    And the payment gateway is never called

  Scenario: Order surfaces partial unavailability without auto-confirming
    Given a registered user with id "user-321"
    And the inventory service reports SHOE-RED-42 as available but BELT-BRN-M as unavailable
    When the user submits an order for SHOE-RED-42 and BELT-BRN-M
    Then the order status is "PARTIAL_UNAVAILABLE"
    And the response status code is 207
    And SHOE-RED-42 is listed as available
    And BELT-BRN-M is listed as unavailable
    And the payment gateway is never called
    And no order is confirmed without explicit user action

  Scenario: Order handling is graceful when the payment gateway times out
    Given a registered user with id "user-654"
    And the inventory service confirms all items are in stock
    And the payment gateway will not respond within the timeout window
    When the user submits an order for SHOE-RED-42 and BELT-BRN-M
    Then the response is returned within 12 seconds
    And the order status is "PAYMENT_PENDING"
    And the response status code is 202
    And the inventory is held for 15 minutes
    And the user is informed that payment confirmation is in progress
    And the payment gateway is not retried more than 2 times

