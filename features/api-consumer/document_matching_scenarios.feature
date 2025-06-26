@api @core_matching @matching_scenarios @story-1.1
Feature: Document Matching API - Specific Matching Scenarios
  As an API Consumer
  I want the service to handle specific document matching scenarios correctly
  So that document relationships are accurately identified across various conditions.

  Background:
    Given the document matching service is available

  @empty_candidates
  Scenario: Empty candidate list
    Given I have a primary document defined as "primary_doc_no_candidates.json"
    And no candidate documents are provided
    When I send a POST request to "/" with the primary document and an empty list of candidate documents
    Then the response status code should be 200
    And the response body should indicate no matches were found

  @supplier_mismatch
  Scenario: Supplier ID mismatch
    Given I have a primary document defined as "primary_doc_diff_supplier.json"
    And I have a list of candidate documents defined as "candidates_diff_supplier.json"
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should indicate no matches were found

  @po_match
  Scenario: Match on purchase order number
    Given I have a primary document defined as "primary_doc_shared_po.json"
    And I have a list of candidate documents defined as "candidates_shared_po.json"
    When I send a POST request to "/" with the primary document and candidate documents
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain exactly one match between the primary document and a candidate document

#  @no_common_fields
#  Scenario: Documents with no common identifiers
#    Given I have a primary document defined as "primary_doc_nothing_alike.json"
#    And I have a list of candidate documents defined as "candidates_nothing_alike.json"
#    When I send a POST request to "/" with the primary document and candidate documents
#    Then the response status code should be 200
#    And the response body should indicate no matches were found

#  @item_level_match
#  Scenario: Match on line items despite differing PO numbers
#    Given I have a primary document defined as "primary_doc_items.json"
#    And I have a list of candidate documents defined as "candidates_items_same.json"
#    When I send a POST request to "/" with the primary document and candidate documents
#    Then the response status code should be 200
#    And the response body should contain a match report
#    And the match report should contain exactly one match based on item overlap
