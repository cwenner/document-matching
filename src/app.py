import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
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


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchRequest(BaseModel):
    """Pydantic model for batch request validation."""

    requests: List[MatchRequest] = Field(
        ..., description="List of match requests to process"
    )


class JobResponse(BaseModel):
    """Response model for job creation."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: str = Field(..., description="Job creation timestamp")


class JobStatusResponse(BaseModel):
    """Response model for job status query."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: str = Field(..., description="Job creation timestamp")
    completed_at: Optional[str] = Field(None, description="Job completion timestamp")
    total_requests: int = Field(..., description="Total number of requests")
    completed_requests: int = Field(..., description="Number of completed requests")
    results: Optional[List[Any]] = Field(None, description="Results if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


# Create a service instance
matching_service = MatchingService()

# Maximum number of candidate documents allowed per request (hard limit - returns 413)
MAX_CANDIDATE_DOCUMENTS = 10000
# Soft cap for processing - logs warning and truncates to this limit
CANDIDATE_PROCESSING_CAP = 1000

# In-memory job storage
jobs: Dict[str, Dict[str, Any]] = {}

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


async def process_batch_job(job_id: str, batch_request: BatchRequest):
    """Background task to process batch requests."""
    try:
        logger.info(f"Job {job_id}: Starting batch processing")
        jobs[job_id]["status"] = JobStatus.PROCESSING

        results = []
        for idx, match_request in enumerate(batch_request.requests):
            try:
                # Convert to dict format expected by matching service
                document = match_request.document.model_dump(
                    by_alias=True, exclude_none=True
                )
                candidate_documents = [
                    doc.model_dump(by_alias=True, exclude_none=True)
                    for doc in match_request.candidate_documents
                ]

                # Apply same limits as main endpoint
                if len(candidate_documents) > MAX_CANDIDATE_DOCUMENTS:
                    raise ValueError(
                        f"Request {idx}: Too many candidate documents: {len(candidate_documents)}"
                    )

                if len(candidate_documents) > CANDIDATE_PROCESSING_CAP:
                    original_count = len(candidate_documents)
                    candidate_documents = candidate_documents[:CANDIDATE_PROCESSING_CAP]
                    logger.warning(
                        f"Job {job_id}, Request {idx}: Candidate count {original_count} exceeds cap. "
                        f"Truncated to {CANDIDATE_PROCESSING_CAP}."
                    )

                # Initialize service if needed
                if matching_service._predictor is None:
                    matching_service.initialize()

                # Process the document
                trace_id = f"batch-{job_id}-{idx}"
                final_report, log_entry = matching_service.process_document(
                    document, candidate_documents, trace_id
                )

                if final_report:
                    results.append(final_report)
                    logger.info(json.dumps(log_entry))
                else:
                    logger.error(json.dumps(log_entry))
                    results.append({"error": "Processing failed", "request_index": idx})

                jobs[job_id]["completed_requests"] = idx + 1

            except Exception as e:
                logger.exception(f"Job {job_id}, Request {idx}: Error processing request")
                results.append({"error": str(e), "request_index": idx})
                jobs[job_id]["completed_requests"] = idx + 1

        # Mark job as completed
        jobs[job_id]["status"] = JobStatus.COMPLETED
        jobs[job_id]["results"] = results
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"Job {job_id}: Completed successfully")

    except Exception as e:
        logger.exception(f"Job {job_id}: Fatal error in batch processing")
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()


@app.post("/batch/async", response_model=JobResponse)
async def create_batch_job(
    batch_request: BatchRequest, background_tasks: BackgroundTasks
):
    """Create an async batch processing job."""
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    # Initialize job in storage
    jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "created_at": created_at,
        "completed_at": None,
        "total_requests": len(batch_request.requests),
        "completed_requests": 0,
        "results": None,
        "error": None,
    }

    # Add background task to process the batch
    background_tasks.add_task(process_batch_job, job_id, batch_request)

    logger.info(
        f"Job {job_id}: Created with {len(batch_request.requests)} requests to process"
    )

    return JobResponse(job_id=job_id, status=JobStatus.PENDING, created_at=created_at)


@app.get("/batch/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a batch processing job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job_data = jobs[job_id]
    return JobStatusResponse(**job_data)
