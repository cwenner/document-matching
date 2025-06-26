Feature: Document Matching with Deviations
  As an API consumer
  I want to match documents with deviations between them
  So that I can identify and handle discrepancies in business documents

  Background:
    Given the document matching service is available

  @story-1.1 @deviations @amount_deviation
  Scenario: Match with Amount Deviations
    Given I have a primary invoice document with amount 1500.00
    And I have a candidate purchase order with amount 1450.00
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain "matched" in labels
    And the match report should include deviation with code "amounts-differ"
    And the deviation severity should reflect the percentage difference

  @story-1.1 @deviations @quantity_deviation
  Scenario: Match with Quantity Deviations
    Given I have a primary invoice document with item quantity 10
    And I have a candidate purchase order with item quantity 8
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "quantities-differ"
    And the deviation severity should reflect the percentage difference

  @story-1.1 @deviations @partial_delivery
  Scenario: Match with Partial Delivery
    Given I have a primary purchase order with item quantity 20
    And I have a candidate delivery receipt with item quantity 12
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "partial-delivery"
    And the deviation severity should be "info"

  @story-1.1 @deviations @currency_mismatch
  Scenario: Match with Different Currencies
    Given I have a primary invoice document with currency "USD"
    And I have a candidate purchase order with currency "EUR"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "currencies-differ"
    And the deviation severity should be "high"

  @story-1.1 @deviations @description_mismatch
  Scenario: Match with Different Item Descriptions
    Given I have a primary invoice with item description "Office Supplies"
    And I have a candidate purchase order with item description "Office Materials"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "descriptions-differ"
    And the deviation severity should reflect the textual similarity
