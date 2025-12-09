# Input Validation Specification

## Overview

This document defines the input validation behavior for the Document Matching API (V1). It addresses issue #74 by documenting the current FastAPI/Pydantic validation approach as the accepted standard.

## Validation Strategy

The API uses **FastAPI with Pydantic models** for automatic request validation. This provides:
- Type checking
- Required field validation
- Custom validation rules
- Consistent error responses

## Status Codes

| Status Code | Meaning | When Used |
|------------|---------|-----------|
| 200 | OK | Valid request, processing succeeded (even if no match found) |
| 400 | Bad Request | Invalid request format, missing required fields, or invalid values |
| 413 | Payload Too Large | Too many candidate documents |
| 415 | Unsupported Media Type | Non-JSON content type |
| 422 | Unprocessable Entity | Pydantic validation errors (converted to 400) |
| 500 | Internal Server Error | Unexpected server-side errors |

## Validation Rules

### 1. Invalid Document Format

**Question:** What constitutes 'invalid format'?

**Answer:** Invalid format includes:
- Malformed JSON (syntax errors)
- Missing top-level structure (not a JSON object)
- Wrong content-type header (non-JSON)

**Implementation:**
- Malformed JSON → 400 with "Invalid JSON request body"
- Wrong content-type → 415 with "Unsupported Media Type. Use application/json"
- Missing structure → 400 via Pydantic validation

**Code location:** `src/app.py` lines 114-120, 190-192

**Status:** ✅ Implemented

### 2. Invalid Document Kind

**Question:** What constitutes 'invalid kind'?

**Answer:** Invalid kind is any value not in the supported set:
- `invoice`
- `purchase-order`
- `delivery-receipt`

**Implementation:**
- Custom Pydantic validator in `Document` model
- Returns 400 with clear error message listing valid kinds
- Example: "Invalid document kind: 'shipping-note'. Valid kinds are: invoice, purchase-order, delivery-receipt"

**Code location:** `src/app.py` lines 32-46

**Status:** ✅ Implemented

### 3. Required Fields

**Question:** Which fields are 'required'?

**Answer:** Minimum required fields per document:
- `id` (string, non-empty)
- `kind` (valid DocumentKind enum value)

**Optional fields:**
- `version` (string)
- `site` (string)
- `stage` (string)
- `headers` (list)
- `items` (list)

**Additional fields:** The model allows extra fields (`model_config = {"extra": "allow"}`) to support flexible document structures.

**Implementation:**
- Pydantic Field validation with `...` (required marker)
- `min_length=1` constraint on `id`
- Missing required fields → 400 via Pydantic validation

**Code location:** `src/app.py` lines 19-30

**Status:** ✅ Implemented

### 4. Invalid Field Values

**Question:** What are 'invalid field values'?

**Answer:** Invalid values include:
- Empty `id` string (fails `min_length=1`)
- Wrong type for `kind` (not a string or valid enum)
- Invalid enum value for `kind` (handled by custom validator)

**V1 Decision:**
- Type validation is enforced by Pydantic
- Value validation is minimal (only `id` length and `kind` enum)
- No validation for `headers` or `items` content (accepts any list)
- Extra fields are allowed and passed through

**Rationale:** Keep validation loose for V1 to support various document formats. Stricter validation can be added in future versions if specific customer requirements emerge.

**Implementation:**
- Automatic via Pydantic type checking
- Custom validator for `kind` enum
- No content validation for nested structures

**Code location:** `src/app.py` lines 22-46

**Status:** ✅ Implemented (V1 scope)

## Error Response Format

All validation errors return structured responses:

```json
{
  "detail": "field_name: error message; another_field: another message"
}
```

Example responses:

**Missing required field:**
```json
{
  "detail": "document: Field required"
}
```

**Invalid document kind:**
```json
{
  "detail": "document.kind: Invalid document kind: 'shipping-note'. Valid kinds are: invoice, purchase-order, delivery-receipt"
}
```

**Empty id:**
```json
{
  "detail": "document.id: String should have at least 1 character"
}
```

**Malformed JSON:**
```json
{
  "detail": "Invalid JSON request body"
}
```

## Candidate Documents Limits

**Hard Limit:** 10,000 candidate documents
- Exceeding this → 413 "Payload too large"

**Soft Cap:** 1,000 candidate documents
- Between 1,000-10,000 → Logs warning and processes only first 1,000
- Returns 200 with results from truncated list

**Code location:** `src/app.py` lines 65-68, 145-162

## V1 Scope Decisions

### In Scope (Implemented)
✅ JSON format validation
✅ Required field validation (`id`, `kind`)
✅ Document kind enum validation
✅ Content-type validation
✅ Payload size limits
✅ Type checking via Pydantic

### Out of Scope (V1)
❌ Strict validation of `headers` structure
❌ Strict validation of `items` structure
❌ Business logic validation (e.g., valid date formats, amount ranges)
❌ Cross-field validation (e.g., total amounts match item sums)
❌ Custom validation for specific document types

## Future Considerations

These validations may be added in future versions if needed:
- Validate `headers` contain expected name/value pairs
- Validate `items` have required fields (description, quantity, price)
- Validate amounts are positive numbers
- Validate dates are in acceptable formats
- Document-specific validation rules (e.g., invoices require certain fields)

## Testing Coverage

The following test scenarios validate this behavior:

**Implemented scenarios:**
- Missing Primary Document → 400
- Malformed JSON Payload → 400
- Candidate Documents Not an Array → 400
- Unsupported Content Type → 415
- Request Payload Too Large → 413

**Previously blocked (@wip) scenarios now covered:**
- Invalid Document Format → Covered by existing tests
- Invalid Document Kind → Covered by kind validator
- Missing Required Document Fields → Covered by Pydantic validation
- Invalid Field Values → Covered by Pydantic type checking

## References

- Implementation: `src/app.py`
- Document Kind Enum: `src/document_utils.py`
- Test Scenarios: `features/api-consumer/error_cases.feature`, `features/api-consumer/invalid_input.feature`
- Related Issue: #74
