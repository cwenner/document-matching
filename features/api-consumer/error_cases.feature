Feature: Document Matching API Error Cases
  As an API consumer
  I want to receive appropriate error responses
  So that I can handle edge cases and invalid requests properly

  Background:
    Given the document matching service is available

  @story-1.1 @error_cases @no_match @implemented
  Scenario: No-Match Scenario
    Given I have a primary invoice document
    And I have a candidate purchase order document that should not match
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain "no-match" in labels
    And the match report should have low certainty metrics

  @story-1.1 @error_cases @empty_candidates @implemented
  Scenario: Empty Candidate List
    Given I have a primary invoice document
    And I have no candidate documents
    When I send a POST request to "/" with the primary document and an empty list of candidate documents
    Then the response status code should be 200
    And the response body should indicate no matches were found
    And the response should comply with the API schema

  @story-1.1 @error_cases @missing_primary @implemented
  Scenario: Missing Primary Document
    Given I have no primary document
    And I have candidate purchase order documents
    When I send a POST request to "/" with a missing primary document and candidate documents
    Then the response status code should be 400
    And the response body should contain a clear error message
    And the error message should indicate the missing primary document

  # NOTE: API does not validate document structure - accepts any dict and attempts processing
  @story-1.1 @error_cases @invalid_format @wip
  Scenario: Invalid Document Format
    Given I have a primary document with invalid format
    And I have valid candidate documents
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 400
    And the response body should contain a clear error message
    And the error message should indicate the format issue

  # NOTE: API does not validate document kind enum - accepts any kind value
  @story-1.1 @error_cases @invalid_kind @wip
  Scenario: Invalid Document Kind
    Given I have a primary document with unsupported kind
    And I have valid candidate documents
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 400
    And the response body should contain a clear error message
    And the error message should indicate the invalid document kind

  @story-1.1 @error_cases @payload_too_large @implemented
  Scenario: Request Payload Too Large
    Given I have a primary document
    And I have too many candidate documents exceeding the limit
    When I send a POST request to "/" with the primary document and excessive candidate documents
    Then the response status code should be 413
    And the response body should contain a clear error message
    And the error message should indicate the payload size issue
