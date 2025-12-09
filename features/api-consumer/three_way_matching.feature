Feature: Three-Way Document Matching via Shared PO Line Items
  As an API consumer
  I want to match invoices and delivery receipts based on shared PO line items
  So that I can correctly group documents that belong to the same business transaction

  Background:
    Given the document matching service is available

  @story-121 @three_way_match @line_items @implemented
  Scenario: Invoice and Delivery Receipt Share Same PO Line Items
    Given I have a purchase order "PO-001" with 3 line items
    And I have an invoice "INV-001" covering PO line items 1 and 2
    And I have a delivery receipt "DR-001" covering PO line items 1 and 2
    When I check if invoice and delivery should merge into three-way match
    Then the result should be "merge"
    And the shared PO line items should be [1, 2]

  @story-121 @three_way_match @line_items @implemented
  Scenario: Invoice and Delivery Receipt Cover Different PO Line Items
    Given I have a purchase order "PO-001" with 3 line items
    And I have an invoice "INV-001" covering PO line items 1 and 2
    And I have a delivery receipt "DR-002" covering PO line item 3
    When I check if invoice and delivery should merge into three-way match
    Then the result should be "no_merge"
    And the shared PO line items should be []

  @story-121 @three_way_match @line_items @implemented
  Scenario: Partial Overlap of PO Line Items
    Given I have a purchase order "PO-001" with 3 line items
    And I have an invoice "INV-001" covering PO line items 1, 2, and 3
    And I have a delivery receipt "DR-001" covering PO line items 2 and 3
    When I check if invoice and delivery should merge into three-way match
    Then the result should be "merge"
    And the shared PO line items should be [2, 3]

  @story-121 @three_way_match @grouping @implemented
  Scenario: Multiple Invoices and Deliveries Grouped by Shared Lines
    Given I have a purchase order "PO-001" with 3 line items
    And I have an invoice "INV-001" covering PO line items 1 and 2
    And I have an invoice "INV-002" covering PO line item 3
    And I have a delivery receipt "DR-001" covering PO line items 1 and 2
    And I have a delivery receipt "DR-002" covering PO line item 3
    When I group documents by shared PO line items
    Then I should get 2 groups
    And group 1 should contain invoice "INV-001" and delivery "DR-001"
    And group 2 should contain invoice "INV-002" and delivery "DR-002"

  @story-121 @three_way_match @article_number @implemented
  Scenario: Match by Article Number When Line Numbers Differ
    Given I have a purchase order "PO-001" with line 1 having article "WIDGET-A"
    And I have an invoice line with article "WIDGET-A" at line 10
    And I have a delivery line with article "WIDGET-A" at line 5
    When I check if invoice and delivery should merge into three-way match
    Then the result should be "merge"
    And the shared PO line items should include the line with "WIDGET-A"

  @story-121 @three_way_match @description @implemented
  Scenario: Match by Description When Article Numbers Missing
    Given I have a purchase order "PO-001" with line 1 described as "Red Widget Part"
    And I have an invoice line at position 1 described as "Red Widget Part"
    And I have a delivery line at position 1 described as "Red Widget Part"
    When I check if invoice and delivery should merge into three-way match
    Then the result should be "merge"

  @story-121 @three_way_match @edge_cases @implemented
  Scenario: No Match When Documents Have No Line Items
    Given I have a purchase order "PO-001" with no line items
    And I have an invoice "INV-001" with no line items
    And I have a delivery receipt "DR-001" with no line items
    When I check if invoice and delivery should merge into three-way match
    Then the result should be "no_merge"
    And the reason should be "missing_items"

  @story-121 @three_way_match @normalization @implemented
  Scenario: Article Number Normalization Enables Match
    Given I have a purchase order line with article "ABC-123"
    And I have an invoice line with article "ABC 123"
    And I have a delivery line with article "00ABC123"
    When I check if invoice and delivery should merge into three-way match
    Then the result should be "merge"
    And the article numbers should be normalized to the same value

  @story-121 @three_way_match @complex @implemented
  Scenario: Complex Multi-Document Scenario
    Given I have a purchase order "PO-001" with 5 line items
    And I have 3 invoices covering different subsets of line items
    And I have 2 delivery receipts covering different subsets of line items
    When I group documents by shared PO line items
    Then each group should contain only documents with overlapping line items
    And no document should appear in multiple groups
