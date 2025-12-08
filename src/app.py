import json
import logging
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from document_utils import DocumentKind
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

# --- FastAPI App ---
app = FastAPI()
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


# Main endpoint for matching - handles all document matching requests
@app.post("/")
async def request_handler(request: Request):
    """Handles matching requests."""
    trace_id = request.headers.get("x-om-trace-id", "<x-om-trace-id missing>")

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
