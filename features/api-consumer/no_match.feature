@api @no_match @story-1.2
Feature: Document Matching API - Clear No-Match Reporting
  As an API Consumer
  I want to receive a clear and distinct no-match report when no suitable matches are found
  So that I know the document could not be paired and can proceed with alternative actions

  Background:
    Given the document matching service is available

  @empty_candidates @implemented
  Scenario: Empty candidate list
    Given I have a primary document defined as "primary_doc_no_candidates.json"
    And no candidate documents are provided
    When I send a POST request to "/" with the primary document and an empty list of candidate documents
    Then the response status code should be 200
    And the response body should indicate no matches were found
    
  @supplier_mismatch @implemented
  Scenario: Supplier ID mismatch
    Given I have a primary document defined as "primary_doc_diff_supplier.json"
    And I have a list of candidate documents defined as "candidates_diff_supplier.json"
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should indicate no matches were found

  @no_match_validation
  Scenario: Validate No-Match Report Schema
    Given I have a primary document with unique identifiers
    And I have candidate documents with different identifiers
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a structured no-match report
    And the no-match report should adhere to the V3 schema
    And the no-match report should clearly indicate no matches were found

  @no_match_different_types
  Scenario: No Match Between Different Document Types
    Given I have a primary invoice document with unique identifiers
    And I have candidate purchase order documents with different identifiers
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a structured no-match report
    And the no-match report should include document type information
    And the no-match report should explain why the documents did not match

  @no_match_structured_array
  Scenario: No-Match Report as Empty Array
    Given I have a primary document with unique supplier ID
    And I have candidate documents with different supplier IDs
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should be a correctly structured empty array
    And the empty array should conform to the V3 report specification

  @no_match_with_reason
  Scenario: No-Match Report With Detailed Reasons
    Given I have a primary document with specific identifiers
    And I have candidate documents with non-matching identifiers
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a structured no-match report
    And the no-match report should include specific reasons why matches failed
    And the no-match report should include "no-match" in labels
