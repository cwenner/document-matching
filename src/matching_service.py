import logging
import os
from typing import Dict, List, Optional, Tuple

from docpairing import DocumentPairingPredictor
from itempair_deviations import DocumentKind
from match_pipeline import run_matching_pipeline, run_matching_pipeline_multiple
from match_reporter import DeviationSeverity, calculate_future_match_certainty

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("matching_service")

# Global configuration
USE_PREDICTION = os.environ.get("DISABLE_MODELS", "false").lower() != "true"

# Certainty value when no actual matching is performed (dummy fallback)
# Using 0.5 indicates "unknown/uncertain" since no real matching occurred
DUMMY_CERTAINTY = 0.5

WHITELISTED_SITES = {
    "badger-logistics",
    "falcon-logistics",
    "christopher-test",
    "test-site",
}


class MatchingService:
    """Class that handles document matching operations with proper initialization control."""

    def __init__(self, model_path=None, svc_threshold=0.15):
        """
        Initialize the matching service.

        Args:
            model_path: Optional path to the model file. If not provided, will use default or environment variable
            svc_threshold: Threshold for the SVM classifier. Default 0.15 biases
                towards more matches (more permissive).
        """
        self._predictor = None
        self.model_path = model_path
        self.svc_threshold = svc_threshold

    def initialize(self) -> Optional[DocumentPairingPredictor]:
        """
        Explicitly initialize the predictor.
        Returns initialized predictor or None if initialization fails or is disabled.
        """
        if self._predictor is None:
            self._predictor = self._initialize_predictor()
        return self._predictor

    def _initialize_predictor(self) -> Optional[DocumentPairingPredictor]:
        """
        Initialize the DocumentPairingPredictor with the model.
        Internal method used by initialize().
        """
        if not USE_PREDICTION:
            logger.info("Model prediction is disabled. Will use dummy logic.")
            return None

        try:
            # Use provided model_path or find the default
            if not self.model_path:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                default_model_path = os.path.join(
                    script_dir, "..", "data", "models", "document-pairing-svm.pkl"
                )
                self.model_path = os.environ.get(
                    "DOCPAIR_MODEL_PATH", default_model_path
                )

            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"Predictor model not found. Checked default and environment variable paths. Last check: {os.path.abspath(self.model_path)}"
                )

            logger.info(
                f"Initializing DocumentPairingPredictor with model: {os.path.abspath(self.model_path)}"
            )
            predictor = DocumentPairingPredictor(
                self.model_path, svc_threshold=self.svc_threshold
            )
            logger.info("DocumentPairingPredictor initialized successfully.")
            return predictor
        except Exception as e:
            logger.error(f"Failed to initialize predictor: {e}")
            return None

    def _is_three_way_matching(
        self, document: Dict, candidate_documents: List[Dict]
    ) -> bool:
        """
        Determine if this is a three-way matching scenario.
        Three-way matching involves Invoice + PO + Delivery Receipt.

        Args:
            document: The primary document
            candidate_documents: List of candidate documents

        Returns:
            True if this is a three-way matching scenario
        """
        all_docs = [document] + candidate_documents
        kinds = set(doc.get("kind") for doc in all_docs)

        # Three-way matching: invoice, purchase-order, and delivery-receipt
        return {"invoice", "purchase-order", "delivery-receipt"}.issubset(kinds)

    def adapt_report_to_v3(self, report: dict) -> dict:
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

    def _create_summary(self, reports: List[Dict]) -> Dict:
        """
        Create a summary object for multiple match reports.

        Args:
            reports: List of match reports

        Returns:
            Summary dict with matchCount, linkedDocuments, and overallSeverity
        """
        match_count = sum(1 for r in reports if "matched" in r.get("labels", []))

        # Collect all unique document IDs
        linked_docs = set()
        for report in reports:
            for doc in report.get("documents", []):
                doc_id = doc.get("id")
                if doc_id:
                    linked_docs.add(doc_id)

        # Determine overall severity (highest severity wins)
        severity_order = ["no-severity", "info", "low", "medium", "high"]
        overall_severity = "no-severity"

        for report in reports:
            for metric in report.get("metrics", []):
                if metric.get("name") == "deviation-severity":
                    severity = metric.get("value", "no-severity")
                    if severity_order.index(severity) > severity_order.index(
                        overall_severity
                    ):
                        overall_severity = severity

        return {
            "matchCount": match_count,
            "linkedDocuments": sorted(list(linked_docs)),
            "overallSeverity": overall_severity,
        }

    def get_dummy_matching_report(self, document: Dict) -> Dict:
        """
        Generates a dummy matching report based on hash of document ID.
        """
        document_id = document.get("id", "<id missing>")

        # Simple hash based logic for dummy data - matches app.py implementation
        if hash(str(document_id)) % 2 == 0:
            return self._dummy_no_match_report(document)
        else:
            return self._dummy_match_report(document)

    def _dummy_no_match_report(self, document: Dict) -> Dict:
        """
        Generates a dummy V3 no-match report.
        """
        doc_id = document.get("id", "<id missing>")
        doc_kind = document.get("kind", "unknown")
        site = document.get("site", "unknown-site")

        # Generate a somewhat unique report ID based on doc ID
        report_id = f"r-nomatch-{hash(str(doc_id)) & 0xfff:03x}"

        # Calculate future match certainty using actual function
        try:
            kind_enum = DocumentKind(doc_kind)
            future_certainty = calculate_future_match_certainty(
                document, kind_enum, is_matched=False
            )
        except ValueError:
            # Invalid document kind, use default uncertainty
            future_certainty = DUMMY_CERTAINTY

        report = {
            "version": "v3",
            "id": report_id,
            "kind": "match-report",
            "site": site,
            "stage": "output",
            "headers": [
                {"name": "document1.id", "value": doc_id},
                {"name": "document1.kind", "value": doc_kind},
                {"name": "document2.id", "value": ""},
                {"name": "document2.kind", "value": ""},
            ],
            "documents": [{"kind": doc_kind, "id": doc_id}],
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
            "metrics": [
                {"name": "candidate-documents", "value": 0},
                {"name": "certainty", "value": DUMMY_CERTAINTY},
                {
                    "name": "deviation-severity",
                    "value": DeviationSeverity.NO_SEVERITY.value,
                },
                {
                    "name": f"{doc_kind}-has-future-match-certainty",
                    "value": future_certainty,
                },
            ],
            "labels": ["no-match"],
        }

        return report

    def _dummy_match_report(self, document: Dict) -> Dict:
        """
        Generates a dummy V3 match report.
        """
        doc_id = document.get("id", "<id missing>")
        doc_kind = document.get(
            "kind", "invoice"
        )  # Assume invoice for dummy matched pair
        site = document.get("site", "unknown-site")

        # Generate a fake partner document ID and report ID
        matched_id = f"matched-doc-{hash(str(doc_id) + '-match') & 0xfff:03x}"  # Dummy matched ID
        report_id = f"r-match-{hash(str(doc_id)) & 0xfff:03x}"
        partner_kind = "purchase-order" if doc_kind == "invoice" else "invoice"

        # Calculate future match certainties using actual function
        try:
            kind_enum = DocumentKind(doc_kind)
            doc_future_certainty = calculate_future_match_certainty(
                document, kind_enum, is_matched=True
            )
        except ValueError:
            doc_future_certainty = DUMMY_CERTAINTY

        try:
            partner_kind_enum = DocumentKind(partner_kind)
            # Create a dummy partner document for calculation
            partner_doc = {"kind": partner_kind}
            partner_future_certainty = calculate_future_match_certainty(
                partner_doc, partner_kind_enum, is_matched=True
            )
        except ValueError:
            partner_future_certainty = DUMMY_CERTAINTY

        report = {
            "version": "v3",
            "id": report_id,
            "kind": "match-report",
            "site": site,
            "stage": "output",
            "headers": [
                {"name": "document1.id", "value": doc_id},
                {"name": "document1.kind", "value": doc_kind},
                {"name": "document2.id", "value": matched_id},
                {"name": "document2.kind", "value": partner_kind},
                {"name": "match.confidence", "value": str(DUMMY_CERTAINTY)},
            ],
            "documents": [
                {"kind": doc_kind, "id": doc_id},
                {"kind": partner_kind, "id": matched_id},
            ],
            "deviations": [
                {
                    "code": "dummy-logic",
                    "message": "Using dummy matching logic",
                    "severity": DeviationSeverity.INFO.value,
                },
                {
                    "code": "amounts-differ",
                    "severity": DeviationSeverity.HIGH.value,
                    "message": "Incl VAT amount differs by 42.75 (dummy)",
                    "field_names": [
                        "headers.incVatAmount",
                        "headers.inc_vat_amount",
                    ],
                    "values": ["1950.25", "1993.00"],
                },
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
                        "id": f"{matched_id}-item-1",
                        "documentId": matched_id,
                        "amount": "100.00",
                        "quantity": "1",
                    },
                    "deviations": [],
                    "item_indices": [0, 0],  # Dummy indices
                    "match_type": "matched",
                    "deviation_severity": DeviationSeverity.MEDIUM.value,
                    "item_unchanged_certainty": DUMMY_CERTAINTY,
                }
            ],
            "metrics": [
                {"name": "candidate-documents", "value": 1},
                {"name": "certainty", "value": DUMMY_CERTAINTY},
                {
                    "name": "deviation-severity",
                    "value": DeviationSeverity.HIGH.value,
                },
                {
                    "name": f"{doc_kind}-has-future-match-certainty",
                    "value": doc_future_certainty,
                },
                {
                    "name": f"{partner_kind}-has-future-match-certainty",
                    "value": partner_future_certainty,
                },
            ],
            "labels": ["match"],
        }

        return report

    def process_document(
        self,
        document: Dict,
        candidate_documents: List[Dict],
        trace_id: str = "<trace_id missing>",
    ) -> Tuple[Optional[Dict], Dict]:
        """
        Process a document against candidate documents and return a matching report.

        Args:
            document: The document to process
            candidate_documents: List of candidate documents to match against
            trace_id: Trace ID for logging

        Returns:
            tuple containing (matching report, log entry)
        """
        # Ensure we have a predictor if needed - lazy initialization
        if self._predictor is None and USE_PREDICTION:
            self.initialize()

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
        # @TODO drop this
        if site in WHITELISTED_SITES and USE_PREDICTION and self._predictor:
            logger.info(
                f"Trace ID {trace_id}: Site '{site}' is whitelisted. Attempting real pipeline matching."
            )

            # Check if this is a three-way matching scenario
            is_three_way = self._is_three_way_matching(document, candidate_documents)

            try:
                if is_three_way:
                    logger.info(
                        f"Trace ID {trace_id}: Detected three-way matching scenario. Generating multiple reports."
                    )
                    pipeline_reports = run_matching_pipeline_multiple(
                        self._predictor, document, candidate_documents
                    )

                    if pipeline_reports is None:
                        logger.error(
                            f"Trace ID {trace_id}: Pipeline run failed critically for document {doc_id}."
                        )
                        log_entry["level"] = "error"
                        log_entry["message"] = (
                            f"Pipeline run failed critically for document {doc_id}."
                        )
                        return None, log_entry

                    # Adapt each report to v3
                    adapted_reports = []
                    for report in pipeline_reports:
                        adapted = self.adapt_report_to_v3(report)
                        adapted["metrics"].append(
                            {
                                "name": "candidate-documents",
                                "value": len(candidate_documents),
                            }
                        )
                        adapted_reports.append(adapted)

                    # Create the response with matchReports and summary
                    final_response = {
                        "matchReports": adapted_reports,
                        "summary": self._create_summary(adapted_reports),
                    }

                    log_entry["message"] = (
                        f"Successfully processed three-way matching for document {doc_id}."
                    )
                    log_entry["matchResult"] = "three-way"
                    log_entry["reportCount"] = len(adapted_reports)
                    return final_response, log_entry

                else:
                    # Single pairing - existing behavior
                    pipeline_report = run_matching_pipeline(
                        self._predictor, document, candidate_documents
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

                    final_report = self.adapt_report_to_v3(pipeline_report)
                    final_report["metrics"].append(
                        {"name": "candidate-documents", "value": len(candidate_documents)}
                    )
                    final_report["internal"] = final_report.get("internal", [])
                    final_report["internal"].append(
                        {
                            "name": "candidate-documents",
                            "value": [
                                {"kind": cd["kind"], "id": cd["id"]}
                                for cd in candidate_documents
                            ],
                        }
                    )

                    if not final_report:
                        logger.error(
                            f"Trace ID {trace_id}: Pipeline returned an error for doc {doc_id}"
                        )
                        log_entry["level"] = "error"
                        log_entry["message"] = (
                            f"Pipeline returned an error for doc {doc_id}"
                        )
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
                log_entry["message"] = (
                    f"Unhandled exception during pipeline execution: {e}"
                )
                return None, log_entry

        else:
            dummy_report = self.get_dummy_matching_report(document)
            dummy_report["metrics"].append(
                {"name": "candidate-documents", "value": len(candidate_documents)}
            )

            log_entry["message"] = f"Processed document {doc_id} using dummy logic."
            log_entry["matchResult"] = dummy_report.get("labels", ["unknown"])[0]
            return dummy_report, log_entry
