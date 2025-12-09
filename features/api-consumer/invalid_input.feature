@api @invalid_input @story-1.3
Feature: Document Matching API - Invalid Input Handling
  As an API Consumer
  I want to receive appropriate error responses when I submit invalid or malformed requests
  So that I can understand and correct my requests

  Background:
    Given the document matching service is available

  @error_cases @missing_primary @implemented
  Scenario: Missing Primary Document
    Given I have no primary document
    And I have a list of valid candidate documents
    When I send a POST request to "/" with a missing primary document and candidate documents
    Then the response status code should be 400
    And the response body should contain a clear error message
    And the error message should indicate the missing primary document
    And the error message should be machine-readable

  # NOTE: API does not validate document structure - accepts any dict and attempts processing
  # BLOCKED BY: #74 (Define input validation strictness and error responses)
  @error_cases @invalid_format @wip
  Scenario: Invalid Document Format
    Given I have a primary document with invalid format
    And I have a list of valid candidate documents
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 400
    And the response body should contain a clear error message
    And the error message should indicate the format issue
    And the error message should be machine-readable

  @error_cases @malformed_json @implemented
  Scenario: Malformed JSON Payload
    Given I have a malformed JSON payload
    When I send a POST request to "/" with the malformed payload
    Then the response status code should be 400
    And the response body should contain a clear error message
    And the error message should indicate the JSON parsing issue
    And the error message should be machine-readable

  @error_cases @candidates_not_array @implemented
  Scenario: Candidate Documents Not an Array
    Given I have a valid primary document
    And I have candidate documents incorrectly formatted as a single object
    When I send a POST request to "/" with the primary document and incorrectly formatted candidates
    Then the response status code should be 400
    And the response body should contain a clear error message
    And the error message should indicate that candidates must be an array
    And the error message should be machine-readable

  @error_cases @unsupported_content_type @implemented
  Scenario: Unsupported Content Type
    Given I have documents in an unsupported format
    When I send a POST request to "/" with an unsupported Content-Type header
    Then the response status code should be 415
    And the response body should contain a clear error message
    And the error message should indicate the unsupported content type
    And the error message should be machine-readable

  # NOTE: API does not validate required document fields - accepts minimal dict
  # BLOCKED BY: #74 (Define input validation strictness and error responses)
  @error_cases @missing_required_fields @wip
  Scenario: Missing Required Document Fields
    Given I have a primary document missing required fields
    And I have a list of valid candidate documents
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 400
    And the response body should contain a clear error message
    And the error message should specify which required fields are missing
    And the error message should be machine-readable

  # NOTE: API does not validate field values - accepts any values
  # BLOCKED BY: #74 (Define input validation strictness and error responses)
  @error_cases @invalid_field_values @wip
  Scenario: Invalid Field Values
    Given I have a primary document with invalid field values
    And I have a list of valid candidate documents
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 400
    And the response body should contain a clear error message
    And the error message should specify which fields have invalid values
    And the error message should be machine-readable
    
  @error_handling @invalid_payload @implemented
  Scenario: Handle invalid request payload gracefully
    Given I have an invalid request payload defined as "payload_invalid_structure.json"
    When I send a POST request to "/" with the invalid payload
    Then the response status code should be 400
    And the response body should contain a clear error message
