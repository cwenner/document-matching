import json
from universaljsonencoder import UniversalJSONEncoder
import requests
import os
import sys
import time
from typing import List, Dict, Set, Tuple
from collections import defaultdict

from wfields import get_supplier_ids
from document_utils import DocumentKind
from try_client import DEFAULT_URL


class MatchingEvaluator:
    def __init__(
        self,
        dataset_path: str,
        api_url: str = DEFAULT_URL,
        max_tested: int = 100,
        skip_portion: float = 0.5,
    ):
        """
        Initialize the evaluator with the dataset path and API URL.

        Args:
            dataset_path: Path to the pairing_sequential.json file
            api_url: URL of the matching service endpoint
            max_tested: Maximum number of documents to test (default: 100)
            skip_portion: Portion of documents to use for building history without testing (0.0-1.0)
        """
        self.dataset_path = dataset_path
        self.api_url = api_url.rstrip("/") + "/"
        self.document_history = []
        self.prediction_results = []
        self.document_accuracies = []
        self.max_tested = max_tested
        self.skip_portion = skip_portion

        # Track document pairing history
        # Map from document ID to lists of paired document IDs by document kind
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
            with open(self.dataset_path, "r") as f:
                data = json.load(f)
                self.inputs = data.get("inputs", [])
                self.targets = data.get("targets", [])

            if len(self.inputs) != len(self.targets):
                raise ValueError("Inputs and targets must have the same length")

            print(f"Loaded dataset with {len(self.inputs)} documents")
            return True
        except Exception as e:
            print(f"Error loading dataset: {e}", file=sys.stderr)
            return False

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

        Args:
            document: The document to match
            candidates: List of candidate documents (already include pairing history)

        Returns:
            Prediction response from the service
        """
        # Add pairing history to the document if available
        document_id = document.get("id")
        document_with_history = dict(document)

        if document_id in self.document_pairings:
            document_with_history["pairing_history"] = self.document_pairings[
                document_id
            ]

        payload = {"document": document_with_history, "candidate-documents": candidates}

        print(
            f"Making prediction for document {document_id} with {len(candidates)} candidates"
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
            print(f"Error making prediction: {e}", file=sys.stderr)
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

    def run_evaluation(self):
        """Run the full evaluation process."""
        if not self.load_dataset():
            return False

        total_documents = len(self.inputs)

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
            f"Will test {test_count} documents (indices {test_start_idx}-{test_end_idx-1})"
        )

        # First, build history without testing for the skip portion
        for i in range(skip_count):
            document = self.inputs[i]
            target = self.targets[i]
            document_id = document.get("id")
            document_kind = document.get("kind")

            print(
                f"\nAdding document {i+1}/{skip_count} to history (not testing): {document_id}"
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

            print(
                f"\nProcessing document {i+1}/{total_documents} (test {i-test_start_idx+1}/{test_count}): {document_id}"
            )

            # Get matching candidates from history with pairing history included
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

            # Print interim results for this document
            print(f"Document {i+1} evaluation:")
            for doc_type, values in document_result["metrics"].items():
                # Print accuracy results even if there are no matches (since we handle that case now)
                tp = values.get("true_positives", 0)
                tn = values.get("true_negatives", 0)
                fp = values.get("false_positives", 0)
                fn = values.get("false_negatives", 0)
                accuracy = values.get("accuracy", 0)

                # Format precision and recall with the same logic as in calculate_precision_recall
                if (tp + fp) > 0:
                    precision = tp / (tp + fp)
                    precision_str = f"{precision:.2f}"
                else:
                    precision_str = "1.00" if fn == 0 else "N/A"

                if (tp + fn) > 0:
                    recall = tp / (tp + fn)
                    recall_str = f"{recall:.2f}"
                else:
                    recall_str = "1.00" if fp == 0 else "N/A"

                print(
                    f"  {doc_type}: Precision={precision_str}, Recall={recall_str}, Accuracy={accuracy:.2f}"
                )

        # ---- Moved: Metrics and result saving code ----
        # Calculate final metrics - this will calculate precision and recall for all tested documents combined
        final_metrics = self.calculate_precision_recall()

        # Print final results
        print("\n=== Final Evaluation Results ===")

        # Calculate overall document accuracy
        avg_doc_accuracy = (
            sum(self.document_accuracies) / len(self.document_accuracies)
            if self.document_accuracies
            else 0
        )
        print(f"\nOVERALL DOCUMENT ACCURACY: {avg_doc_accuracy:.4f}")

        for doc_type, metrics in final_metrics.items():
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

        # Save results to file
        output_path = os.path.join(
            os.path.dirname(self.dataset_path), "matching_evaluation_results.json"
        )
        try:
            with open(output_path, "w") as f:
                json.dump(
                    {
                        "document_results": self.prediction_results,
                        "final_metrics": final_metrics,
                    },
                    f,
                    indent=2,
                    cls=UniversalJSONEncoder,
                )
            print(f"\nResults saved to {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}", file=sys.stderr)
        return True

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

        # Calculate final metrics - this will calculate precision and recall for all tested documents combined
        final_metrics = self.calculate_precision_recall()

        # Print final results
        print("\n=== Final Evaluation Results ===")

        # Calculate overall document accuracy
        avg_doc_accuracy = (
            sum(self.document_accuracies) / len(self.document_accuracies)
            if self.document_accuracies
            else 0
        )
        print(f"\nOVERALL DOCUMENT ACCURACY: {avg_doc_accuracy:.4f}")

        for doc_type, metrics in final_metrics.items():
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

        # Save results to file
        output_path = os.path.join(
            os.path.dirname(self.dataset_path), "matching_evaluation_results.json"
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate document matching on sequential dataset."
    )
    parser.add_argument(
        "--dataset",
        default="pairing_sequential.json",
        help="Path to the pairing_sequential.json dataset file",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_URL,
        help=f"URL of the matching service endpoint (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--max-tested",
        type=int,
        default=200,
        help="Maximum number of documents to test (default: 100)",
    )
    parser.add_argument(
        "--skip-portion",
        type=float,
        default=0.5,
        help="Portion of documents to use for building history without testing (0.0-1.0)",
    )

    args = parser.parse_args()

    # Initialize and run evaluator
    evaluator = MatchingEvaluator(
        args.dataset, args.api_url, args.max_tested, args.skip_portion
    )
    evaluator.run_evaluation()
