Feature: Core Document Matching API
  As an API consumer
  I want to match documents against each other
  So that I can determine relationships between business documents

  Background:
    Given the document matching service is available

  @story-1.1 @core @invoice_po_match
  Scenario: Basic Invoice-PO Match
    Given I have a primary invoice document
    And I have a candidate purchase order document
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report in v3 schema
    And the match report should contain "matched" in labels
    And the match report should include certainty metrics
    And the match report should reference both document IDs
    And the match report should complete within 60 seconds

  @story-1.1 @core @po_dr_match
  Scenario: Basic PO-Delivery Receipt Match
    Given I have a primary purchase order document
    And I have a candidate delivery receipt document
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report in v3 schema
    And the match report should contain "matched" in labels
    And the match report should include certainty metrics
    And the match report should reference both document IDs
    And the match report should complete within 60 seconds

  @story-1.1 @core @three_way_match
  Scenario: Three-Way Document Matching
    Given I have an invoice document
    And I have a purchase order document
    And I have a delivery receipt document
    When I send a POST request to "/" with all three documents
    Then the response status code should be 200
    And the response body should contain two match reports
    And one match report should be between invoice and purchase order
    And one match report should be between purchase order and delivery receipt
    And both match reports should follow the v3 schema
    And both match reports should complete within 60 seconds

  @story-1.1 @core @multiple_candidates
  Scenario: Match with Multiple Candidate Documents
    Given I have a primary invoice document
    And I have 5 candidate purchase order documents
    When I send a POST request to "/" with the primary document and all candidate documents
    Then the response status code should be 200
    And the response body should contain match reports for each candidate document
    And each match report should follow the v3 schema
    And the entire response should complete within 60 seconds

  @story-1.1 @performance @max_candidates
  Scenario: Performance Requirements with Maximum Candidates
    Given I have a primary invoice document
    And I have 10 candidate purchase order documents
    When I send a POST request to "/" with the primary document and all candidate documents
    Then the response status code should be 200
    And the response body should contain match reports for each candidate document
    And the entire response should complete within 60 seconds
