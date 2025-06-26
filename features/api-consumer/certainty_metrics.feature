@api @certainty_metrics @story-1.6
Feature: Document Matching - Match Certainty Metrics
  As an API Consumer
  I want to receive confidence metrics for each match and prediction about future matches
  So that I can make informed decisions about which matches to trust and handle appropriately

  Background:
    Given the document matching service is available

  @metrics @certainty_value
  Scenario: Match Report Includes Certainty Metric
    Given I have a primary invoice document
    And I have a candidate purchase order document
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should include a "metrics" section
    And the metrics section should contain a "certainty" value between 0 and 1
    And the certainty value should reflect the confidence level of the match

  @metrics @future_match_prediction
  Scenario: Future Match Prediction for Invoices
    Given I have a primary invoice document
    And I have a list of candidate documents
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should include an "invoice-has-future-match-certainty" metric
    And the future match certainty should be a decimal value between 0 and 1

  @metrics @future_match_prediction_po
  Scenario: Future Match Prediction for Purchase Orders
    Given I have a primary purchase order document
    And I have a list of candidate documents
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should include a "po-has-future-match-certainty" metric
    And the future match certainty should be a decimal value between 0 and 1

  @metrics @item_level_certainty
  Scenario: Item-Level Match Certainty
    Given I have a primary document with line items
    And I have a candidate document with matching line items
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report with line item matches
    And each item pair should include an "item_unchanged_certainty" value
    And all item certainty values should be between 0 and 1

  @metrics @varying_certainty
  Scenario: Match with Varying Certainty Levels
    Given I have a primary document with some ambiguous attributes
    And I have multiple candidate documents with different similarity levels
    When I send a POST request to "/" with the primary document and all candidate documents
    Then the response status code should be 200
    And the response body should contain multiple match reports
    And each match report should have a different certainty value
    And the certainty values should correlate with the similarity levels

  @metrics @comprehensive
  Scenario: Comprehensive Certainty Metrics
    Given I have a complex primary document with items and attachments
    And I have candidate documents with varying levels of similarity
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain match reports
    And all match reports should include a complete "metrics" section
    And the metrics should include overall match certainty
    And the metrics should include future match predictions where applicable
    And all item pairings should include item-level certainty values
    And all certainty values should be expressed as decimals between 0 and 1
