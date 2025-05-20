import json
import sys
import os
import logging
from typing import Dict, List, Optional, Tuple, Any

from docpairing import DocumentPairingPredictor
from match_pipeline import run_matching_pipeline
from match_reporter import generate_no_match_report, DeviationSeverity

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("matching_service")

# Global configuration
USE_PREDICTION = os.environ.get("DISABLE_MODELS", "false").lower() != "true"
WHITELISTED_SITES = {"badger-logistics", "falcon-logistics", "christopher-test"}

# Global predictor instance
predictor = None


def initialize_predictor() -> Optional[DocumentPairingPredictor]:
    """
    Initialize the DocumentPairingPredictor with the model.
    Returns initialized predictor or None if initialization fails or is disabled.
    """
    global predictor

    if not USE_PREDICTION:
        logger.info("Model prediction is disabled. Will use dummy logic.")
        return None

    try:
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
        predictor = DocumentPairingPredictor(model_path, svc_threshold=0.15)
        logger.info("DocumentPairingPredictor initialized successfully.")
        return predictor
    except Exception as e:
        logger.error(f"Failed to initialize predictor: {e}")
        return None


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


def get_dummy_matching_report(document: Dict) -> Dict:
    """
    Generates a dummy matching report based on the document kind.
    """
    kind = document.get("kind", "unknown")

    if kind == "invoice":
        return _dummy_match_report(document)

    return _dummy_no_match_report(document)


def _dummy_no_match_report(document: Dict) -> Dict:
    """
    Generates a dummy V3 no-match report.
    """
    doc_id = document.get("id", "<id missing>")
    doc_kind = document.get("kind", "unknown")

    report = {
        "version": "v3",
        "headers": [
            {"name": "document1.id", "value": doc_id},
            {"name": "document1.kind", "value": doc_kind},
            {"name": "document2.id", "value": ""},
            {"name": "document2.kind", "value": ""},
        ],
        "deviations": [
            {
                "code": "no-match-found",
                "message": "No matching document found",
                "severity": DeviationSeverity.INFO.value,
            },
            {
                "code": "dummy-logic",
                "message": "Using dummy matching logic",
                "severity": DeviationSeverity.INFO.value,
            },
        ],
        "itempairs": [],
        "metrics": [{"name": "candidate-documents", "value": 0}],
        "labels": ["no-match", "dummy-logic"],
    }

    return report


def _dummy_match_report(document: Dict) -> Dict:
    """
    Generates a dummy V3 match report.
    """
    doc_id = document.get("id", "<id missing>")
    doc_kind = document.get("kind", "unknown")

    # Generate a fake partner document ID
    partner_id = f"DUMMY-{doc_id}-MATCH"
    partner_kind = "purchase_order" if doc_kind == "invoice" else "invoice"

    report = {
        "version": "v3",
        "headers": [
            {"name": "document1.id", "value": doc_id},
            {"name": "document1.kind", "value": doc_kind},
            {"name": "document2.id", "value": partner_id},
            {"name": "document2.kind", "value": partner_kind},
            {"name": "match.confidence", "value": "0.99"},
        ],
        "deviations": [
            {
                "code": "dummy-logic",
                "message": "Using dummy matching logic",
                "severity": DeviationSeverity.INFO.value,
            }
        ],
        "itempairs": [
            {
                "item1": {
                    "id": f"{doc_id}-item-1",
                    "documentId": doc_id,
                    "amount": "100.00",
                    "quantity": "1",
                },
                "item2": {
                    "id": f"{partner_id}-item-1",
                    "documentId": partner_id,
                    "amount": "100.00",
                    "quantity": "1",
                },
                "deviations": [],
            }
        ],
        "metrics": [{"name": "candidate-documents", "value": 1}],
        "labels": ["match", "dummy-logic"],
    }

    return report


def process_document(
    document: Dict,
    candidate_documents: List[Dict],
    trace_id: str = "<trace_id missing>",
) -> Tuple[Dict, Dict]:
    """
    Process a document against candidate documents and return a matching report.

    Args:
        document: The document to process
        candidate_documents: List of candidate documents to match against
        trace_id: Trace ID for logging

    Returns:
        tuple containing (matching report, log entry)
    """
    global predictor

    doc_id = document.get("id", "<id missing>")
    site = document.get("site", "<site missing>")
    kind = document.get("kind", "<kind missing>")
    stage = document.get("stage", "<stage missing>")

    # Create log entry
    log_entry = {
        "traceId": trace_id,
        "level": "info",  # Default level
        "site": site,
        "documentId": doc_id,
        "stage": stage,
        "kind": kind,
        "message": f"Processing document {doc_id} from site {site}.",
        "numCandidates": len(candidate_documents),
    }

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
                log_entry["level"] = "error"
                log_entry["message"] = (
                    f"Pipeline run failed critically for document {doc_id}."
                )
                return None, log_entry

            final_report = adapt_report_to_v3(pipeline_report)
            final_report["metrics"].append(
                {"name": "candidate-documents", "value": len(candidate_documents)}
            )

            if not final_report:
                logger.error(
                    f"Trace ID {trace_id}: Pipeline returned an error for doc {doc_id}"
                )
                log_entry["level"] = "error"
                log_entry["message"] = f"Pipeline returned an error for doc {doc_id}"
                return None, log_entry

            log_entry["message"] = (
                f"Successfully processed document {doc_id} using pipeline."
            )
            log_entry["matchResult"] = final_report.get("labels", ["unknown"])[
                0
            ]  # Log match/no-match
            return final_report, log_entry

        except Exception as e:
            logger.exception(
                f"Trace ID {trace_id}: Unhandled exception during pipeline execution for document {doc_id}."
            )
            log_entry["level"] = "error"
            log_entry["message"] = f"Unhandled exception during pipeline execution: {e}"
            return None, log_entry

    else:
        dummy_report = get_dummy_matching_report(document)
        dummy_report["metrics"].append(
            {"name": "candidate-documents", "value": len(candidate_documents)}
        )

        log_entry["message"] = f"Processed document {doc_id} using dummy logic."
        log_entry["matchResult"] = dummy_report.get("labels", ["unknown"])[0]
        return dummy_report, log_entry


# Initialize the predictor when the module is imported
predictor = initialize_predictor()
