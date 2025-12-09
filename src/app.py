import json
import logging
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from document_utils import DocumentKind
from error_codes import ErrorCode, StandardErrorResponse
from matching_service import MatchingService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("matching_service_api")


class Document(BaseModel):
    """Pydantic model for document validation."""

    id: str = Field(..., min_length=1, description="Document identifier")
    kind: DocumentKind = Field(..., description="Document type")
    version: Optional[str] = None
    site: Optional[str] = None
    stage: Optional[str] = None
    headers: Optional[List[Any]] = None
    items: Optional[List[Any]] = None

    model_config = {"extra": "allow", "use_enum_values": True}

    @field_validator("kind", mode="before")
    @classmethod
    def validate_kind(cls, v: Any) -> DocumentKind:
        if isinstance(v, DocumentKind):
            return v
        if isinstance(v, str):
            try:
                return DocumentKind(v)
            except ValueError:
                valid_kinds = [k.value for k in DocumentKind]
                raise ValueError(
                    f"Invalid document kind: '{v}'. "
                    f"Valid kinds are: {', '.join(valid_kinds)}"
                )
        raise ValueError(f"kind must be a string, got {type(v).__name__}")


class MatchRequest(BaseModel):
    """Pydantic model for match request validation."""

    document: Document = Field(..., description="Primary document to match")
    candidate_documents: List[Document] = Field(
        default=[],
        alias="candidate-documents",
        description="List of candidate documents",
    )

    model_config = {"populate_by_name": True}


# Create a service instance
matching_service = MatchingService()

# Maximum number of candidate documents allowed per request (hard limit - returns 413)
MAX_CANDIDATE_DOCUMENTS = 10000
# Soft cap for processing - logs warning and truncates to this limit
CANDIDATE_PROCESSING_CAP = 1000

# --- FastAPI App ---
app = FastAPI()
logger.info("✔ Matching Service API Ready")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic validation errors to standardized 400 responses."""
    errors = exc.errors()
    error_messages = []
    field_errors = {}

    for error in errors:
        loc = ".".join(str(x) for x in error.get("loc", []))
        msg = error.get("msg", "validation error")
        error_messages.append(f"{loc}: {msg}")
        field_errors[loc] = msg

    detail = "; ".join(error_messages) if error_messages else "Validation error"

    error_response = StandardErrorResponse(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        detail=detail,
        fields=field_errors if field_errors else None,
    )

    return JSONResponse(
        status_code=400, content=error_response.model_dump(exclude_none=True)
    )


def create_error_response(
    error_code: ErrorCode, message: str, detail: Optional[str] = None
) -> dict:
    """Create a standardized error response."""
    error_response = StandardErrorResponse(
        error_code=error_code, message=message, detail=detail
    )
    return error_response.model_dump(exclude_none=True)


@app.get("/health")
async def health_handler(_request: Request):
    """Health probe endpoint."""
    return Response("Ready to match\r\n")


@app.get("/health/readiness")
async def readiness_handler(_request: Request):
    """Readiness probe endpoint - used to determine if the service is ready to accept requests."""
    return {"status": "READY"}


@app.get("/health/liveness")
async def liveness_handler(_request: Request):
    """Liveness probe endpoint - used to determine if the service is running."""
    return {"status": "HEALTHY"}


# Main endpoint for matching - handles all document matching requests
@app.post("/")
async def request_handler(request: Request):
    """Handles matching requests."""
    trace_id = request.headers.get("x-om-trace-id", "<x-om-trace-id missing>")

    # Validate Content-Type header (case-insensitive per RFC 7231)
    content_type = request.headers.get("content-type", "")
    if content_type and not content_type.lower().startswith("application/json"):
        logger.error(f"Trace ID {trace_id}: Unsupported Content-Type: {content_type}")
        return JSONResponse(
            status_code=415,
            content=create_error_response(
                ErrorCode.UNSUPPORTED_MEDIA_TYPE,
                "Unsupported Media Type",
                "Content-Type must be application/json",
            ),
        )

    try:
        # Parse request data
        indata = await request.json()

        # Validate with Pydantic model
        try:
            match_request = MatchRequest.model_validate(indata)
        except Exception as validation_error:
            # Re-raise as RequestValidationError for consistent handling
            from pydantic import ValidationError

            if isinstance(validation_error, ValidationError):
                raise RequestValidationError(validation_error.errors())
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    ErrorCode.VALIDATION_ERROR,
                    "Request validation failed",
                    str(validation_error),
                ),
            )

        # Use validated model data for matching service
        # exclude_none=True maintains backward compatibility with code expecting missing keys
        document = match_request.document.model_dump(by_alias=True, exclude_none=True)
        candidate_documents = [
            doc.model_dump(by_alias=True, exclude_none=True)
            for doc in match_request.candidate_documents
        ]

        # Check candidate document count limit (hard limit)
        if len(candidate_documents) > MAX_CANDIDATE_DOCUMENTS:
            logger.error(
                f"Trace ID {trace_id}: Too many candidate documents: {len(candidate_documents)}"
            )
            return JSONResponse(
                status_code=413,
                content=create_error_response(
                    ErrorCode.PAYLOAD_TOO_LARGE,
                    "Payload too large",
                    f"Maximum {MAX_CANDIDATE_DOCUMENTS} candidate documents allowed, received {len(candidate_documents)}",
                ),
            )

        # Soft cap: if over processing limit, log warning and truncate
        if len(candidate_documents) > CANDIDATE_PROCESSING_CAP:
            original_count = len(candidate_documents)
            candidate_documents = candidate_documents[:CANDIDATE_PROCESSING_CAP]
            logger.warning(
                f"Trace ID {trace_id}: Candidate count {original_count} exceeds processing cap. "
                f"Truncated to first {CANDIDATE_PROCESSING_CAP} candidates."
            )

        # Log request receipt
        doc_id = document.get("id", "<id missing>")
        logger.info(
            f"Trace ID {trace_id}: Processing request for document {doc_id} with {len(candidate_documents)} candidates"
        )

        # Ensure the service is initialized (lazy initialization)
        if matching_service._predictor is None:
            matching_service.initialize()

        # Delegate to matching service for processing
        final_report, log_entry = matching_service.process_document(
            document, candidate_documents, trace_id
        )

        # Handle errors
        if not final_report:
            logger.error(json.dumps(log_entry))
            return JSONResponse(
                status_code=500,
                content=create_error_response(
                    ErrorCode.MATCHING_SERVICE_ERROR,
                    "Matching service error",
                    "Failed to process document",
                ),
            )

        # Log success and return result
        logger.info(json.dumps(log_entry))
        return final_report

    except json.JSONDecodeError as e:
        logger.error(f"Trace ID {trace_id}: Failed to decode JSON request body.")
        return JSONResponse(
            status_code=400,
            content=create_error_response(
                ErrorCode.INVALID_JSON,
                "Invalid JSON",
                f"Failed to parse JSON request body: {str(e)}",
            ),
        )
    except RequestValidationError:
        # Re-raise validation errors to let FastAPI handle them
        raise
    except HTTPException as e:
        # Re-raise HTTPExceptions to let FastAPI handle them
        raise e
    except Exception as e:
        logger.exception(f"Trace ID {trace_id}: Unexpected error in request handler.")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                ErrorCode.INTERNAL_SERVER_ERROR,
                "Internal server error",
                str(e),
            ),
        )
