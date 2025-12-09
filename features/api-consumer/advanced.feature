Feature: Advanced Document Matching Features
  As an API consumer
  I want to access advanced document matching capabilities
  So that I can obtain detailed insights about document relationships

  Background:
    Given the document matching service is available

  @story-1.1 @advanced @future_match @implemented
  Scenario: Future Match Certainty
    Given I have a primary invoice document
    And I have a candidate purchase order document
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should include "invoice-has-future-match-certainty" metric
    And the match report should include "purchase-order-has-future-match-certainty" metric
    And the match report should include "delivery-receipt-has-future-match-certainty" metric

  @story-1.1 @advanced @attachment_data @implemented
  Scenario: Documents with Attachment Data
    Given I have a primary invoice document with attachment data
    And I have a candidate purchase order document with attachment data
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should include fields that reference attachment data

  @story-1.1 @advanced @xml_data @implemented
  Scenario: Documents with Original XML Data
    Given I have a primary invoice document with original XML data
    And I have a candidate purchase order document
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should include evidence that XML data was used in matching
    And the match report should contain matching attributes derived from XML

  # NOTE: ML model does not guarantee same-supplier matches have highest certainty
  # The model considers multiple features and may select different candidates
  # BLOCKED BY: #58 (Investigate supplier ID priority in ML matching model)
  @story-1.1 @advanced @supplier_matching @wip
  Scenario: Matching Documents from Same Supplier
    Given I have a primary invoice document from supplier "ABC Corp"
    And I have multiple candidate purchase orders from different suppliers
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain match reports
    And the match report for the same supplier should have higher certainty

  @story-1.1 @advanced @multiple_deviations @implemented
  Scenario: Match Report with Multiple Deviation Types
    Given I have a primary invoice document
    And I have a candidate purchase order document with multiple deviations
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain multiple deviation types
    And the overall deviation severity should reflect the most severe deviation
