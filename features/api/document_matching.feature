@api @core_matching @story-1.1
Feature: Document Matching API - Core Functionality
  As an API Consumer
  I want to interact with the document matching service
  So that I can identify relationships between my business documents.

  Background:
    Given the document matching service is available

  @error_handling @invalid_payload
  Scenario: Handle invalid request payload gracefully
    Given I have an invalid request payload defined as "payload_invalid_structure.json"
    When I send a POST request to "/" with the invalid payload
    Then the response status code should be 400
    And the response body should contain a clear error message
# 
  @attachment_data @interpreted_data
  Scenario: Utilize interpreted data from document attachments for matching
    Given I have a primary document "primary_doc_with_attachment.json" that includes an "interpreted_data.json" attachment
    And I have a list of candidate documents "candidates_for_attachment_test.json"
    When I send a POST request to "/" with the primary document "primary_doc_with_attachment.json" and candidates "candidates_for_attachment_test.json"
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should show evidence that attachment data was considered in matching
    
  @performance @response_time
  Scenario: Service maintains acceptable response times
    Given I have a primary document defined as "primary_doc_standard.json"
    And I have a list of 20 candidate documents defined as "candidates_multiple.json"
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the service should respond within 2 seconds
