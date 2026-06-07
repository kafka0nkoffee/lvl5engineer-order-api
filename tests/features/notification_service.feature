Feature: Notification Service

  Scenario: Notification is queued when a confirmed order is received
    Given the notification service is healthy
    When the order service sends a confirmed order notification for order "order-abc-123" with total 134.97 for user "user-123"
    Then the notification service returns status 200
    And the response body contains a notification_id in UUID format
    And the response body contains status "QUEUED"

  Scenario: Order confirmation is unaffected when notification service returns 503
    Given a registered user with id "user-123"
    And the inventory service confirms all items are in stock
    And the payment gateway will accept the charge
    And the notification service will respond with 503 Service Unavailable
    When the user submits an order for SHOE-RED-42 and BELT-BRN-M
    Then the order status is "CONFIRMED"
    And the notification endpoint receives at most one request
