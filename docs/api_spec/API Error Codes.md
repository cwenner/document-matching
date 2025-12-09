# API Error Codes

This document describes the standardized error response format and error codes used by the Document Matching API.

## Error Response Format

All error responses follow a standardized schema:

```json
{
  "error_code": "ERROR_CODE_CONSTANT",
  "message": "Human-readable error message",
  "detail": "Additional details about the error (optional)",
  "fields": {
    "field_name": "field-specific error message"
  }
}
```

### Fields

- **error_code**: Machine-readable error code constant (see codes below)
- **message**: Brief human-readable description of the error type
- **detail**: Optional additional details about what went wrong
- **fields**: Optional field-specific error information (primarily for validation errors)

## Error Codes

### Client Errors (4xx)

#### VALIDATION_ERROR
**Status Code**: 400 Bad Request
**Description**: Request validation failed due to invalid input data

**Example**:
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "detail": "document.kind: Field required",
  "fields": {
    "document.kind": "Field required"
  }
}
```

#### MISSING_REQUIRED_FIELD
**Status Code**: 400 Bad Request
**Description**: A required field is missing from the request

**Example**:
```json
{
  "error_code": "MISSING_REQUIRED_FIELD",
  "message": "Required field missing",
  "detail": "Field 'document' is required"
}
```

#### INVALID_FIELD_VALUE
**Status Code**: 400 Bad Request
**Description**: A field contains an invalid value

**Example**:
```json
{
  "error_code": "INVALID_FIELD_VALUE",
  "message": "Invalid field value",
  "detail": "document.id must be non-empty"
}
```

#### INVALID_JSON
**Status Code**: 400 Bad Request
**Description**: Request body contains malformed JSON

**Example**:
```json
{
  "error_code": "INVALID_JSON",
  "message": "Invalid JSON",
  "detail": "Failed to parse JSON request body: Expecting ',' delimiter"
}
```

#### UNSUPPORTED_MEDIA_TYPE
**Status Code**: 415 Unsupported Media Type
**Description**: Request Content-Type is not application/json

**Example**:
```json
{
  "error_code": "UNSUPPORTED_MEDIA_TYPE",
  "message": "Unsupported Media Type",
  "detail": "Content-Type must be application/json"
}
```

#### PAYLOAD_TOO_LARGE
**Status Code**: 413 Payload Too Large
**Description**: Request exceeds maximum size limits

**Example**:
```json
{
  "error_code": "PAYLOAD_TOO_LARGE",
  "message": "Payload too large",
  "detail": "Maximum 10000 candidate documents allowed, received 10001"
}
```

#### INVALID_DOCUMENT_KIND
**Status Code**: 400 Bad Request
**Description**: Document kind is not supported

**Example**:
```json
{
  "error_code": "INVALID_DOCUMENT_KIND",
  "message": "Invalid document kind",
  "detail": "Kind 'unsupported-type' is not valid. Valid kinds are: invoice, purchase-order, delivery-receipt"
}
```

#### INVALID_DOCUMENT_FORMAT
**Status Code**: 400 Bad Request
**Description**: Document structure does not match expected format

**Example**:
```json
{
  "error_code": "INVALID_DOCUMENT_FORMAT",
  "message": "Invalid document format",
  "detail": "Document must contain 'id' and 'kind' fields"
}
```

### Server Errors (5xx)

#### INTERNAL_SERVER_ERROR
**Status Code**: 500 Internal Server Error
**Description**: Unexpected server error occurred

**Example**:
```json
{
  "error_code": "INTERNAL_SERVER_ERROR",
  "message": "Internal server error",
  "detail": "An unexpected error occurred while processing the request"
}
```

#### MATCHING_SERVICE_ERROR
**Status Code**: 500 Internal Server Error
**Description**: Matching service failed to process the document

**Example**:
```json
{
  "error_code": "MATCHING_SERVICE_ERROR",
  "message": "Matching service error",
  "detail": "Failed to process document"
}
```

## Error Handling Best Practices

### For API Consumers

1. **Always check HTTP status code first** to determine error category (4xx vs 5xx)
2. **Parse the error_code field** for programmatic error handling
3. **Display the message field** to end users for human-readable context
4. **Use detail field** for debugging and logging
5. **Check fields object** for field-level validation errors

### Example Error Handling

```python
response = requests.post(api_url, json=payload)

if response.status_code != 200:
    error_data = response.json()
    error_code = error_data.get('error_code')

    if error_code == 'VALIDATION_ERROR':
        # Handle validation errors
        fields = error_data.get('fields', {})
        print(f"Validation failed: {fields}")
    elif error_code == 'PAYLOAD_TOO_LARGE':
        # Handle too many candidates
        print("Too many candidates, reduce batch size")
    else:
        # Handle other errors
        print(f"Error: {error_data.get('message')}")
```

## Migration from Previous Error Format

Previous error responses used a simple `{"detail": "error message"}` format. The new format is backward compatible in that:

- All error responses still include descriptive information
- HTTP status codes remain unchanged
- The `detail` field is still present in the new format

However, clients should migrate to using the structured error format for better error handling.
