import json
import requests
import os
import sys
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
                candidates.append(historical_doc)

        return candidates

    def make_prediction(self, document: Dict, candidates: List[Dict]) -> Dict:
        """
        Send document and candidates to the matching service and get predictions.

        Args:
            document: The document to match
            candidates: List of candidate documents

        Returns:
            Prediction response from the service
        """
        payload = {"document": document, "candidate_documents": candidates}

        print(
            f"Making prediction for document {document.get('id')} with {len(candidates)} candidates"
        )

        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=60
            )

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

    def evaluate_prediction(
        self, document: Dict, prediction: Dict, target: Dict
    ) -> Tuple[Dict, Dict]:
        """
        Evaluate prediction against the expected target.

        Args:
            document: The input document
            prediction: The prediction response from the matching service
            target: The expected target from the dataset

        Returns:
            Tuple of (document result, metrics update)
        """
        document_id = document.get("id")
        document_kind = document.get("kind")

        # Extract predicted IDs from the prediction response
        predicted_invoice_ids = set()
        predicted_delivery_ids = set()
        predicted_purchase_order_ids = set()

        if prediction and "matches" in prediction:
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

        # Calculate accuracy for each document type according to the specified rules
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

        # Update metrics
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

        # Prepare result for this document
        document_result = {
            "document_id": document_id,
            "document_kind": document_kind,
            "predicted": {
                "invoice_ids": list(predicted_invoice_ids),
                "delivery_ids": list(predicted_delivery_ids),
                "purchase_order_ids": list(predicted_purchase_order_ids),
            },
            "expected": {
                "invoice_ids": list(expected_invoice_ids),
                "delivery_ids": list(expected_delivery_ids),
                "purchase_order_ids": list(expected_purchase_order_ids),
            },
            "metrics": metrics_update,
        }

        return document_result, metrics_update

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
            print(
                f"\nAdding document {i+1}/{skip_count} to history (not testing): {document.get('id')}"
            )
            # Just add to history without testing
            self.document_history.append(document)

        # Now process and test documents after the skip portion
        for i in range(test_start_idx, test_end_idx):
            document = self.inputs[i]
            target = self.targets[i]
            print(
                f"\nProcessing document {i+1}/{total_documents} (test {i-test_start_idx+1}/{test_count}): {document.get('id')}"
            )

            # Get matching candidates from history
            candidates = self.get_matching_candidates(document)

            # Make prediction
            prediction = self.make_prediction(document, candidates)

            # Evaluate prediction
            document_result, metrics_update = self.evaluate_prediction(
                document, prediction, target
            )

            # Update metrics
            self.update_metrics(metrics_update)

            # Store result
            self.prediction_results.append(document_result)

            # Add document to history AFTER making the prediction
            self.document_history.append(document)

            # Print interim results for this document
            print(f"Document {i+1} evaluation:")
            for doc_type, values in metrics_update.items():
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
                )
            print(f"\nResults saved to {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}", file=sys.stderr)

        return True


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
