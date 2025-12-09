"""
Error codes and standardized error response schema for Document Matching API.

This module defines:
- Error codes as constants for consistent error handling
- StandardErrorResponse schema for uniform error responses
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """Standardized error codes for the Document Matching API."""

    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"
    INVALID_JSON = "INVALID_JSON"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    INVALID_DOCUMENT_KIND = "INVALID_DOCUMENT_KIND"
    INVALID_DOCUMENT_FORMAT = "INVALID_DOCUMENT_FORMAT"

    # Server errors (5xx)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    MATCHING_SERVICE_ERROR = "MATCHING_SERVICE_ERROR"


class StandardErrorResponse(BaseModel):
    """Standardized error response schema."""

    error_code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(
        None, description="Additional details about the error"
    )
    fields: Optional[Dict[str, Any]] = Field(
        None, description="Field-specific error information for validation errors"
    )

    model_config = {"json_schema_extra": {"example": {
        "error_code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "detail": "document.kind: Field required",
        "fields": {"document.kind": "Field required"},
    }}}
