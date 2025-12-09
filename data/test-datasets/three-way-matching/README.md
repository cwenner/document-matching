# Three-Way Matching Test Dataset

This dataset supports testing of Invoice-Delivery matching heuristics based on shared Purchase Order line items.

## Dataset Structure

Each scenario is contained in a separate directory with:
- `documents.json` - All documents (PO, Invoice, Delivery Receipt) for the scenario
- `ground_truth.json` - Expected groupings/matches

## Scenarios Covered

### Scenario 1: Simple Match
- **Directory**: `scenario-01-simple-match`
- **Description**: 1 PO, 1 Invoice, 1 Delivery - all line items match perfectly
- **Expected**: All three documents should be grouped together

### Scenario 2: Split Invoicing
- **Directory**: `scenario-02-split-invoicing`
- **Description**: 1 PO with 2 line items, 2 Invoices (each covers 1 line), 1 Delivery (covers both)
- **Expected**: All documents grouped together via shared PO lines

### Scenario 3: Split Delivery
- **Directory**: `scenario-03-split-delivery`
- **Description**: 1 PO with 2 line items, 1 Invoice (covers both), 2 Deliveries (each covers 1 line)
- **Expected**: All documents grouped together via shared PO lines

### Scenario 4: Complex Multi-Document
- **Directory**: `scenario-04-complex`
- **Description**: 1 PO with 4 line items, 2 Invoices, 2 Deliveries - need correct pairing
- **Expected**: Correct groupings based on which PO lines each document references

### Scenario 5: Partial Overlap
- **Directory**: `scenario-05-partial-overlap`
- **Description**: 1 PO with 3 lines, Invoice covers lines 1-2, Delivery covers lines 2-3
- **Expected**: All grouped due to overlapping line 2

### Scenario 6: No Overlap
- **Directory**: `scenario-06-no-overlap`
- **Description**: 1 PO with 4 lines, Invoice covers lines 1-2, Delivery covers lines 3-4
- **Expected**: Invoice and Delivery should NOT be grouped together

### Scenario 7: Multiple POs Simple
- **Directory**: `scenario-07-multiple-pos`
- **Description**: 2 POs, 2 Invoices, 2 Deliveries - each pair matches to one PO
- **Expected**: Two separate groups

### Scenario 8: Quantity Variations
- **Directory**: `scenario-08-quantity-variations`
- **Description**: Partial deliveries and invoicing with varying quantities on same PO line
- **Expected**: Documents grouped by PO line reference, regardless of quantity

### Scenario 9: Multiple Items Per Document
- **Directory**: `scenario-09-multiple-items`
- **Description**: Each document has multiple line items referencing different PO lines
- **Expected**: Complex matching based on overlapping PO line references

### Scenario 10: Edge Case - Same Article Different Lines
- **Directory**: `scenario-10-same-article`
- **Description**: Same article number appears on multiple PO lines
- **Expected**: Matching based on specific PO line numbers, not just article numbers

## Document Field Reference

### Purchase Order
- Headers: `orderNumber`, `supplierId`, `orderDate`
- Items: `id` (PO line ID), `lineNumber`, `inventory` (article number), `description`, `quantityOrdered`

### Invoice
- Headers: `invoiceNumber`, `supplierId`, `invoiceDate`, `orderReference` (PO number)
- Items: `lineNumber`, `text` (description), `debit`, `quantity`, `poLineReference` (links to PO line)

### Delivery Receipt
- Headers: `deliveryNumber`, `supplierId`, `deliveryDate`, `orderReference` (PO number)
- Items: `lineNumber`, `text` (description), `quantity`, `poLineReference` (links to PO line)

## Usage

These test datasets can be used to:
1. Develop Invoice-Delivery matching heuristics
2. Evaluate matching accuracy
3. Test edge cases and complex scenarios
4. Validate three-way matching logic
