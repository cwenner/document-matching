# API Consumer Test Data

This directory contains test data files used by the API consumer BDD (Behavior-Driven Development) tests located in `features/api-consumer/`.

## File Organization

### Primary Documents
- `primary_doc_standard.json` - Standard primary document for performance testing
- `primary_doc_shared_po.json` - Primary document with shared PO number for matching tests
- `primary_doc_no_candidates.json` - Primary document for empty candidates test scenarios
- `primary_doc_diff_supplier.json` - Primary document with different supplier for mismatch tests
- `primary_doc_with_attachment.json` - Primary document with attachment metadata

### Candidate Documents
- `candidates_multiple.json` - Multiple candidate documents for performance testing
- `candidates_shared_po.json` - Candidates with shared PO number for matching scenarios
- `candidates_diff_supplier.json` - Candidates with different supplier for mismatch tests
- `candidates_for_attachment_test.json` - Candidates for attachment testing scenarios

### Attachment Test Data
- `interpreted_data.json` - Sample interpreted JSON attachment data
- `interpreted_xml.json` - Sample interpreted XML attachment data

### Error Testing
- `payload_invalid_structure.json` - Invalid payload structure for error handling tests

## Usage

These test data files are loaded by BDD step definitions using the centralized `get_test_data_path()` function from `tests.config`. The files follow the v3 document format and use the whitelisted site "test-site" to ensure proper ML pipeline testing.

## Maintenance

When adding new test scenarios:
1. Create appropriately named JSON files following the existing v3 document format
2. Reference them in the corresponding feature files in `features/api-consumer/`
3. Ensure test data uses realistic values that match the domain model
4. Use "test-site" as the site value for proper ML pipeline testing