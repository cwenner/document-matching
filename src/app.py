import json
import logging
from fastapi import Request, Response, FastAPI, HTTPException
from matching_service import MatchingService
from match_reporter import DeviationSeverity


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("matching_service_api")

# Create a service instance
matching_service = MatchingService()

# --- FastAPI App ---
app = FastAPI()
logger.info(f"✔ Matching Service API Ready")


@app.get("/health")
async def health_handler(_request: Request):
    """Health/readiness probe endpoint."""
    return Response("Ready to match\r\n")


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


def get_dummy_matching_report(document):
    document_id = document.get("id", "<id missing>")
    # Simple hash based logic for dummy data
    if hash(str(document_id)) % 2 == 0:
        return _dummy_no_match_report(document)
    else:
        return _dummy_match_report(document)


def _dummy_no_match_report(document):
    """Generates a dummy V3 no-match report."""
    doc_id = document.get("id", "unknown-id")
    site = document.get("site", "unknown-site")
    kind = document.get("kind", "unknown-kind")  # Use actual kind if available
    # Generate a somewhat unique report ID based on doc ID
    report_id = f"r-nomatch-{hash(str(doc_id)) & 0xfff:03x}"
    return {
        "version": "v3",
        "id": report_id,
        "kind": "match-report",
        "site": site,
        "stage": "output",
        "headers": [],
        "documents": [{"kind": kind, "id": doc_id}],
        "labels": ["no-match"],
        "metrics": [
            {"name": "certainty", "value": 0.95},  # Simplified value
            {
                "name": "deviation-severity",
                "value": DeviationSeverity.NO_SEVERITY.value
            },
            {
                "name": f"{kind}-has-future-match-certainty",
                "value": 0.88,
            },  # Use dynamic kind
        ],
        "deviations": [],
        "itempairs": [],
    }


def _dummy_match_report(document):
    """Generates a dummy V3 match report."""
    doc_id = document.get("id", "unknown-id")
    site = document.get("site", "unknown-site")
    kind = document.get("kind", "invoice")  # Assume invoice for dummy matched pair
    matched_kind = "purchase-order" if kind == "invoice" else "invoice"
    matched_id = (
        f"matched-doc-{hash(str(doc_id)+'-match') & 0xfff:03x}"  # Dummy matched ID
    )
    report_id = f"r-match-{hash(str(doc_id)) & 0xfff:03x}"
    return {
        "version": "v3",
        "id": report_id,
        "kind": "match-report",
        "site": site,
        "stage": "output",
        "headers": [],
        "documents": [
            {"kind": kind, "id": doc_id},
            {"kind": matched_kind, "id": matched_id},
        ],
        "labels": ["match"],
        "metrics": [
            {"name": "certainty", "value": 0.93},  # Simplified value
            {
                "name": "deviation-severity",
                "value": DeviationSeverity.HIGH.value,
            },  # Dummy severity
            {"name": f"{kind}-has-future-match-certainty", "value": 0.98},
            {"name": f"{matched_kind}-has-future-match-certainty", "value": 0.99},
        ],
        "deviations": [  # Dummy deviation
            {
                "code": "amounts-differ",
                "severity": DeviationSeverity.HIGH.value,
                "message": "Incl VAT amount differs by 42.75 (dummy)",
                "field_names": [
                    "headers.incVatAmount",
                    "headers.inc_vat_amount",
                ],  # Example dot notation (if required) or list
                "values": ["1950.25", "1993.00"],
            }
        ],
        "itempairs": [  # Dummy item pair
            {
                "item_indices": [0, 0],  # Dummy indices
                "match_type": "matched",
                "deviation_severity": DeviationSeverity.MEDIUM.value,
                "item_unchanged_certainty": 0.88,
                "deviations": [
                    {
                        "field_names": ["fields.quantity", "fields.quantity"],
                        "values": [9, 11],
                        "severity": DeviationSeverity.MEDIUM.value,
                        "message": "Quantity differs by 2 (dummy)",
                        "code": "quantity-differs",  # Use consistent code
                    }
                ],
            }
        ],
    }
