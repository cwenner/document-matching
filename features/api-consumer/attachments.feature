@api @attachments @story-1.4
Feature: Document Matching API - Utilizing Interpreted Data from Attachments
  As an API Consumer
  I want the matching service to automatically unpack and utilize interpreted data from document attachments
  So that structured data within attachments can be leveraged for more accurate matching

  Background:
    Given the document matching service is available

  @attachment @interpreted_json @implemented
  Scenario: Document With Interpreted JSON Attachment
    Given I have a primary document with an "interpreted_data.json" attachment
    And I have candidate documents with similar data but in different formats
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should indicate that the attachment data was used
    And the match should have higher certainty metrics than without attachments

  @attachment @interpreted_xml @implemented
  Scenario: Document With Interpreted XML Attachment
    Given I have a primary document with an "interpreted_xml.json" attachment
    And I have candidate documents with similar data but in different formats
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should indicate that the attachment data was used
    And the match should have higher certainty metrics than without attachments

  @attachment @both_interpreted_files @implemented
  Scenario: Document With Both Interpreted XML and JSON Attachments
    Given I have a primary document with both "interpreted_data.json" and "interpreted_xml.json" attachments
    And I have candidate documents with similar data but in different formats
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should indicate which attachment type was prioritized

  @attachment @malformed_interpreted_data @implemented
  Scenario: Document With Malformed Interpreted Attachment
    Given I have a primary document with a malformed "interpreted_data.json" attachment
    And I have candidate documents with matching identifiers
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a match report
    And the service should proceed with matching using other available data

  @attachment @missing_interpreted_data @implemented
  Scenario: Documents Without Interpreted Attachments
    Given I have a primary document without interpreted attachments
    And I have candidate documents with matching identifiers
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a match report
    And the service should match using only the base document data

  @attachment @multi_document_attachments @implemented
  Scenario: Multiple Documents with Different Attachment Types
    Given I have a primary document with an "interpreted_data.json" attachment
    And I have a candidate document with an "interpreted_xml.json" attachment
    And I have another candidate document without interpreted attachments
    When I send a POST request to "/" with the primary document and all candidate documents
    Then the response status code should be 200
    And the response body should contain match reports
    And each match report should correctly indicate which attachment data was used
    
  @attachment_data @interpreted_data @implemented
  Scenario: Utilize interpreted data from document attachments for matching
    Given I have a primary document "primary_doc_with_attachment.json" that includes an "interpreted_data.json" attachment
    And I have a list of candidate documents "candidates_for_attachment_test.json"
    When I send a POST request to "/" with the primary document "primary_doc_with_attachment.json" and candidates "candidates_for_attachment_test.json"
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should show evidence that attachment data was considered in matching
