@api @deviations @story-1.5
Feature: Document Matching - Detailed Deviation Information
  As an API Consumer
  I want to receive detailed deviation information whenever matches are found with discrepancies between documents
  So that I can quickly identify and assess issues that require attention

  Background:
    Given the document matching service is available

  @deviations @amount_deviation @implemented
  Scenario: Match with Amount Deviations
    Given I have a primary invoice document with amount 1500.00
    And I have a candidate purchase order with amount 1450.00
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain "match" in labels
    And the match report should include deviation with code "AMOUNTS_DIFFER"
    And the deviation severity should reflect the percentage difference

  @deviations @quantity_deviation @implemented
  Scenario: Match with Quantity Deviations
    Given I have a primary invoice document with item quantity 10
    And I have a candidate purchase order with item quantity 8
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "QUANTITIES_DIFFER"
    And the deviation severity should reflect the percentage difference

  @deviations @partial_delivery
  Scenario: Match with Partial Delivery
    Given I have a primary purchase order with item quantity 20
    And I have a candidate delivery receipt with item quantity 12
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "PARTIAL_DELIVERY"
    And the deviation severity should be "info"

  @deviations @currency_mismatch
  Scenario: Match with Different Currencies
    Given I have a primary invoice document with currency "USD"
    And I have a candidate purchase order with currency "EUR"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "CURRENCIES_DIFFER"
    And the deviation severity should be "high"

  @deviations @description_mismatch
  Scenario: Match with Different Item Descriptions
    Given I have a primary invoice with item description "Office Supplies"
    And I have a candidate purchase order with item description "Office Materials"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "DESCRIPTIONS_DIFFER"
    And the deviation severity should reflect the textual similarity

  @deviations @comprehensive
  Scenario: Comprehensive Deviation Reporting
    Given I have a primary invoice document with multiple deviations from the standard
    And I have a candidate purchase order with corresponding deviations
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should include a "deviations" section at document level
    And each item pair in the match report should include a "deviations" section where applicable
    And all deviations should include standardized deviation codes
    And all deviations should include a severity level
    And all deviations should include human-readable messages explaining the discrepancy
    And all deviations should include field references and actual values that differ
    And the match report should include a "deviation-severity" metric showing the highest deviation severity

  @deviations @field_format
  Scenario: Deviation Field Names and Values Format
    Given I have a primary invoice document with amount 1800.00
    And I have a candidate purchase order with amount 1750.50
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "AMOUNTS_DIFFER"
    And the deviation should contain a "field_names" array with field path strings
    And the deviation should contain a "values" array with string representations of actual values
    And the "field_names" array length should equal the number of documents in the match
    And the "values" array length should equal the number of documents in the match
