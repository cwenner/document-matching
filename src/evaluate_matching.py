import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Set

import requests

from universaljsonencoder import UniversalJSONEncoder

# Configure logging
logging.basicConfig(level=logging.WARNING, format="%(message)s")

from document_utils import DocumentKind, get_field
from matching_service import MatchingService
from try_client import DEFAULT_URL
from wfields import get_supplier_ids


class MatchingEvaluator:
    def __init__(
        self,
        dataset_path: str,
        api_url: str = DEFAULT_URL,
        max_tested: int = 100,
        skip_portion: float = 0.5,
        use_direct_calls: bool = False,
        model_path: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the evaluator with the dataset path and API URL.

        Args:
            dataset_path: Path to the pairing_sequential.json file
            api_url: URL of the matching service endpoint
            max_tested: Maximum number of documents to test (default: 100)
            skip_portion: Portion of documents to use for building history without testing (0.0-1.0)
            use_direct_calls: If True, use direct method calls to matching_service instead of HTTP
            model_path: Path to the model file (only used with direct calls)
        """
        self.dataset_path = dataset_path
        self.api_url = api_url.rstrip("/") + "/"
        self.document_history = []
        self.prediction_results = []
        self.document_accuracies = []
        self.max_tested = max_tested
        self.skip_portion = skip_portion
        self.use_direct_calls = use_direct_calls
        self.model_path = model_path
        # Use (id, kind) tuple as key to avoid collisions between documents of different kinds with same ID
        self.id2document = {}
        self.verbose = verbose

        # We'll use direct field access for document extraction

        if self.use_direct_calls:
            # Create our own service instance for direct calls
            self.matching_service = MatchingService(model_path=self.model_path)
            # Initialize it immediately to catch any issues early
            self.matching_service.initialize()

        self.document_pairings = {}
        # Format: {
        #   "doc_id": {
        #     "invoice": ["invoice_id1", "invoice_id2", ...],
        #     "delivery-receipt": ["delivery_id1", "delivery_id2", ...],
        #     "purchase-order": ["po_id1", "po_id2", ...]
        #   }
        # }
        self.metrics = {
            "invoice": {
                "true_positives": 0,
                "true_negatives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "accuracies": [],
            },
            "delivery": {
                "true_positives": 0,
                "true_negatives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "accuracies": [],
            },
            "purchase-order": {
                "true_positives": 0,
                "true_negatives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "accuracies": [],
            },
        }

    def load_dataset(self):
        """Load the sequential pairing dataset."""
        try:
            # Load JSON data from file
            with open(self.dataset_path, "r") as f:
                data = json.load(f)

            # Extract inputs and targets
            self.inputs = data.get("inputs", [])
            self.targets = data.get("targets", [])

            # Create a mapping from document ID to document for easy lookup
            for document in self.inputs:
                if "id" in document:
                    # Store with composite key to avoid ID collisions between different document types
                    self.id2document[(document["id"], document["kind"])] = document

            if self.verbose:
                print(f"Loaded dataset with {len(self.inputs)} documents")
            return True
        except Exception as e:
            print(f"Error loading dataset: {e}", file=sys.stderr)
            return False

    def print_final_results(self, final_metrics):
        """Print the final evaluation results.

        Args:
            final_metrics: Dictionary with final evaluation metrics
        """
        # Calculate overall document accuracy
        avg_doc_accuracy = (
            sum(self.document_accuracies) / len(self.document_accuracies)
            if self.document_accuracies
            else 0
        )

        # Print header
        print("\n=== Final Evaluation Results ===")
        print(f"\nOVERALL DOCUMENT ACCURACY: {avg_doc_accuracy:.4f}")

        # Print per-document type metrics
        for doc_type, metrics in final_metrics.items():
            if doc_type == "overall":
                continue

            print(f"\n{doc_type.upper()}:")

            # Format precision, recall, and F1 for display
            precision = metrics["precision"]
            recall = metrics["recall"]
            f1 = metrics["f1_score"]
            avg_accuracy = metrics["average_accuracy"]

            precision_str = (
                f"{precision:.4f}" if isinstance(precision, float) else "N/A"
            )
            recall_str = f"{recall:.4f}" if isinstance(recall, float) else "N/A"
            f1_str = f"{f1:.4f}" if isinstance(f1, float) else "N/A"
            accuracy_str = (
                f"{avg_accuracy:.4f}" if isinstance(avg_accuracy, float) else "N/A"
            )

            print(f"  Precision: {precision_str}")
            print(f"  Recall: {recall_str}")
            print(f"  F1 Score: {f1_str}")
            print(f"  Average Accuracy: {accuracy_str}")
            print(f"  True Positives: {metrics['true_positives']}")
            print(f"  True Negatives: {metrics['true_negatives']}")
            print(f"  False Positives: {metrics['false_positives']}")
            print(f"  False Negatives: {metrics['false_negatives']}")

        # Print overall metrics
        print("\nOVERALL:")

        # Format for display
        precision = final_metrics["overall"]["precision"]
        recall = final_metrics["overall"]["recall"]
        f1 = final_metrics["overall"]["f1_score"]
        avg_accuracy = final_metrics["overall"]["average_accuracy"]

        precision_str = f"{precision:.4f}" if isinstance(precision, float) else "N/A"
        recall_str = f"{recall:.4f}" if isinstance(recall, float) else "N/A"
        f1_str = f"{f1:.4f}" if isinstance(f1, float) else "N/A"
        accuracy_str = (
            f"{avg_accuracy:.4f}" if isinstance(avg_accuracy, float) else "N/A"
        )

        print(f"  Precision: {precision_str}")
        print(f"  Recall: {recall_str}")
        print(f"  F1 Score: {f1_str}")
        print(f"  Average Accuracy: {accuracy_str}")
        print(
            f"  True Positives: {sum([m['true_positives'] for m in self.metrics.values()])}"
        )
        print(
            f"  True Negatives: {sum([m['true_negatives'] for m in self.metrics.values()])}"
        )
        print(
            f"  False Positives: {sum([m['false_positives'] for m in self.metrics.values()])}"
        )
        print(
            f"  False Negatives: {sum([m['false_negatives'] for m in self.metrics.values()])}"
        )

        # Save results to file
        output_path = os.path.join(
            os.path.dirname(self.dataset_path), "matching_evaluation_results.json"
        )

        # Create results dictionary for saving
        results = {
            "overall_document_accuracy": float(avg_doc_accuracy),
            "metrics": {
                k: {kk: vv for kk, vv in v.items() if kk != "accuracies"}
                for k, v in self.metrics.items()
            },
            "precision": final_metrics["overall"]["precision"],
            "recall": final_metrics["overall"]["recall"],
            "f1_score": final_metrics["overall"]["f1_score"],
            "average_accuracy": final_metrics["overall"]["average_accuracy"],
        }

        try:
            with open(output_path, "w") as f:
                json.dump(results, f, cls=UniversalJSONEncoder, indent=4)
            print(f"Results saved to {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}", file=sys.stderr)

    def update_document_pairings(
        self, document_id: str, document_kind: str, paired_ids: Dict
    ):
        """
        Update document pairing history with new matches.

        Args:
            document_id: ID of the document to update pairings for
            document_kind: Kind of the document (invoice, purchase-order, delivery-receipt)
            paired_ids: Dictionary with lists of paired IDs by document kind
        """
        if document_id not in self.document_pairings:
            self.document_pairings[document_id] = {
                "invoice": set(),
                "delivery-receipt": set(),
                "purchase-order": set(),
            }

        # Add all paired IDs to the document's pairing history
        for kind, ids in paired_ids.items():
            for paired_id in ids:
                if paired_id not in self.document_pairings[document_id][kind]:
                    self.document_pairings[document_id][kind].add(paired_id)

                # Also update the reverse relationship
                if paired_id not in self.document_pairings:
                    self.document_pairings[paired_id] = {
                        "invoice": set(),
                        "delivery-receipt": set(),
                        "purchase-order": set(),
                    }
                if document_id not in self.document_pairings[paired_id][document_kind]:
                    self.document_pairings[paired_id][document_kind].add(document_id)

    def get_candidates(self, document: Dict) -> List[Dict]:
        """
        Get candidate documents from history based on overlapping supplier_ids.
        Include their pairing history in the returned candidates.

        Args:
            document: The current document

        Returns:
            List of candidate documents with pairing history
        """
        document_supplier_ids = set(get_supplier_ids(document))
        if not document_supplier_ids:
            return []

        candidates = []
        for historical_doc in self.document_history:
            historical_supplier_ids = set(get_supplier_ids(historical_doc))
            # Check for non-empty intersection of supplier IDs
            if document_supplier_ids.intersection(historical_supplier_ids):
                # Create a copy of the historical document
                candidate_doc = dict(historical_doc)

                # Add pairing history if available
                historical_doc_id = historical_doc.get("id")
                if historical_doc_id in self.document_pairings:
                    candidate_doc["pairing_history"] = self.document_pairings[
                        historical_doc_id
                    ]

                candidates.append(candidate_doc)

        return candidates

    def get_matching_candidates(self, document: Dict) -> List[Dict]:
        """
        Get candidate documents from history that have matching supplier IDs.

        Args:
            document: The current document

        Returns:
            List of candidate documents
        """
        document_supplier_ids = set(get_supplier_ids(document))
        if not document_supplier_ids:
            return []

        candidates = []
        for historical_doc in self.document_history:
            historical_supplier_ids = set(get_supplier_ids(historical_doc))
            # Check for non-empty intersection of supplier IDs
            if document_supplier_ids.intersection(historical_supplier_ids):
                # Get the document ID
                historical_doc_id = historical_doc.get("id")

                # Add pairing history to the document if available
                historical_doc_with_history = dict(historical_doc)

                # Include pairing history if available for this document
                if historical_doc_id in self.document_pairings:
                    # Convert sets to lists for JSON serialization
                    pairing_history = {
                        kind: list(doc_ids)
                        for kind, doc_ids in self.document_pairings[
                            historical_doc_id
                        ].items()
                    }
                    historical_doc_with_history["pairing_history"] = pairing_history

                candidates.append(historical_doc_with_history)

        return candidates

    def make_prediction(self, document: Dict, candidates: List[Dict]) -> Dict:
        """
        Send document and candidates to the matching service and get predictions.
        Can either use HTTP API or direct method calls based on configuration.

        Args:
            document: The document to match
            candidates: List of candidate documents

        Returns:
            Prediction response from either API or direct service call
        """
        # Add pairing history to the document if available
        document_id = document.get("id")
        document_with_history = dict(document)

        if document_id in self.document_pairings:
            document_with_history["pairing_history"] = self.document_pairings[
                document_id
            ]

        # Use direct method calls if configured
        if self.use_direct_calls:
            # print(
            #     f"[DIRECT] Predicting for document {document_id} with {len(candidates)} candidates"
            # )
            # start_time = time.time()

            try:
                # Generate a trace_id for logging
                trace_id = f"eval-{document_id}-{int(time.time())}"

                # Call the process_document method directly on our service instance
                report, _ = self.matching_service.process_document(
                    document_with_history, candidates, trace_id
                )
                return report

            except Exception as e:
                print(f"Error making direct prediction: {e}", file=sys.stderr)
                return {}
        else:
            # Use HTTP API (original behavior)
            payload = {
                "document": document_with_history,
                "candidate-documents": candidates,
            }

            print(
                f"[HTTP] Predicting for document {document_id} with {len(candidates)} candidates"
            )

            start_time = time.time()

            try:
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                response = requests.post(
                    self.api_url, headers=headers, json=payload, timeout=60
                )

                elapsed = time.time() - start_time
                print(f"API request completed in {elapsed:.2f} seconds")

                if response.ok:
                    return response.json()
                else:
                    print(
                        f"Error response from API: {response.status_code} - {response.text}",
                        file=sys.stderr,
                    )
                    return {}
            except Exception as e:
                print(f"Error making HTTP prediction: {e}", file=sys.stderr)
                return {}

    def evaluate_document(self, document: Dict, prediction: Dict, target: Dict) -> Dict:
        """
        Evaluate prediction against the expected target.

        Args:
            document: The input document
            prediction: The prediction response from the matching service
            target: The expected target from the dataset

        Returns:
            Dictionary with evaluation results
        """
        document_id = document.get("id")
        document_kind = document.get("kind")

        # Extract predicted IDs from the prediction response
        predicted_invoice_ids = set()
        predicted_delivery_ids = set()
        predicted_purchase_order_ids = set()

        # Check different API response formats
        if prediction:
            # Check for matched_documents format (new API)
            if "matched_documents" in prediction:
                for match in prediction.get("matched_documents", []):
                    match_id = match.get("id")
                    match_kind = match.get("kind")

                    if match_kind == DocumentKind.INVOICE.value:
                        predicted_invoice_ids.add(match_id)
                    elif match_kind == DocumentKind.DELIVERY_RECEIPT.value:
                        predicted_delivery_ids.add(match_id)
                    elif match_kind == DocumentKind.PURCHASE_ORDER.value:
                        predicted_purchase_order_ids.add(match_id)
            # Check for matches format (old API)
            elif "matches" in prediction:
                for match in prediction.get("matches", []):
                    match_id = match.get("id")
                    match_kind = match.get("kind")

                    if match_kind == DocumentKind.INVOICE.value:
                        predicted_invoice_ids.add(match_id)
                    elif match_kind == DocumentKind.DELIVERY_RECEIPT.value:
                        predicted_delivery_ids.add(match_id)
                    elif match_kind == DocumentKind.PURCHASE_ORDER.value:
                        predicted_purchase_order_ids.add(match_id)

        # Get expected IDs from the target
        expected_invoice_ids = set(target.get("paired_invoice_ids", []))
        expected_delivery_ids = set(target.get("paired_delivery_ids", []))
        expected_purchase_order_ids = set(target.get("paired_purchase_order_ids", []))

        # Calculate true positives, false positives, and false negatives
        # Calculate TP, TN, FP, FN metrics for each document type
        invoice_tp = len(predicted_invoice_ids.intersection(expected_invoice_ids))
        invoice_tn = 1 if not predicted_invoice_ids and not expected_invoice_ids else 0
        invoice_fp = len(predicted_invoice_ids - expected_invoice_ids)
        invoice_fn = len(expected_invoice_ids - predicted_invoice_ids)

        delivery_tp = len(predicted_delivery_ids.intersection(expected_delivery_ids))
        delivery_tn = (
            1 if not predicted_delivery_ids and not expected_delivery_ids else 0
        )
        delivery_fp = len(predicted_delivery_ids - expected_delivery_ids)
        delivery_fn = len(expected_delivery_ids - predicted_delivery_ids)

        po_tp = len(
            predicted_purchase_order_ids.intersection(expected_purchase_order_ids)
        )
        po_tn = (
            1
            if not predicted_purchase_order_ids and not expected_purchase_order_ids
            else 0
        )
        po_fp = len(predicted_purchase_order_ids - expected_purchase_order_ids)
        po_fn = len(expected_purchase_order_ids - predicted_purchase_order_ids)

        # Consolidate false negative reporting for better debugging
        if invoice_fn or delivery_fn or po_fn:
            print("\n====================================================")
            print(f"FALSE NEGATIVE REPORT FOR DOCUMENT {document['id']}")
            print("====================================================\n")

            # Document info section
            print("CURRENT DOCUMENT:")
            print(f"  ID: {document['id']}")
            print(f"  Kind: {document['kind']}")

            # Document field details based on kind
            if document["kind"] == "invoice":
                # Get orderReference from header if present
                order_ref = None
                if "orderReference" in document:
                    order_ref = document["orderReference"]
                elif "header" in document and "orderReference" in document["header"]:
                    order_ref = document["header"]["orderReference"]
                print(f"  Order Reference: {order_ref}")
            elif document["kind"] == "delivery-receipt":
                po_numbers = []
                for line in document.get("items", []):
                    po_nbr = get_field(line, "purchaseOrderNumber")
                    if po_nbr and po_nbr not in po_numbers:
                        po_numbers.append(po_nbr)
                print(f"  PO Numbers: {po_numbers}")
            elif document["kind"] == "purchase-order":
                po_number = document["id"]
                print(f"  PO Number: {po_number}")

            # Document header fields
            header = document.get("header", {})
            if header:
                print("  Header Info:")
                for key, value in header.items():
                    if key in [
                        "orderReference",
                        "orderNumber",
                        "documentDate",
                        "supplierName",
                    ]:
                        print(f"    {key}: {value}")

            # Supplier IDs
            supplier_ids = get_supplier_ids(document)
            if supplier_ids:
                print(f"  Supplier IDs: {supplier_ids}")
            print("\n")

            # False negative details by document type
            if invoice_fn:
                missed_invoice_ids = expected_invoice_ids - predicted_invoice_ids
                print(f"INVOICE FALSE NEGATIVES: {invoice_fn}")
                print(f"  Missed invoice IDs: {missed_invoice_ids}")

                # Details for each missed invoice
                for missed_id in missed_invoice_ids:
                    # Use composite key (id, kind) to look up invoice
                    if (missed_id, "invoice") in self.id2document:
                        missed_doc = self.id2document[(missed_id, "invoice")]
                        print("\n  Missed Invoice Details:")
                        print(f"    ID: {missed_id}")
                        # Get orderReference from header if present
                        order_ref = None
                        if "orderReference" in missed_doc:
                            order_ref = missed_doc["orderReference"]
                        elif (
                            "header" in missed_doc
                            and "orderReference" in missed_doc["header"]
                        ):
                            order_ref = missed_doc["header"]["orderReference"]
                        print(f"    Order Reference: {order_ref}")

                        # Header info for the missed document
                        header = missed_doc.get("header", {})
                        if header:
                            for key, value in header.items():
                                if key in [
                                    "orderReference",
                                    "documentDate",
                                    "supplierName",
                                ]:
                                    print(f"    {key}: {value}")

                        # Supplier matching info
                        missed_supplier_ids = get_supplier_ids(missed_doc)
                        print(f"    Supplier IDs: {missed_supplier_ids}")
                        common_suppliers = (
                            set(supplier_ids).intersection(set(missed_supplier_ids))
                            if supplier_ids and missed_supplier_ids
                            else set()
                        )
                        print(f"    Common Suppliers: {common_suppliers}")
                print("\n")

            if delivery_fn:
                missed_delivery_ids = expected_delivery_ids - predicted_delivery_ids
                print(f"DELIVERY FALSE NEGATIVES: {delivery_fn}")
                print(f"  Missed delivery IDs: {missed_delivery_ids}")

                # Details for each missed delivery
                for missed_id in missed_delivery_ids:
                    # Use composite key (id, kind) to look up delivery receipt
                    if (missed_id, "delivery-receipt") in self.id2document:
                        missed_doc = self.id2document[(missed_id, "delivery-receipt")]
                        print("\n  Missed Delivery Details:")
                        print(f"    ID: {missed_id}")
                        po_numbers = []
                        for line in missed_doc.get("items", []):
                            po_nbr = get_field(line, "purchaseOrderNumber")
                            if po_nbr and po_nbr not in po_numbers:
                                po_numbers.append(po_nbr)
                        print(f"    PO Numbers: {po_numbers}")

                        # Header info
                        header = missed_doc.get("header", {})
                        if header:
                            for key, value in header.items():
                                if key in ["documentDate", "supplierName"]:
                                    print(f"    {key}: {value}")

                        # Supplier matching info
                        missed_supplier_ids = get_supplier_ids(missed_doc)
                        print(f"    Supplier IDs: {missed_supplier_ids}")
                        common_suppliers = (
                            set(supplier_ids).intersection(set(missed_supplier_ids))
                            if supplier_ids and missed_supplier_ids
                            else set()
                        )
                        print(f"    Common Suppliers: {common_suppliers}")
                print("\n")

            if po_fn:
                missed_po_ids = (
                    expected_purchase_order_ids - predicted_purchase_order_ids
                )
                print(f"PURCHASE ORDER FALSE NEGATIVES: {po_fn}")
                print(f"  Missed purchase order IDs: {missed_po_ids}")

                # Details for each missed purchase order
                for missed_id in missed_po_ids:
                    # Use composite key (id, kind) to look up purchase order
                    if (missed_id, "purchase-order") in self.id2document:
                        missed_doc = self.id2document[(missed_id, "purchase-order")]
                        print("\n  Missed Purchase Order Details:")
                        print(f"    ID: {missed_id}")
                        po_number = missed_doc["id"]
                        print(f"    PO Number: {po_number}")

                        # Header info
                        header = missed_doc.get("header", {})
                        if header:
                            for key, value in header.items():
                                if key in [
                                    "orderNumber",
                                    "documentDate",
                                    "supplierName",
                                ]:
                                    print(f"    {key}: {value}")

                        # Supplier matching info
                        missed_supplier_ids = get_supplier_ids(missed_doc)
                        print(f"    Supplier IDs: {missed_supplier_ids}")
                        common_suppliers = (
                            set(supplier_ids).intersection(set(missed_supplier_ids))
                            if supplier_ids and missed_supplier_ids
                            else set()
                        )
                        print(f"    Common Suppliers: {common_suppliers}")

            print("\n====================================================\n")

        # Calculate document accuracy
        invoice_accuracy = self._calculate_accuracy(
            predicted_invoice_ids, expected_invoice_ids
        )
        delivery_accuracy = self._calculate_accuracy(
            predicted_delivery_ids, expected_delivery_ids
        )
        po_accuracy = self._calculate_accuracy(
            predicted_purchase_order_ids, expected_purchase_order_ids
        )

        # Calculate overall document accuracy (across all types)
        all_predicted = (
            predicted_invoice_ids
            | predicted_delivery_ids
            | predicted_purchase_order_ids
        )
        all_expected = (
            expected_invoice_ids | expected_delivery_ids | expected_purchase_order_ids
        )
        document_accuracy = self._calculate_accuracy(all_predicted, all_expected)
        self.document_accuracies.append(document_accuracy)

        # Prepare metrics update
        metrics_update = {
            "invoice": {
                "true_positives": invoice_tp,
                "true_negatives": invoice_tn,
                "false_positives": invoice_fp,
                "false_negatives": invoice_fn,
                "accuracy": invoice_accuracy,
            },
            "delivery": {
                "true_positives": delivery_tp,
                "true_negatives": delivery_tn,
                "false_positives": delivery_fp,
                "false_negatives": delivery_fn,
                "accuracy": delivery_accuracy,
            },
            "purchase-order": {
                "true_positives": po_tp,
                "true_negatives": po_tn,
                "false_positives": po_fp,
                "false_negatives": po_fn,
                "accuracy": po_accuracy,
            },
        }

        # Update overall metrics
        self.update_metrics(metrics_update)

        # Prepare result for this document
        document_result = {
            "document_id": document_id,
            "document_kind": document_kind,
            "predicted": {
                "invoice_ids": predicted_invoice_ids,  # Keep as set
                "delivery_ids": predicted_delivery_ids,  # Keep as set
                "purchase_order_ids": predicted_purchase_order_ids,  # Keep as set
            },
            "expected": {
                "invoice_ids": expected_invoice_ids,  # Keep as set
                "delivery_ids": expected_delivery_ids,  # Keep as set
                "purchase_order_ids": expected_purchase_order_ids,  # Keep as set
            },
            "accuracy": {
                "invoice": invoice_accuracy,
                "delivery": delivery_accuracy,
                "purchase_order": po_accuracy,
                "overall": document_accuracy,
            },
            "metrics": metrics_update,
            "prediction": prediction,  # Store the raw prediction response
        }

        return document_result

    def _calculate_accuracy(
        self, predicted_ids: Set[str], expected_ids: Set[str]
    ) -> float:
        """
        Calculate accuracy according to the specified rules:
        * No matches expected, no matches made: 100%
        * No matches expected, matches made: 0%
        * Matches expected, no matches made: 0%
        * Some matches expected, some matches made: |intersect|/|union|

        Args:
            predicted_ids: Set of predicted document IDs
            expected_ids: Set of expected document IDs

        Returns:
            Accuracy score between 0 and 1
        """
        if not expected_ids and not predicted_ids:
            return 1.0  # 100% accurate when no matches expected and none made

        if not expected_ids and predicted_ids:
            return 0.0  # 0% accurate when no matches expected but some made

        if expected_ids and not predicted_ids:
            return 0.0  # 0% accurate when matches expected but none made

        # Calculate Jaccard similarity (intersection over union)
        intersection = len(expected_ids.intersection(predicted_ids))
        union = len(expected_ids.union(predicted_ids))

        return intersection / union if union > 0 else 0.0

    def update_metrics(self, metrics_update: Dict):
        """
        Update the overall metrics with results from a single document.

        Args:
            metrics_update: Metrics from a single document evaluation
        """
        for doc_type, values in metrics_update.items():
            for metric_name, value in values.items():
                if metric_name == "accuracy":
                    # Store accuracy values in a list rather than summing
                    self.metrics[doc_type]["accuracies"].append(value)
                else:
                    # For other metrics (TP, FP, FN), sum as before
                    self.metrics[doc_type][metric_name] += value

    def calculate_precision_recall(self) -> Dict:
        """
        Calculate precision and recall for each document type.

        Returns:
            Dictionary with precision and recall metrics
        """
        results = {}

        for doc_type, values in self.metrics.items():
            tp = values["true_positives"]
            tn = values["true_negatives"]
            fp = values["false_positives"]
            fn = values["false_negatives"]
            accuracies = values["accuracies"]

            # Calculate precision and recall
            # Handle the case where there were no matches expected or found
            if (tp + fp) > 0:
                precision = tp / (tp + fp)
            else:
                # If no matches were predicted at all (neither TP nor FP exists),
                # precision is either perfect (1.0) if there were no matches to find (FN = 0),
                # or undefined if there were matches to find (FN > 0)
                precision = 1.0 if fn == 0 else "N/A"

            if (tp + fn) > 0:
                recall = tp / (tp + fn)
            else:
                # If no matches were expected at all (neither TP nor FN exists),
                # recall is either perfect (1.0) if no matches were incorrectly found (FP = 0),
                # or undefined if some matches were incorrectly found (FP > 0)
                recall = 1.0 if fp == 0 else "N/A"

            # Calculate F1 score
            if (
                isinstance(precision, float)
                and isinstance(recall, float)
                and (precision + recall) > 0
            ):
                f1 = 2 * (precision * recall) / (precision + recall)
            else:
                f1 = "N/A"

            # Calculate average accuracy
            avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else "N/A"

            results[doc_type] = {
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "average_accuracy": avg_accuracy,
                "true_positives": tp,
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
            }

        # Calculate overall metrics
        total_tp = sum(values["true_positives"] for values in self.metrics.values())
        total_tn = sum(values["true_negatives"] for values in self.metrics.values())
        total_fp = sum(values["false_positives"] for values in self.metrics.values())
        total_fn = sum(values["false_negatives"] for values in self.metrics.values())

        # Calculate overall precision and recall with the same logic as above
        if (total_tp + total_fp) > 0:
            overall_precision = total_tp / (total_tp + total_fp)
        else:
            overall_precision = 1.0 if total_fn == 0 else "N/A"

        if (total_tp + total_fn) > 0:
            overall_recall = total_tp / (total_tp + total_fn)
        else:
            overall_recall = 1.0 if total_fp == 0 else "N/A"

        # Calculate overall F1 score
        if (
            isinstance(overall_precision, float)
            and isinstance(overall_recall, float)
            and (overall_precision + overall_recall) > 0
        ):
            overall_f1 = (
                2
                * (overall_precision * overall_recall)
                / (overall_precision + overall_recall)
            )
        else:
            overall_f1 = "N/A"

        # Calculate overall accuracy by averaging all document accuracies
        all_accuracies = []
        for values in self.metrics.values():
            all_accuracies.extend(values["accuracies"])
        overall_accuracy = (
            sum(all_accuracies) / len(all_accuracies) if all_accuracies else "N/A"
        )

        results["overall"] = {
            "precision": overall_precision,
            "recall": overall_recall,
            "f1_score": overall_f1,
            "average_accuracy": overall_accuracy,
            "true_positives": total_tp,
            "true_negatives": total_tn,
            "false_positives": total_fp,
            "false_negatives": total_fn,
        }

        return results

    def run_evaluation(self) -> bool:
        """Run the full evaluation process."""
        if not self.load_dataset():
            return False

        total_documents = len(self.inputs)
        if self.verbose:
            print(f"Total documents: {total_documents}")

        # Calculate how many documents to skip for history building
        skip_count = int(total_documents * self.skip_portion)

        # Calculate how many documents to test
        # If skip portion would leave fewer than max_tested, use whatever is left
        test_count = min(self.max_tested, total_documents - skip_count)

        # Determine the document indices to process and test
        if skip_count + test_count > total_documents:
            # If skip_count + test_count exceeds total documents,
            # prioritize testing the last `test_count` documents
            skip_count = total_documents - test_count

        # Set the start and end indices for testing
        test_start_idx = skip_count
        test_end_idx = skip_count + test_count

        print(f"Total documents: {total_documents}")
        print(f"First {skip_count} documents will only build history (not tested)")
        print(
            f"Will test {test_count} documents (indices {test_start_idx}-{test_end_idx - 1})"
        )

        # First, build history without testing for the skip portion
        for i in range(skip_count):
            document = self.inputs[i]
            target = self.targets[i]
            document_id = document.get("id")
            document_kind = document.get("kind")

            if self.verbose:
                print(
                    f"\nAdding document {i + 1}/{skip_count} to history (not testing): {document_id}"
                )

            # Record expected pairings from the target
            paired_ids = {
                "invoice": target.get("paired_invoice_ids", []),
                "delivery-receipt": target.get("paired_delivery_ids", []),
                "purchase-order": target.get("paired_purchase_order_ids", []),
            }

            # Update document's pairing history with expected matches
            self.update_document_pairings(document_id, document_kind, paired_ids)

            # Just add to history without testing
            self.document_history.append(document)

        # Now process and test documents after the skip portion
        for i in range(test_start_idx, test_end_idx):
            document = self.inputs[i]
            target = self.targets[i]
            document_id = document.get("id")
            document_kind = document.get("kind")

            # print(
            #     f"\nProcessing document {i+1}/{len(self.inputs)} (test {i-test_start_idx+1}/{test_count}): {document['id']}"
            # )

            # Get matching candidates from history with pairing history included

            if document["id"] != "000713" or document["kind"] != "purchase-order":
                self.document_history.append(document)
                continue
            candidates = self.get_matching_candidates(document)

            # Make prediction using the API
            prediction = self.make_prediction(document, candidates)

            # Check accuracy of the prediction against target
            document_result = self.evaluate_document(document, prediction, target)

            # Store result
            self.prediction_results.append(document_result)

            # Extract pairing history from API response (if available)
            if "document" in prediction and "pairing_history" in prediction["document"]:
                api_pairing_history = prediction["document"]["pairing_history"]
                # Update document pairing history with API-returned history
                self.update_document_pairings(
                    document_id, document_kind, api_pairing_history
                )

            # Extract predicted matches from the evaluation result
            predicted_ids = {
                "invoice": document_result["predicted"]["invoice_ids"],
                "delivery-receipt": document_result["predicted"]["delivery_ids"],
                "purchase-order": document_result["predicted"]["purchase_order_ids"],
            }

            # Update pairing history with predicted matches
            self.update_document_pairings(document_id, document_kind, predicted_ids)

            # Update with expected matches as well
            expected_ids = {
                "invoice": document_result["expected"]["invoice_ids"],
                "delivery-receipt": document_result["expected"]["delivery_ids"],
                "purchase-order": document_result["expected"]["purchase_order_ids"],
            }

            # Update pairing history with expected matches
            self.update_document_pairings(document_id, document_kind, expected_ids)

            # Add document to history AFTER making the prediction
            self.document_history.append(document)

            # Only print per-document evaluation results if verbose mode is enabled
            if self.verbose:
                try:
                    logging.debug(
                        f"Document {i + 1} evaluation:\n"
                        f"  invoice: Precision={document_result.get('invoice_precision', 1.0):.2f}, "
                        f"Recall={document_result.get('invoice_recall', 1.0):.2f}, "
                        f"Accuracy={document_result.get('invoice_accuracy', 1.0):.2f}\n"
                        f"  delivery: Precision={document_result.get('delivery_precision', 1.0):.2f}, "
                        f"Recall={document_result.get('delivery_recall', 1.0):.2f}, "
                        f"Accuracy={document_result.get('delivery_accuracy', 1.0):.2f}\n"
                        f"  purchase-order: Precision={document_result.get('po_precision', 1.0):.2f}, "
                        f"Recall={document_result.get('po_recall', 1.0):.2f}, "
                        f"Accuracy={document_result.get('po_accuracy', 1.0):.2f}"
                    )
                except Exception as e:
                    if self.verbose:
                        logging.error(f"Error printing document result: {e}")

        # Calculate final metrics and print results
        final_metrics = self.calculate_precision_recall()
        self.print_final_results(final_metrics)
        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate matching service performance"
    )
    parser.add_argument(
        "--dataset", required=True, help="Path to the pairing_sequential.json file"
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_URL,
        help="URL of the matching service endpoint. Only used with --use-api-calls",
    )
    parser.add_argument(
        "--max-tested",
        type=int,
        default=100,
        help="Maximum number of documents to test",
    )
    parser.add_argument(
        "--skip-portion",
        type=float,
        default=0.5,
        help="Portion of documents to use for building history without testing (0.0-1.0)",
    )
    parser.add_argument(
        "--use-api-calls",
        action="store_true",
        help="Use API calls to matching_service instead of direct method calls",
    )
    parser.add_argument(
        "--model-path",
        help="Path to the model file (only used without --use-api-calls)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed logs",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (sets logging level to DEBUG)",
    )

    args = parser.parse_args()

    # Set logging level based on flags
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif not args.verbose:
        # Silence most logs unless verbose
        logging.getLogger("matching_service").setLevel(logging.WARNING)
        logging.getLogger("match_pipeline").setLevel(logging.WARNING)
        logging.getLogger("itempairing").setLevel(logging.WARNING)

    # We want direct calls if NOT using API calls
    use_direct_calls = not args.use_api_calls

    # Initialize and run evaluator
    evaluator = MatchingEvaluator(
        dataset_path=args.dataset,
        api_url=args.api_url,
        max_tested=args.max_tested,
        skip_portion=args.skip_portion,
        use_direct_calls=use_direct_calls,
        model_path=args.model_path,
        verbose=args.verbose,
    )
    evaluator.run_evaluation()
