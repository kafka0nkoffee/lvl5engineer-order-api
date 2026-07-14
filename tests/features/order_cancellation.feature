Feature: Order Cancellation

  Scenario: Order is successfully cancelled when it is in CONFIRMED state
    Given a CONFIRMED order with id "order-abc-123" exists
    And the inventory service will accept the reservation release
    When the user cancels order "order-abc-123"
    Then the order status is "CANCELLED"
    And the response includes the order id "order-abc-123"
    And the inventory service receives exactly 1 reservation release request
    And the notification service receives exactly 1 cancellation notification

  Scenario: Cancelling an already-cancelled order returns 200 with CANCELLED status
    Given a CANCELLED order with id "order-abc-456" exists
    When the user cancels order "order-abc-456"
    Then the order status is "CANCELLED"
    And the response includes the order id "order-abc-456"
    And the inventory service receives no reservation release requests
    And the notification service receives no cancellation notifications

  Scenario: Cancellation of a non-existent order returns 404
    When the user cancels order "order-does-not-exist"
    Then the response status code is 404
    And the response body contains an error field with value "Order not found"
    And the inventory service receives no reservation release requests

  Scenario: Cancellation of a PAYMENT_PENDING order is rejected with 409
    Given a PAYMENT_PENDING order with id "order-abc-789" exists
    When the user cancels order "order-abc-789"
    Then the response status code is 409
    And the response body contains an error field with value "Order cannot be cancelled in PAYMENT_PENDING state"
    And the inventory service receives no reservation release requests

  Scenario: Cancellation of a PAYMENT_FAILED order is rejected with 409
    Given a PAYMENT_FAILED order with id "order-abc-012" exists
    When the user cancels order "order-abc-012"
    Then the response status code is 409
    And the response body contains an error field with value "Order cannot be cancelled in PAYMENT_FAILED state"
    And the inventory service receives no reservation release requests
