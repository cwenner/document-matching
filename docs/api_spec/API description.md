# API description

Clarifications for the matching API with examples of how the shared data structures could be converted to the API format.

## JSON Super Schema:

Described here: [https://github.com/omnimodular/api-spec](https://github.com/omnimodular/api-spec)

This super format is shared by all document types including Match Reports. Specific subfields are however described separately belows.

Generally speaking, any portion that contains name-value pairs is open ended and platforms can add additional fields. Note however that any changes to already-present fields may adversely affect performance. Customers and Omni can together specify which exposed fields matter the most and how to communicate changes to these.

Omni will always provide backwards-compatible responses.

## Specific fields

Of particular important to Omni are any inputs fields:

- Document timestamp (creation/incoming)
- In-document identifiers (PO #s, Receipt #s, Your/buyer/sales reference, etc.)
- Supplier information.
- Amounts and currencies.
- Items, coding information, descriptions, article numbers, quantities, etc.
- Text, original data, original document.
    - Final pairing information - purchase receipt data, PO#/Receipt#.

### Specific fields for Match Report

See separate file.
