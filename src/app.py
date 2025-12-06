import json
import logging

from fastapi import FastAPI, HTTPException, Request, Response

from matching_service import MatchingService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("matching_service_api")

# Create a service instance
matching_service = MatchingService()

# --- FastAPI App ---
app = FastAPI()
logger.info("✔ Matching Service API Ready")


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
        document = indata.get("document")
        candidate_documents = indata.get(
            "candidate-documents", []
        )  # Default to empty list

        # Validate request data
        if not document or not isinstance(document, dict):
            logger.error(
                f"Trace ID {trace_id}: Invalid or missing 'document' in request body."
            )
            raise HTTPException(
                status_code=400, detail="Missing or invalid 'document' in request body"
            )
        if not isinstance(candidate_documents, list):
            logger.error(
                f"Trace ID {trace_id}: Invalid 'candidate-documents' format, expected a list."
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid 'candidate-documents' format, expected a list",
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
    except HTTPException as e:
        # Re-raise HTTPExceptions to let FastAPI handle them
        raise e
    except Exception as e:
        logger.exception(f"Trace ID {trace_id}: Unexpected error in request handler.")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
