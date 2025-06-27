# Developer Test Data

This directory contains test data files used by the developer BDD tests located in `features/developer/`.

## File Organization

### Sample Documents
- `primary_doc_sample.json` - Sample primary document for ad-hoc testing scenarios
- `candidates_sample.json` - Sample candidate documents for development testing
- `expected_output_sample.json` - Expected match report output for comparison testing

## Usage Scenarios

### Ad-hoc Testing
Files are designed for developer scenarios where:
- Local JSON files need to be loaded for testing
- Quick verification of document processing
- Manual testing of matching logic

### Test Comparison
The expected output file provides:
- Reference match report structure
- Expected field values and formats
- Baseline for comparison testing

## Document Structure

All files follow the v3 document format and use:
- Site: "test-site" for proper ML pipeline testing
- Realistic field values for development scenarios
- Consistent data relationships between primary and candidate documents

## Maintenance

When adding new developer test scenarios:
1. Follow the existing v3 document format
2. Use descriptive IDs prefixed with "DEV-"
3. Include realistic test data that matches domain requirements
4. Ensure candidate documents have logical relationships to primary documents