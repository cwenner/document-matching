Feature: Document Matching at Item Level
  As an API consumer
  I want to match documents at the item level
  So that I can identify paired and unpaired items across documents

  Background:
    Given the document matching service is available

  @story-1.1 @item_level @item_pairing @implemented
  Scenario: Item Pairing Success
    Given I have a primary invoice with 3 items
    And I have a candidate purchase order with the same 3 items
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain 3 itempairs with match_type "matched"
    And each itempair should have item_indices for both documents
    And each itempair should have item_unchanged_certainty scores
    And each itempair should have match_type property as a string with value "matched"

  @story-1.1 @item_level @unmatched_primary @implemented
  Scenario: Unmatched Items in Primary Document
    Given I have a primary invoice with 5 items
    And I have a candidate purchase order with 3 matching items
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain 5 itempairs
    And 3 itempairs should have match_type "matched"
    And 2 itempairs should have match_type "unmatched"
    And the unmatched itempairs should have item_indices [n, null]
    And the matched itempairs should have match_type property as a string with value "matched"
    And the unmatched itempairs should have match_type property as a string with value "unmatched"
    And the unmatched itempairs should have deviations with code "item-unmatched"

  @story-1.1 @item_level @unmatched_candidate @implemented
  Scenario: Unmatched Items in Candidate Document
    Given I have a primary invoice with 3 items
    And I have a candidate purchase order with 5 items
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain 5 itempairs
    And 3 itempairs should have match_type "matched"
    And 2 itempairs should have match_type "unmatched"
    And the unmatched itempairs should have item_indices [null, n]
    And the unmatched itempairs should have deviations with code "item-unmatched"

  @story-1.1 @item_level @item_reordering @implemented
  Scenario: Different Item Order in Documents
    Given I have a primary invoice with items in order A, B, C
    And I have a candidate purchase order with items in order C, A, B
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain 3 itempairs with match_type "matched"
    And the item_indices should correctly map the reordered items

  @story-1.1 @item_level @article_numbers_differ @implemented
  Scenario: Matching Items with Different Article Numbers
    Given I have a primary invoice with item article number "ABC123"
    And I have a candidate purchase order with item article number "XYZ123"
    But the item descriptions are similar
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain an itempair for these items
    And the itempair should have deviation with code "article-numbers-differ"
