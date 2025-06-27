# Operational Test Data

This directory contains test data files used by the operational BDD tests located in `features/operational/`.

## File Organization

### Simple Test Documents
- `simple_primary_doc.json` - Simple primary document for statelessness and configuration testing
- `simple_candidates.json` - Simple candidate documents for operational scenarios

## Usage

These test data files support operational feature testing for:
- **Statelessness assurance** - Testing that requests don't affect each other
- **Configurable matching** - Testing different matching configurations
- **Service behavior** - Testing operational characteristics rather than complex data processing

## Design Philosophy

Operational test data is intentionally simple to:
- Focus on service behavior rather than complex document matching
- Provide predictable inputs for operational testing
- Minimize data complexity that could interfere with operational testing

## Document Characteristics

- **Minimal complexity** - Basic document structure without complex relationships
- **Predictable values** - Simple amounts and identifiers for consistent testing
- **Standard format** - Follows v3 document format with "test-site" designation
- **Quick processing** - Designed for fast operational testing cycles