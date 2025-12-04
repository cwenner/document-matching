@api @deviations @story-1.5
Feature: Document Matching - Detailed Deviation Information
  As an API Consumer
  I want to receive detailed deviation information whenever matches are found with discrepancies between documents
  So that I can quickly identify and assess issues that require attention

  Background:
    Given the document matching service is available

  # ============================================================================
  # AMOUNTS_DIFFER - Header Level (#24)
  # Thresholds: no-severity (abs<=0.01 AND rel<=0.1%), low (abs<=1 AND rel<=1%),
  #             medium (abs<=50 AND rel<=5%), high (otherwise)
  # ============================================================================

  @deviations @amount_deviation @implemented
  Scenario: Match with Amount Deviations
    Given I have a primary invoice document with amount 1500.00
    And I have a candidate purchase order with amount 1450.00
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain "matched" in labels
    And the match report should include deviation with code "AMOUNTS_DIFFER"
    And the deviation severity should reflect the percentage difference

  @deviations @amount_deviation @header_level @no_severity @implemented
  Scenario: Header amount deviation - no-severity for tiny differences
    Given I have a primary invoice document with amount 1000.00
    And I have a candidate purchase order with amount 1000.005
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the AMOUNTS_DIFFER deviation severity should be "no-severity"

  @deviations @amount_deviation @header_level @low @implemented
  Scenario: Header amount deviation - low severity for small differences
    Given I have a primary invoice document with amount 100.00
    And I have a candidate purchase order with amount 100.50
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the AMOUNTS_DIFFER deviation severity should be "low"

  @deviations @amount_deviation @header_level @medium @implemented
  Scenario: Header amount deviation - medium severity for moderate differences
    Given I have a primary invoice document with amount 1000.00
    And I have a candidate purchase order with amount 1025.00
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the AMOUNTS_DIFFER deviation severity should be "medium"

  @deviations @amount_deviation @header_level @high @implemented
  Scenario: Header amount deviation - high severity for large differences
    Given I have a primary invoice document with amount 1000.00
    And I have a candidate purchase order with amount 1200.00
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the AMOUNTS_DIFFER deviation severity should be "high"

  # ============================================================================
  # QUANTITIES_DIFFER (#26) - Only when qty > PO qty
  # Thresholds: low (abs<=1 AND rel<=10%), medium (abs<=10 OR rel<=50%), high (otherwise)
  # ============================================================================

  @deviations @quantity_deviation @implemented
  Scenario: Match with Quantity Deviations
    Given I have a primary invoice document with item quantity 10
    And I have a candidate purchase order with item quantity 8
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "QUANTITIES_DIFFER"
    And the deviation severity should reflect the percentage difference

  @deviations @quantity_deviation @low @implemented
  Scenario: Quantity deviation - low severity for small excess
    Given I have a primary invoice document with item quantity 11
    And I have a candidate purchase order with item quantity 10
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the QUANTITIES_DIFFER item deviation severity should be "low"

  @deviations @quantity_deviation @high @implemented
  Scenario: Quantity deviation - high severity for large excess
    Given I have a primary invoice document with item quantity 200
    And I have a candidate purchase order with item quantity 100
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the QUANTITIES_DIFFER item deviation severity should be "high"

  # ============================================================================
  # PARTIAL_DELIVERY (#21) - When qty < PO qty, always INFO
  # ============================================================================

  @deviations @partial_delivery @implemented
  Scenario: Match with Partial Delivery
    Given I have a primary invoice document with item quantity 12
    And I have a candidate purchase order with item quantity 20
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain item deviation with code "PARTIAL_DELIVERY"
    And the PARTIAL_DELIVERY item deviation severity should be "info"
    And the match report should contain "partial-delivery" in labels

  # ============================================================================
  # PRICES_PER_UNIT_DIFFER (#25)
  # Thresholds: no-severity (abs<=0.005 OR rel<=0.5%), low (rel<=5%),
  #             medium (rel<=20%), high (otherwise)
  # ============================================================================

  @deviations @unit_price @implemented
  Scenario: Unit price deviation - low severity for small price difference
    Given I have a primary invoice with item unit price 100.00
    And I have a candidate purchase order with item unit price 102.00
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the PRICES_PER_UNIT_DIFFER item deviation severity should be "low"

  @deviations @unit_price @high @implemented
  Scenario: Unit price deviation - high severity for large price difference
    Given I have a primary invoice with item unit price 100.00
    And I have a candidate purchase order with item unit price 130.00
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the PRICES_PER_UNIT_DIFFER item deviation severity should be "high"

  # ============================================================================
  # ARTICLE_NUMBERS_DIFFER (#22)
  # Default MEDIUM, downgrade to LOW if description similarity >= 0.9
  # ============================================================================

  @deviations @article_number @implemented
  Scenario: Article number deviation with similar descriptions
    Given I have a primary invoice with item article number "ABC-123" and description "Widget Type A"
    And I have a candidate purchase order with item article number "ABC-124" and description "Widget Type A"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the ARTICLE_NUMBERS_DIFFER item deviation severity should be "low" or "medium"

  # ============================================================================
  # ITEM_UNMATCHED (#20)
  # Severity based on line amount: no-severity (<=0.01), low (<=1),
  #                                medium (<=10), high (>10)
  # ============================================================================

  @deviations @item_unmatched @implemented
  Scenario: Unmatched item with high value
    Given I have a primary invoice with two items where one has no match
    And I have a candidate purchase order with one item
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain item with match_type "unmatched"
    And the ITEM_UNMATCHED deviation severity should reflect the line amount

  # ============================================================================
  # Other deviation scenarios
  # ============================================================================

  @deviations @currency_mismatch
  Scenario: Match with Different Currencies
    Given I have a primary invoice document with currency "USD"
    And I have a candidate purchase order with currency "EUR"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "CURRENCIES_DIFFER"
    And the deviation severity should be "high"

  # ============================================================================
  # DESCRIPTIONS_DIFFER (#27) - Similarity-based severity
  # Thresholds: no-severity (sim>=0.98 OR casing/whitespace only), info (sim>=0.90),
  #             low (sim>=0.75), medium (sim>=0.50), high (sim<0.50 OR one empty)
  # ============================================================================

  @deviations @description_mismatch
  Scenario: Match with Different Item Descriptions
    Given I have a primary invoice with item and article number "OFF-001" and description "Office Supplies"
    And I have a candidate purchase order with item and article number "OFF-001" and description "Office Materials"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain item deviation with code "DESCRIPTIONS_DIFFER"
    And the deviation severity should reflect the textual similarity

  @deviations @description @no_severity @implemented
  Scenario: Description deviation - no-severity for nearly identical descriptions
    Given I have a primary invoice with item and article number "BOLT-10" and description "10mm galvanized bolt"
    And I have a candidate purchase order with item and article number "BOLT-10" and description "10mm galvanised bolt"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the DESCRIPTIONS_DIFFER item deviation severity should be "no-severity"

  @deviations @description @no_severity @casing @implemented
  Scenario: Description deviation - no-severity for casing differences only
    Given I have a primary invoice with item and article number "WIDGET-A" and description "Widget Type A"
    And I have a candidate purchase order with item and article number "WIDGET-A" and description "widget type a"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And there should be no DESCRIPTIONS_DIFFER deviation

  @deviations @description @no_severity @whitespace @implemented
  Scenario: Description deviation - no-severity for whitespace differences only
    Given I have a primary invoice with item and article number "ABC-123" and description "ABC 123"
    And I have a candidate purchase order with item and article number "ABC-123" and description "ABC  123"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And there should be no DESCRIPTIONS_DIFFER deviation

  @deviations @description @info @implemented
  Scenario: Description deviation - info severity for reordered terms
    Given I have a primary invoice with item and article number "SCREW-M8-10" and description "M8 hex screw 10mm"
    And I have a candidate purchase order with item and article number "SCREW-M8-10" and description "Hex screw M8x10"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the DESCRIPTIONS_DIFFER item deviation severity should be "info"

  @deviations @description @low @implemented
  Scenario: Description deviation - low severity for wording differences
    Given I have a primary invoice with item and article number "BOLT-M10" and description "Stainless steel bolt M10"
    And I have a candidate purchase order with item and article number "BOLT-M10" and description "Steel bolt M10 grade 8"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the DESCRIPTIONS_DIFFER item deviation severity should be "low"

  @deviations @description @medium @implemented
  Scenario: Description deviation - medium severity for overlapping topic
    Given I have a primary invoice with item and article number "FASTENER-001" and description "Steel fastener set industrial grade"
    And I have a candidate purchase order with item and article number "FASTENER-001" and description "Metal fastener hardware kit"
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the DESCRIPTIONS_DIFFER item deviation severity should be "medium"

  # Note: The empty description case (one empty, other non-empty → HIGH severity)
  # cannot be tested end-to-end because items won't pair when one description is empty.
  # This edge case is tested at the unit level in check_description_deviation().

  @deviations @description @both_empty @implemented
  Scenario: Description deviation - no deviation when both descriptions are empty
    Given I have a primary invoice with item and article number "EMPTY-001" and description ""
    And I have a candidate purchase order with item and article number "EMPTY-001" and description ""
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And there should be no DESCRIPTIONS_DIFFER deviation

  @deviations @comprehensive
  Scenario: Comprehensive Deviation Reporting
    Given I have a primary invoice document with multiple deviations from the standard
    And I have a candidate purchase order with corresponding deviations
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should include a "deviations" section at document level
    And each item pair in the match report should include a "deviations" section where applicable
    And all deviations should include standardized deviation codes
    And all deviations should include a severity level
    And all deviations should include human-readable messages explaining the discrepancy
    And all deviations should include field references and actual values that differ
    And the match report should include a "deviation-severity" metric showing the highest deviation severity

  @deviations @field_format
  Scenario: Deviation Field Names and Values Format
    Given I have a primary invoice document with amount 1800.00
    And I have a candidate purchase order with amount 1750.50
    When I send a POST request to "/" with the primary document and candidate document
    Then the response status code should be 200
    And the response body should contain a match report
    And the match report should contain deviation with code "AMOUNTS_DIFFER"
    And the deviation should contain a "field_names" array with field path strings
    And the deviation should contain a "values" array with string representations of actual values
    And the "field_names" array length should equal the number of documents in the match
    And the "values" array length should equal the number of documents in the match
