Feature: Core Document Matching API
  As an API consumer
  I want to match documents against each other
  So that I can determine relationships between business documents

  Background:
    Given the document matching service is available

  @performance @response_time @implemented
  Scenario: Service maintains acceptable response times
    Given I have a primary document defined as "primary_doc_standard.json"
    And I have a list of 20 candidate documents defined as "candidates_multiple.json"
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the service should respond within 2 seconds

  @po_match @implemented
  Scenario: Document with matching PO number
    Given I have a primary document defined as "primary_doc_shared_po.json"
    And I have a list of candidate documents defined as "candidates_shared_po.json"
    When I send a POST request to "/" with the primary document and candidates
    Then the response status code should be 200
    And the match report should include document IDs from the candidate documents

  @story-1.1 @core @invoice_po_match @implemented
  Scenario: Basic Invoice-PO Match
    Given I have a primary invoice document
    And I have a candidate purchase order document
    When I send a POST request to "/" with the primary document and candidates
    Then the response status code should be 200
    And the response body should contain a match report in v3 schema
    And the match report should contain "matched" in labels
    And the match report should include certainty metrics
    And the match report should reference both document IDs
    And the match report should complete within 60 seconds

  # NOTE: PO-primary matching not supported - ML model trained for invoice-primary only
  # BLOCKED BY: #14 (Enable all matching directions)
  @story-1.1 @core @po_dr_match @wip
  Scenario: Basic PO-Delivery Receipt Match
    Given I have a primary purchase order document
    And I have a candidate delivery receipt document
    When I send a POST request to "/" with the primary document and candidates
    Then the response status code should be 200
    And the response body should contain a match report in v3 schema
    And the match report should contain "matched" in labels
    And the match report should include certainty metrics
    And the match report should reference both document IDs
    And the match report should complete within 60 seconds

  # Three-way matching returns separate reports for Invoice↔PO and PO↔Delivery
  @story-1.1 @core @three_way_match @implemented
  Scenario: Three-Way Document Matching
    Given I have an invoice document
    And I have a candidate purchase order document
    And I have a candidate delivery receipt document
    When I send a POST request to "/" with the primary document and candidates
    Then the response status code should be 200
    And the response body should contain two match reports
    And one match report should be between invoice and purchase order
    And one match report should be between purchase order and delivery receipt
    And both match reports should follow the v3 schema
    And both match reports should complete within 60 seconds

  @story-1.1 @core @multiple_candidates @implemented
  Scenario: Match with Multiple Candidate Documents
    Given I have a primary invoice document
    And I have 5 candidate purchase order documents
    When I send a POST request to "/" with the primary document and candidates
    Then the response status code should be 200
    And the response body should contain match reports for each candidate document
    And each match report should follow the v3 schema
    And the entire response should complete within 60 seconds

  @story-1.1 @performance @max_candidates @implemented
  Scenario: Performance Requirements with Maximum Candidates
    Given I have a primary invoice document
    And I have 10 candidate purchase order documents
    When I send a POST request to "/" with the primary document and candidates
    Then the response status code should be 200
    And the response body should contain match reports for each candidate document
    And the entire response should complete within 60 seconds
