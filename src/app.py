import json
import sys
import os
import logging
from fastapi import Request, Response, FastAPI, HTTPException


# @TODO split this file up for server vs dummy vs real


from docpairing import DocumentPairingPredictor
from match_pipeline import run_matching_pipeline
from match_reporter import generate_no_match_report, DeviationSeverity


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("matching_service")


# Whitelist of sites to use the real pipeline for
USE_PREDICTION = os.environ.get("DISABLE_MODELS", "false").lower() != "true"
WHITELISTED_SITES = {"badger-logistics", "falcon-logistics", "christopher-test"}


predictor = None

if USE_PREDICTION:
    # @TODO use config file?
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_model_path = os.path.join(
        script_dir, "..", "data", "models", "document-pairing-svm.pkl"
    )
    model_path = os.environ.get("DOCPAIR_MODEL_PATH", default_model_path)

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Predictor model not found. Checked default and environment variable paths. Last check: {os.path.abspath(model_path)}"
        )

    logger.info(
        f"Initializing DocumentPairingPredictor with model: {os.path.abspath(model_path)}"
    )
    predictor = DocumentPairingPredictor(model_path, svc_threshold=0.05)
    logger.info("DocumentPairingPredictor initialized successfully.")


# --- FastAPI App ---
app = FastAPI()
logger.info(f"✔ Matching Service Ready")


def adapt_report_to_v3(report: dict) -> dict:
    """
    Adapts report generated to API spec.
    """
    if not report:
        return report

    v3_report = report.copy()

    v3_report["version"] = "v3"

    if "itempairs" in v3_report and v3_report["itempairs"]:
        for pair in v3_report["itempairs"]:
            pair.pop("match_score", None)  # @TODO name?

    # Fill minimal defaults
    v3_report.setdefault("headers", [])
    v3_report.setdefault("deviations", [])
    v3_report.setdefault("itempairs", [])
    v3_report.setdefault("metrics", [])
    v3_report.setdefault("labels", [])

    return v3_report


@app.get("/")
async def ready_handler(_request: Request):
    """Readiness probe endpoint."""
    return Response("Ready to match\r\n")


@app.post("/")
async def request_handler(request: Request):
    """Handles matching requests."""
    trace_id = request.headers.get("x-om-trace-id", "<x-om-trace-id missing>")

    try:
        indata = await request.json()
        document = indata.get("document")
        candidate_documents = indata.get(
            "candidate_documents", []
        )  # Default to empty list

        if not document or not isinstance(document, dict):
            logger.error(
                f"Trace ID {trace_id}: Invalid or missing 'document' in request body."
            )
            raise HTTPException(
                status_code=400, detail="Missing or invalid 'document' in request body"
            )
        if not isinstance(candidate_documents, list):
            logger.error(
                f"Trace ID {trace_id}: Invalid 'candidate_documents' format, expected a list."
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid 'candidate_documents' format, expected a list",
            )

        doc_id = document.get("id", "<id missing>")
        site = document.get("site", "<site missing>")
        kind = document.get("kind", "<kind missing>")
        stage = document.get("stage", "<stage missing>")

        # Standard Logging
        log_entry = {
            "traceId": trace_id,
            "level": "info",  # Default level
            "site": site,
            "documentId": doc_id,
            "stage": stage,
            "kind": kind,
            "message": f"Received request for document {doc_id} from site {site}.",
            "numCandidates": len(candidate_documents),
        }
        logger.info(json.dumps(log_entry))

        # --- Decision Logic: Whitelist Check ---
        if site in WHITELISTED_SITES and USE_PREDICTION and predictor:
            logger.info(
                f"Trace ID {trace_id}: Site '{site}' is whitelisted. Attempting real pipeline matching."
            )
            try:
                pipeline_report = run_matching_pipeline(
                    predictor, document, candidate_documents
                )

                if pipeline_report is None:
                    logger.error(
                        f"Trace ID {trace_id}: Pipeline run failed critically for document {doc_id}."
                    )
                    raise HTTPException(
                        status_code=500, detail="Matching pipeline failed unexpectedly."
                    )

                final_report = adapt_report_to_v3(pipeline_report)

                if not final_report:
                    logger.error(
                        f"Trace ID {trace_id}: Pipeline returned an error for doc {doc_id}"
                    )
                    raise HTTPException(
                        status_code=500, detail=f"Matching pipeline error"
                    )

                log_entry["message"] = (
                    f"Successfully processed document {doc_id} using pipeline."
                )
                log_entry["matchResult"] = final_report.get("labels", ["unknown"])[
                    0
                ]  # Log match/no-match
                logger.info(json.dumps(log_entry))
                return final_report

            except Exception as e:
                logger.exception(
                    f"Trace ID {trace_id}: Unhandled exception during pipeline execution for document {doc_id}."
                )
                log_entry["level"] = "error"
                log_entry["message"] = (
                    f"Unhandled exception during pipeline execution: {e}"
                )
                logger.error(json.dumps(log_entry))
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error during matching: {e}",
                )

        else:
            dummy_report = get_dummy_matching_report(document)

            log_entry["message"] = f"Processed document {doc_id} using dummy logic."
            log_entry["matchResult"] = dummy_report.get("labels", ["unknown"])[0]
            logger.info(json.dumps(log_entry))
            return dummy_report

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
                "value": DeviationSeverity.NO_SEVERITY.value,
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
