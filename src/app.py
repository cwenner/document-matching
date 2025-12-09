import json
import logging
import time
import uuid
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from document_utils import DocumentKind
from matching_service import MatchingService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("matching_service_api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    def __init__(self, app, log_level: int = logging.INFO):
        super().__init__(app)
        self.log_level = log_level

    async def dispatch(self, request: Request, call_next):
        """Process request and log details."""
        # Generate or extract request ID
        request_id = request.headers.get("x-om-trace-id")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store request ID for use in handlers
        request.state.request_id = request_id

        # Log incoming request
        start_time = time.time()
        logger.log(
            self.log_level,
            f"Request ID {request_id}: {request.method} {request.url.path} - "
            f"Headers: {dict(request.headers)}",
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration = time.time() - start_time
            logger.error(
                f"Request ID {request_id}: {request.method} {request.url.path} - "
                f"Exception: {str(e)} - Duration: {duration:.3f}s"
            )
            raise

        # Log response
        duration = time.time() - start_time
        logger.log(
            self.log_level,
            f"Request ID {request_id}: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {duration:.3f}s",
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


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

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware, log_level=logging.INFO)

logger.info("✔ Matching Service API Ready")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic validation errors to 400 responses with clear messages."""
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = ".".join(str(x) for x in error.get("loc", []))
        msg = error.get("msg", "validation error")
        error_messages.append(f"{loc}: {msg}")
    detail = "; ".join(error_messages) if error_messages else "Validation error"
    return JSONResponse(status_code=400, content={"detail": detail})


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


@app.get("/health/circuit-breakers")
async def circuit_breakers_handler(_request: Request):
    """Circuit breaker status endpoint - shows status of all circuit breakers."""
    try:
        from src.external_service_client import get_all_circuit_breaker_statuses

        statuses = get_all_circuit_breaker_statuses()
        return {"circuit_breakers": statuses}
    except Exception as e:
        logger.warning(f"Failed to get circuit breaker statuses: {e}")
        return {"circuit_breakers": {}, "error": "Circuit breaker monitoring not available"}


# Main endpoint for matching - handles all document matching requests
@app.post("/")
async def request_handler(request: Request):
    """Handles matching requests."""
    trace_id = request.headers.get("x-om-trace-id", "<x-om-trace-id missing>")

    # Validate Content-Type header (case-insensitive per RFC 7231)
    content_type = request.headers.get("content-type", "")
    if content_type and not content_type.lower().startswith("application/json"):
        logger.error(f"Trace ID {trace_id}: Unsupported Content-Type: {content_type}")
        raise HTTPException(
            status_code=415, detail="Unsupported Media Type. Use application/json"
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
            raise HTTPException(status_code=400, detail=str(validation_error))

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
            raise HTTPException(
                status_code=413,
                detail=f"Payload too large. Maximum {MAX_CANDIDATE_DOCUMENTS} candidate documents allowed",
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
            raise HTTPException(
                status_code=500, detail="Matching service failed to process document"
            )

        # Log success and return result
        logger.info(json.dumps(log_entry))
        return final_report

    except json.JSONDecodeError:
        logger.error(f"Trace ID {trace_id}: Failed to decode JSON request body.")
        raise HTTPException(status_code=400, detail="Invalid JSON request body")
    except RequestValidationError:
        # Re-raise validation errors to let FastAPI handle them
        raise
    except HTTPException as e:
        # Re-raise HTTPExceptions to let FastAPI handle them
        raise e
    except Exception as e:
        logger.exception(f"Trace ID {trace_id}: Unexpected error in request handler.")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
