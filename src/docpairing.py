import collections
import datetime
import logging
import pickle
import re
from typing import Dict, List, Optional, Tuple

import dateparser
import numpy as np
import pandas as pd

from document_utils import get_field
from wfields import get_supplier_ids

# @TODO everything here needs refactoring

# Certainty constants for different match types
REFERENCE_MATCH_CERTAINTY = (
    0.95  # High but not 1.0 to account for OCR/extraction errors
)
SVM_FALLBACK_MIN_CERTAINTY = 0.15  # Minimum certainty for SVM fallback matches


logger = logging.getLogger(__name__)


class DocumentPairingPredictor:
    def __init__(
        self,
        model_path: str = "data/models/document-pairing-svm.pkl",
        svc_threshold: float = 0.15,
        filter_by_supplier: bool = True,
    ) -> None:
        """
        Initialize the document pairing predictor with a trained SVM model.

        Args:
            model_path (str): Path to the pickled SVM model
            svc_threshold (float): Threshold for SVM confidence to consider a match.
                Default is 0.15 to bias towards more matches (more permissive).
        """
        # Load the SVM model
        # TODO: This should ideally be loaded lazily or passed in, not loaded at init globally
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        # Set SVM threshold
        self.svc_threshold = svc_threshold

        # Option to filter by supplier
        self.filter_by_supplier = filter_by_supplier

        # Initialize data structures for tracking documents and pairings
        self.order_reference2invoice_ids = collections.defaultdict(list)
        self.purchase_order_nbr2delivery_ids = collections.defaultdict(list)
        self.purchase_order_nbr2id = {}
        self.id2document = {}
        self.type2id2type2paired_ids = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(list))
        )
        self.ids_have_received_invoices = set()
        self.ids_have_received_deliveries = set()
        self.ids_have_received_purchase_orders = set()
        self.supplier_id2document_ids = collections.defaultdict(list)

    def clear_documents(self) -> None:
        """Clear all document tracking data structures"""
        self.order_reference2invoice_ids.clear()
        self.purchase_order_nbr2delivery_ids.clear()
        self.purchase_order_nbr2id.clear()
        self.id2document.clear()
        self.type2id2type2paired_ids.clear()
        self.ids_have_received_invoices.clear()
        self.ids_have_received_deliveries.clear()
        self.ids_have_received_purchase_orders.clear()
        self.supplier_id2document_ids.clear()

    def record_document(self, doc: Dict, target: Optional[Dict] = None) -> None:
        """
        Record the existence of a document in tracking data structures.
        This is needed to pair with that document in other calls.

        Args:
            doc (dict): The document to record
            target (dict, optional): Target pairings for the document
        """
        self.id2document[doc["id"]] = doc

        if self.filter_by_supplier:
            for supplier_id in get_supplier_ids(doc):
                self.supplier_id2document_ids[supplier_id].append(doc["id"])
        else:
            # Use a stand-in value to group all docs together if not filtering
            self.supplier_id2document_ids[None].append(doc["id"])

        if doc["kind"] == "invoice":
            order_reference = self._get_header(doc, "orderReference")
            if order_reference:
                self.order_reference2invoice_ids[order_reference].append(doc["id"])
        elif doc["kind"] == "delivery-receipt":
            for line in doc.get("items", []):
                po_nbr = get_field(line, "purchaseOrderNumber")
                if po_nbr:
                    self.purchase_order_nbr2delivery_ids[po_nbr].append(doc["id"])
        elif doc["kind"] == "purchase-order":
            po_num = self._get_header(doc, "orderNumber")
            if po_num:
                self.purchase_order_nbr2id[po_num] = doc["id"]

        if target:
            for paired_id in target.get("paired_invoice_ids", []):
                if paired_id in self.id2document:
                    self.type2id2type2paired_ids[doc["kind"]][doc["id"]][
                        self.id2document[paired_id]["kind"]
                    ].append(paired_id)
                    self.ids_have_received_invoices.add(paired_id)
            for paired_id in target.get("paired_delivery_ids", []):
                if paired_id in self.id2document:
                    self.type2id2type2paired_ids[doc["kind"]][doc["id"]][
                        self.id2document[paired_id]["kind"]
                    ].append(paired_id)
                    self.ids_have_received_deliveries.add(paired_id)
            for paired_id in target.get("paired_purchase_order_ids", []):
                if paired_id in self.id2document:
                    self.type2id2type2paired_ids[doc["kind"]][doc["id"]][
                        self.id2document[paired_id]["kind"]
                    ].append(paired_id)
                    self.ids_have_received_purchase_orders.add(paired_id)
            if doc["kind"] == "invoice":
                self.ids_have_received_invoices.update(
                    target.get("paired_invoice_ids", [])
                )
            elif doc["kind"] == "delivery-receipt":
                self.ids_have_received_deliveries.update(
                    target.get("paired_delivery_ids", [])
                )
            elif doc["kind"] == "purchase-order":
                self.ids_have_received_purchase_orders.update(
                    target.get("paired_purchase_order_ids", [])
                )

    def predict_pairings(
        self,
        document: Dict,
        candidate_documents: List[Dict],
        threshold: float = 0.15,
        use_reference_logic: bool = True,
        ignore_chronology: bool = False,
    ) -> List[Tuple[str, float]]:
        """
        Predict pairings between the input document and a list of candidate documents.
        Uses a combination of reference-based logic and SVM predictions.

        Args:
            document (dict): The document to find pairings for
            candidate_documents (list): List of potential matching documents
            threshold (float): Minimum confidence score to include in results
            use_reference_logic (bool): Whether to use reference-based logic first

        Returns:
            list: Ranked list of (document_id, confidence_score) tuples
        """
        # Store all documents for reference
        self.record_document(document)
        for doc in candidate_documents:
            self.record_document(doc)

        # If using reference logic, try that first
        if use_reference_logic:
            ref_pred = self._predict_document_by_order_ref(document)

            # Apply SVM fallback for invoice→PO or PO→invoice when no reference match
            if (
                document["kind"] == "invoice"
                and not ref_pred["paired_purchase_order_ids"]
            ) or (
                document["kind"] == "purchase-order"
                and not ref_pred["paired_invoice_ids"]
            ):
                ref_pred = self._apply_svm_fallback(
                    document,
                    ref_pred,
                    candidate_documents,
                    ignore_chronology=ignore_chronology,
                )

            predictions = []
            # Get any SVM confidence scores that were stored during fallback
            svm_scores = ref_pred.get("_svm_confidence_scores", {})

            # Add invoice pairings
            for doc_id in ref_pred.get("paired_invoice_ids", []):
                if doc_id in [d["id"] for d in candidate_documents]:
                    # Use SVM score if available, otherwise reference match certainty
                    score = svm_scores.get(doc_id, REFERENCE_MATCH_CERTAINTY)
                    predictions.append((doc_id, score))

            # Add delivery pairings
            for doc_id in ref_pred.get("paired_delivery_ids", []):
                if doc_id in [d["id"] for d in candidate_documents]:
                    score = svm_scores.get(doc_id, REFERENCE_MATCH_CERTAINTY)
                    predictions.append((doc_id, score))

            # Add purchase order pairings
            for doc_id in ref_pred.get("paired_purchase_order_ids", []):
                if doc_id in [d["id"] for d in candidate_documents]:
                    score = svm_scores.get(doc_id, REFERENCE_MATCH_CERTAINTY)
                    predictions.append((doc_id, score))

            if predictions:
                return predictions

        # If reference logic didn't find matches or we're not using it, fall back to SVM
        # Determine the valid document pairing types
        if document["kind"] == "invoice":
            valid_candidate_types = ["purchase-order", "delivery-receipt"]
        elif document["kind"] == "purchase-order":
            valid_candidate_types = ["invoice", "delivery-receipt"]
        elif document["kind"] == "delivery-receipt":
            valid_candidate_types = ["purchase-order", "invoice"]
        else:
            valid_candidate_types = ["invoice", "purchase-order", "delivery-receipt"]

        # Get features for each candidate and predict with the SVM
        predictions = []
        for candidate in candidate_documents:
            if candidate["kind"] not in valid_candidate_types:
                continue

            # Skip documents that are chronologically incompatible
            if not self._is_chronologically_valid(document, candidate):
                continue

            # Get comparison features
            feats = self._get_comparison_features(document, candidate)
            feats_eng = self._engineer_features(feats)
            feats_svm, _ = self._features_for_svm(feats_eng)

            # Get prediction probability
            if len(feats_svm) > 0:  # Ensure we have features
                prob = self.model.predict_proba(np.array([feats_svm]))[0, 1]
                if prob >= threshold:
                    predictions.append((candidate["id"], prob))

        # Sort by confidence score in descending order
        predictions.sort(key=lambda x: x[1], reverse=True)

        return predictions

    def predict_best_pairing(
        self,
        document: Dict,
        candidate_documents: List[Dict],
        threshold: float = 0.15,
        use_reference_logic: bool = True,
        ignore_chronology: bool = False,
    ) -> Tuple[Optional[str], float]:
        """
        Predict the single best pairing for a document.

        Args:
            document (dict): The document to find pairings for
            candidate_documents (list): List of potential matching documents
            threshold (float): Minimum confidence score to consider a match
            use_reference_logic (bool): Whether to use reference-based logic first

        Returns:
            tuple: (document_id, confidence_score) or (None, 0) if no match found
        """
        predictions = self.predict_pairings(
            document,
            candidate_documents,
            threshold=threshold,
            use_reference_logic=use_reference_logic,
            ignore_chronology=ignore_chronology,
        )
        if predictions:
            return predictions[0]
        return (None, 0.0)

    def _predict_document_by_order_ref(self, document):
        """
        Predict document pairings based on order references.

        Args:
            document (dict): The document to predict pairings for

        Returns:
            dict: Dictionary with paired document IDs by type
        """
        paired_invoice_ids = []
        paired_delivery_ids = []
        paired_purchase_order_ids = []

        if document["kind"] == "invoice":
            order_reference = self._get_header(document, "orderReference")
            if order_reference in self.purchase_order_nbr2id:
                paired_purchase_order_ids.append(
                    self.purchase_order_nbr2id[order_reference]
                )
            for delivery_id in self.purchase_order_nbr2delivery_ids.get(
                order_reference, []
            ):
                paired_delivery_ids.append(delivery_id)
        elif document["kind"] == "delivery-receipt":
            for line in document.get("items", []):
                po_nbr = get_field(line, "purchaseOrderNumber")
                if po_nbr and po_nbr in self.purchase_order_nbr2id:
                    paired_purchase_order_ids.append(self.purchase_order_nbr2id[po_nbr])
                for invoice_id in self.order_reference2invoice_ids.get(po_nbr, []):
                    paired_invoice_ids.append(invoice_id)
        elif document["kind"] == "purchase-order":
            po_nbr = self._get_header(document, "orderNumber")
            if po_nbr:
                for delivery_id in self.purchase_order_nbr2delivery_ids.get(po_nbr, []):
                    paired_delivery_ids.append(delivery_id)
                for invoice_id in self.order_reference2invoice_ids.get(po_nbr, []):
                    paired_invoice_ids.append(invoice_id)

        # Fallback: if no matched PO for an invoice, search based on supplier
        if not paired_purchase_order_ids and document["kind"] == "invoice":
            candidates = []
            if self.filter_by_supplier:
                for supplier_id in get_supplier_ids(document):
                    candidates += [
                        self.id2document[x]
                        for x in self.supplier_id2document_ids.get(supplier_id, [])
                        if (
                            x in self.id2document
                            and self.id2document[x]["kind"] == "purchase-order"
                            and x not in self.ids_have_received_invoices
                        )
                    ]
            else:
                candidates = [
                    self.id2document[x]
                    for x in self.supplier_id2document_ids.get(None, [])
                    if (
                        x in self.id2document
                        and self.id2document[x]["kind"] == "purchase-order"
                        and x not in self.ids_have_received_invoices
                    )
                ]

            if candidates:
                expected_article_numbers = set(self._get_line_article_numbers(document))
                candidate_article_numbers = [
                    set(self._get_line_article_numbers(x)) for x in candidates
                ]

                # Find maximum matching article numbers
                max_match_counts = [
                    len(expected_article_numbers.intersection(x))
                    for x in candidate_article_numbers
                ]

                if max_match_counts:
                    max_candidate_article_numbers = max(max_match_counts)

                    best_candidates = [
                        x
                        for x, y, count in zip(
                            candidates, candidate_article_numbers, max_match_counts
                        )
                        if count == max_candidate_article_numbers and count > 0
                    ]

                    if (
                        max_candidate_article_numbers == len(expected_article_numbers)
                        and len(best_candidates) == 1
                    ):
                        paired_purchase_order_ids.append(best_candidates[0]["id"])
                    else:
                        # Try amount-based matching
                        invoice_exc_vat_amount = self._get_exc_vat_amount(document)
                        candidate_exc_vat_amounts = [
                            self._get_exc_vat_amount(x) for x in candidates
                        ]
                        amount_diffs = [
                            abs(invoice_exc_vat_amount - x)
                            for x in candidate_exc_vat_amounts
                        ]

                        if amount_diffs:
                            min_amount_diff = min(amount_diffs)
                            if min_amount_diff < 0.5:
                                amount_candidates = [
                                    x
                                    for x, diff in zip(candidates, amount_diffs)
                                    if diff < 0.5
                                ]
                                if (
                                    len(amount_candidates) == 1
                                    and amount_candidates[0] in best_candidates
                                ):
                                    paired_purchase_order_ids.append(
                                        amount_candidates[0]["id"]
                                    )

        if paired_purchase_order_ids:
            paired_purchase_order_ids = paired_purchase_order_ids[:1]

        prediction = {
            "paired_invoice_ids": sorted(set(paired_invoice_ids)),
            "paired_delivery_ids": sorted(set(paired_delivery_ids)),
            "paired_purchase_order_ids": sorted(set(paired_purchase_order_ids)),
        }

        # Make pairings transitive
        prediction = self._make_pairings_transitive(document, prediction)
        return prediction

    def _apply_svm_fallback(
        self,
        document,
        base_pred,
        candidate_documents,
        ignore_chronology=False,
    ):
        """
        Apply SVM fallback for documents that didn't match using reference logic.

        Supports bidirectional matching: invoice→PO and PO→invoice.
        Feature extraction normalizes to canonical (invoice, PO) order.

        Args:
            document (dict): The document to find pairings for
            base_pred (dict): Prediction from reference-based logic
            candidate_documents (list): List of potential matching documents

        Returns:
            dict: Updated prediction with SVM-based matches
        """
        primary_kind = document["kind"]

        # Determine matching direction and result field
        if primary_kind == "invoice":
            target_kind = "purchase-order"
            result_field = "paired_purchase_order_ids"
        elif primary_kind == "purchase-order":
            target_kind = "invoice"
            result_field = "paired_invoice_ids"
        else:
            return base_pred

        # Skip if already has matches for target type
        if len(base_pred.get(result_field, [])) > 0:
            return base_pred

        if self.model is None:
            return base_pred

        supplier_ids = get_supplier_ids(document)
        candidate_ids = []

        # Get candidates of target kind from the same supplier
        if self.filter_by_supplier:
            for doc in candidate_documents:
                if (
                    doc["kind"] == target_kind
                    and (set(get_supplier_ids(doc)) & set(supplier_ids))
                    and (
                        ignore_chronology
                        or self._is_chronologically_valid(document, doc)
                    )
                ):
                    candidate_ids.append(doc["id"])
        else:
            for doc in candidate_documents:
                if doc["kind"] == target_kind and (
                    ignore_chronology or self._is_chronologically_valid(document, doc)
                ):
                    candidate_ids.append(doc["id"])

        if not candidate_ids:
            return base_pred

        feats_list = []
        candidates_list = []

        for candidate_id in candidate_ids:
            candidate_doc = self.id2document[candidate_id]
            # Feature extraction handles canonical order normalization
            feats = self._get_comparison_features(document, candidate_doc)
            feats_eng = self._engineer_features(feats)
            feats_svm, _ = self._features_for_svm(feats_eng)
            feats_list.append(feats_svm)
            candidates_list.append(candidate_id)

        if not feats_list:
            return base_pred

        # Get probabilities from SVM
        X_cand = np.array(feats_list)
        probas = self.model.predict_proba(X_cand)[:, 1]
        best_idx = np.argmax(probas)
        best_score = probas[best_idx]
        best_match_id = candidates_list[best_idx]

        # Apply threshold
        if best_score > self.svc_threshold:
            base_pred[result_field] = [best_match_id]
            # Store the actual SVM confidence score for this match
            base_pred["_svm_confidence_scores"] = base_pred.get(
                "_svm_confidence_scores", {}
            )
            base_pred["_svm_confidence_scores"][best_match_id] = float(best_score)
            # Make transitive again after updating
            base_pred = self._make_pairings_transitive(document, base_pred)

        return base_pred

    def _make_pairings_transitive(self, document, prediction):
        """
        Make document pairings transitive (if A->B and B->C, then A->C).

        Args:
            document (dict): The document being processed
            prediction (dict): Current prediction

        Returns:
            dict: Updated prediction with transitive pairings
        """
        # Create a copy to avoid modifying the original
        prediction = {k: v.copy() for k, v in prediction.items()}

        while True:
            any_change = False
            for paired_id in prediction.get("paired_invoice_ids", []):
                if paired_id in self.type2id2type2paired_ids["invoice"]:
                    for other_id in self.type2id2type2paired_ids["invoice"][paired_id][
                        "delivery-receipt"
                    ]:
                        if other_id not in prediction["paired_delivery_ids"]:
                            prediction["paired_delivery_ids"].append(other_id)
                            any_change = True
                    for other_id in self.type2id2type2paired_ids["invoice"][paired_id][
                        "purchase-order"
                    ]:
                        if other_id not in prediction["paired_purchase_order_ids"]:
                            prediction["paired_purchase_order_ids"].append(other_id)
                            any_change = True

            for paired_id in prediction.get("paired_delivery_ids", []):
                if paired_id in self.type2id2type2paired_ids["delivery-receipt"]:
                    for other_id in self.type2id2type2paired_ids["delivery-receipt"][
                        paired_id
                    ]["invoice"]:
                        if other_id not in prediction["paired_invoice_ids"]:
                            prediction["paired_invoice_ids"].append(other_id)
                            any_change = True
                    for other_id in self.type2id2type2paired_ids["delivery-receipt"][
                        paired_id
                    ]["purchase-order"]:
                        if other_id not in prediction["paired_purchase_order_ids"]:
                            prediction["paired_purchase_order_ids"].append(other_id)
                            any_change = True

            for paired_id in prediction.get("paired_purchase_order_ids", []):
                if paired_id in self.type2id2type2paired_ids["purchase-order"]:
                    for other_id in self.type2id2type2paired_ids["purchase-order"][
                        paired_id
                    ]["invoice"]:
                        if other_id not in prediction["paired_invoice_ids"]:
                            prediction["paired_invoice_ids"].append(other_id)
                            any_change = True
                    for other_id in self.type2id2type2paired_ids["purchase-order"][
                        paired_id
                    ]["delivery-receipt"]:
                        if other_id not in prediction["paired_delivery_ids"]:
                            prediction["paired_delivery_ids"].append(other_id)
                            any_change = True

            if not any_change:
                break

        # Remove self-references based on document type
        if document["kind"] == "invoice":
            prediction["paired_invoice_ids"] = []
        elif document["kind"] == "delivery-receipt":
            prediction["paired_delivery_ids"] = []
        elif document["kind"] == "purchase-order":
            prediction["paired_purchase_order_ids"] = []

        return prediction

    def _is_chronologically_valid(self, doc1, doc2):
        """
        Check if documents are in chronologically valid order

        Args:
            doc1 (dict): First document
            doc2 (dict): Second document

        Returns:
            bool: True if chronologically valid, False otherwise
        """
        try:
            # For invoice-PO pairs, invoice should come after PO
            if doc1["kind"] == "invoice" and doc2["kind"] == "purchase-order":
                date1 = self._get_document_date(doc1)
                date2 = self._get_document_date(doc2)
                if date1 is None or date2 is None:
                    return True  # Assume valid if dates can't be parsed
                return date1 >= date2
            # For PO-invoice pairs, invoice should come after PO
            elif doc1["kind"] == "purchase-order" and doc2["kind"] == "invoice":
                date1 = self._get_document_date(doc1)
                date2 = self._get_document_date(doc2)
                if date1 is None or date2 is None:
                    return True  # Assume valid if dates can't be parsed
                return date1 <= date2
            # Other combinations are always valid
            return True
        except Exception:
            # If date parsing fails, assume valid
            return True

    # @TODO drop this - use get_field instead
    def _get_header(self, doc: Dict, key: str) -> Optional[str]:
        """Get a header value from a document"""
        for h in doc.get("headers", []):
            if h.get("name") == key:
                return h.get("value")
        return None

    # @TODO move to wfields
    def _get_document_date(self, document):
        """Extract date from document"""
        try:
            if "created_at" in document:
                return dateparser.parse(document["created_at"])
            if document["kind"] == "invoice":
                return dateparser.parse(self._get_header(document, "creationTime"))
            elif document["kind"] == "delivery-receipt":
                return dateparser.parse(self._get_header(document, "date"))
            elif document["kind"] == "purchase-order":
                return dateparser.parse(self._get_header(document, "creationTime"))
        except:
            # Default to current date if parsing fails
            return datetime.datetime.now()

    def _get_inc_vat_amount(self, document):
        """Get inclusive VAT amount from document"""
        try:
            vat_amount = self._get_header(document, "incVatAmount")
            if vat_amount is not None:
                return float(vat_amount)

            # Try original data if header doesn't exist
            if (
                document.get("original_data", {})
                .get("interpreted_data", {})
                .get("incVatAmount")
            ):
                return float(
                    document["original_data"]["interpreted_data"]["incVatAmount"]
                )
        except Exception:
            pass
        return 0.0

    def _get_exc_vat_amount(self, document):
        """Get exclusive VAT amount from document"""
        try:
            vat_amount = self._get_header(document, "excVatAmount")
            if vat_amount is not None:
                return float(vat_amount)

            # Try original data if header doesn't exist
            if (
                document.get("original_data", {})
                .get("interpreted_data", {})
                .get("excVatAmount")
            ):
                return float(
                    document["original_data"]["interpreted_data"]["excVatAmount"]
                )
        except Exception:
            pass
        return 0.0

    def _normalize_article_number(self, s):
        """Normalize article numbers for comparison"""
        if not s:
            return s
        s = str(s).replace("-", "")
        s = re.sub(r"\s+", "", s)
        s = re.sub(r"\A0+", "", s)
        return s

    def _get_named_item(self, kvlist, name):
        """Get named item from key-value list"""
        for item in kvlist:
            if item.get("name") == name:
                return item.get("value")
        return None

    def _get_invoice_lines(self, document):
        """Extract invoice lines from document"""
        if document["kind"] != "invoice":
            return []

        og = document.get("original_data", {})
        if not og or not og.get("interpreted_xml"):
            return None

        xml = og["interpreted_xml"]
        if "CreditNote" in xml:
            doc = xml["CreditNote"]
        elif "Invoice" in xml:
            doc = xml["Invoice"]
        else:
            return []

        if "cac:InvoiceLine" in doc:
            invoice_lines = doc["cac:InvoiceLine"]
        elif "InvoiceLine" in doc:
            invoice_lines = doc["InvoiceLine"]
        elif "cac:CreditNoteLine" in doc:
            invoice_lines = doc["cac:CreditNoteLine"]
        elif "CreditNoteLine" in doc:
            invoice_lines = doc["CreditNoteLine"]
        else:
            return []

        if isinstance(invoice_lines, dict):
            invoice_lines = [invoice_lines]

        return invoice_lines

    def _get_line_article_numbers(self, doc, drop_empty=True):
        """Extract article numbers from document lines"""
        article_numbers = []

        try:
            if doc["kind"] == "invoice":
                invoice_lines = self._get_invoice_lines(doc) or []
                article_numbers = [
                    (
                        line.get("cac:SellersItemIdentification")
                        or line.get("SellersItemIdentification")
                        or {}
                    ).get("cbc:ID")
                    or (
                        line.get("cac:SellersItemIdentification")
                        or line.get("SellersItemIdentification")
                        or {}
                    ).get("ID")
                    or None
                    for line in invoice_lines
                ]

                # If we couldn't get article numbers from invoice lines, try items array
                if not article_numbers and "items" in doc:
                    try:
                        article_numbers = []
                        for line in doc["items"]:
                            item_id = get_field(line, "inventory") or get_field(
                                line, "articleNumber"
                            )
                            if item_id:
                                article_numbers.append(item_id)
                    except Exception:
                        pass

            elif doc["kind"] == "purchase-order":
                if "items" in doc:
                    article_numbers = []
                    for line in doc["items"]:
                        item_id = get_field(line, "inventory") or get_field(
                            line, "articleNumber"
                        )
                        if item_id:
                            article_numbers.append(item_id)

            elif doc["kind"] == "delivery-receipt":
                if "items" in doc:
                    article_numbers = []
                    for line in doc["items"]:
                        item_id = get_field(line, "inventory") or get_field(
                            line, "articleNumber"
                        )
                        if item_id:
                            article_numbers.append(item_id)
        except Exception:
            # If article number extraction fails, return empty list
            return []

        article_numbers = [
            self._normalize_article_number(x) for x in article_numbers if x is not None
        ]
        if drop_empty:
            article_numbers = [x for x in article_numbers if x]

        return article_numbers

    def _get_comparison_features(self, doc1, doc2):
        """Calculate comparison features between two documents"""
        features = {}

        # Determine document roles for feature extraction
        if doc1["kind"] == "invoice" and doc2["kind"] == "purchase-order":
            invoice = doc1
            po = doc2
        elif doc1["kind"] == "purchase-order" and doc2["kind"] == "invoice":
            invoice = doc2
            po = doc1
        else:
            # For other document type combinations, create generic features
            return self._get_generic_comparison_features(doc1, doc2)

        # Article number features
        invoice_article_numbers = set(self._get_line_article_numbers(invoice))
        po_article_numbers = set(self._get_line_article_numbers(po))

        features["num_invoice_article_numbers"] = len(invoice_article_numbers)
        features["num_po_article_numbers"] = len(po_article_numbers)
        features["num_matching_article_numbers"] = len(
            invoice_article_numbers.intersection(po_article_numbers)
        )

        # Amount features
        invoice_inc_vat_amount = self._get_inc_vat_amount(invoice)
        po_inc_vat_amount = self._get_inc_vat_amount(po)
        invoice_exc_vat_amount = self._get_exc_vat_amount(invoice)
        po_exc_vat_amount = self._get_exc_vat_amount(po)

        features["exc_vat_amount_diff"] = invoice_exc_vat_amount - po_exc_vat_amount
        features["inc_vat_amount_diff"] = invoice_inc_vat_amount - po_inc_vat_amount
        features["inc_vat_amount_diff_frac"] = (
            2
            * (invoice_inc_vat_amount - po_inc_vat_amount)
            / ((po_inc_vat_amount + invoice_inc_vat_amount) or 1.0)
        )
        features["exc_vat_amount_diff_frac"] = (
            2
            * (invoice_exc_vat_amount - po_exc_vat_amount)
            / ((po_exc_vat_amount + invoice_exc_vat_amount) or 1.0)
        )

        # Date features
        try:
            invoice_date = self._get_document_date(invoice)
            po_date = self._get_document_date(po)
            if invoice_date is not None and po_date is not None:
                features["date_diff"] = (invoice_date - po_date).days
            else:
                features["date_diff"] = 0
        except Exception:
            features["date_diff"] = 0

        # Previous matches feature
        features["num_previously_matched_invoices"] = 0

        return features

    def _get_generic_comparison_features(self, doc1, doc2):
        """Calculate generic comparison features for non-invoice/PO document pairs"""
        features = {}

        # Article number features - try to get article numbers from both documents
        doc1_article_numbers = set(self._get_line_article_numbers(doc1))
        doc2_article_numbers = set(self._get_line_article_numbers(doc2))

        features["num_invoice_article_numbers"] = len(doc1_article_numbers)
        features["num_po_article_numbers"] = len(doc2_article_numbers)
        features["num_matching_article_numbers"] = len(
            doc1_article_numbers.intersection(doc2_article_numbers)
        )

        # Amount features - try to get amounts and calculate differences
        try:
            doc1_inc_vat_amount = self._get_inc_vat_amount(doc1)
            doc2_inc_vat_amount = self._get_inc_vat_amount(doc2)
            doc1_exc_vat_amount = self._get_exc_vat_amount(doc1)
            doc2_exc_vat_amount = self._get_exc_vat_amount(doc2)

            features["exc_vat_amount_diff"] = doc1_exc_vat_amount - doc2_exc_vat_amount
            features["inc_vat_amount_diff"] = doc1_inc_vat_amount - doc2_inc_vat_amount
            features["inc_vat_amount_diff_frac"] = (
                2
                * (doc1_inc_vat_amount - doc2_inc_vat_amount)
                / ((doc2_inc_vat_amount + doc1_inc_vat_amount) or 1.0)
            )
            features["exc_vat_amount_diff_frac"] = (
                2
                * (doc1_exc_vat_amount - doc2_exc_vat_amount)
                / ((doc2_exc_vat_amount + doc1_exc_vat_amount) or 1.0)
            )
        except Exception:
            # If amount extraction fails, use zero differences
            features["exc_vat_amount_diff"] = 0
            features["inc_vat_amount_diff"] = 0
            features["inc_vat_amount_diff_frac"] = 0
            features["exc_vat_amount_diff_frac"] = 0

        # Date features
        try:
            doc1_date = self._get_document_date(doc1)
            doc2_date = self._get_document_date(doc2)
            if doc1_date is not None and doc2_date is not None:
                features["date_diff"] = (doc1_date - doc2_date).days
            else:
                features["date_diff"] = 0
        except Exception:
            features["date_diff"] = 0

        features["num_previously_matched_invoices"] = 0

        return features

    def _engineer_features(self, features):
        """Engineer additional features from base features"""
        features = features.copy()

        features["missing_invoice_article_numbers"] = (
            features["num_invoice_article_numbers"]
            - features["num_matching_article_numbers"]
        )
        features["extra_po_article_numbers"] = (
            features["num_po_article_numbers"]
            - features["num_matching_article_numbers"]
        )
        features["matching_article_numbers_precision"] = features[
            "num_matching_article_numbers"
        ] / (features["num_invoice_article_numbers"] or 1.0)
        features["matching_article_numbers_recall"] = features[
            "num_matching_article_numbers"
        ] / (features["num_po_article_numbers"] or 1.0)
        features["amount_diff_below_a_sek"] = (
            abs(features["exc_vat_amount_diff"]) < 1
            or abs(features["inc_vat_amount_diff"]) < 1
        )
        features["same_day"] = features["date_diff"] == 0
        features["previously_unmatched"] = (
            features["num_previously_matched_invoices"] == 0
        )

        return features

    def _features_for_svm(self, feat_dict):
        """Convert feature dictionary to SVM-compatible format"""
        out = []
        feature_names = []

        for k, v in feat_dict.items():
            if isinstance(v, pd.Timestamp):
                out.append(v.timestamp())
                feature_names.append(k)
            elif isinstance(v, str):
                continue
            elif isinstance(v, bool):
                out.append(float(v))
                feature_names.append(k)
            elif isinstance(v, datetime.datetime):
                out.append(v.timestamp())
                feature_names.append(k)
            elif isinstance(v, (int, float)):
                out.append(float(v))
                feature_names.append(k)
            else:
                continue

        final_out = []
        final_feature_names = []

        for i, x in enumerate(out):
            final_out.append(max(0, x))
            final_feature_names.append(f"max(0,{feature_names[i]})")
            final_out.append(min(0, x))
            final_feature_names.append(f"min(0,{feature_names[i]})")
            final_out.append(x**2)
            final_feature_names.append(f"{feature_names[i]}^2")
            final_out.append(np.sign(x) * np.log(1 + abs(x)))
            final_feature_names.append(f"log1p|{feature_names[i]}|")

        return final_out, final_feature_names


# Example usage
if __name__ == "__main__":
    try:
        predictor = DocumentPairingPredictor("data/models/document-pairing-svm.pkl")
    except FileNotFoundError as e:
        print("ERROR: SVM model file 'data/models/document-pairing-svm.pkl' not found.")
        raise e
    except Exception as e:
        print(f"ERROR: Failed to load SVM model: {e}")
        raise e

    # Example invoice document
    invoice = {
        "id": "invoice-123",
        "kind": "invoice",
        "created_at": "2023-01-15",
        "headers": [
            {"name": "supplierId", "value": "supplier-456"},
            {"name": "incVatAmount", "value": "1200.50"},
            {"name": "excVatAmount", "value": "1000.00"},
            {"name": "orderReference", "value": "PO123"},
        ],
        # Other invoice details...
    }

    # Example purchase order document
    purchase_order = {
        "id": "po-789",
        "kind": "purchase-order",
        "created_at": "2023-01-10",
        "headers": [
            {"name": "supplierId", "value": "supplier-456"},
            {"name": "incVatAmount", "value": "1200.50"},
            {"name": "excVatAmount", "value": "1000.00"},
            {"name": "orderNumber", "value": "PO123"},
        ],
        "items": [{"fields": [{"name": "inventory", "value": "ABC123"}]}],
    }

    other_purchase_order = {
        "id": "po-790",
        "kind": "purchase-order",
        "created_at": "2023-01-10",
        "headers": [
            {"name": "supplierId", "value": "supplier-789"},
            {"name": "incVatAmount", "value": "2400.50"},
            {"name": "excVatAmount", "value": "2000.00"},
            {"name": "orderNumber", "value": "PO456"},
        ],
        "items": [{"fields": [{"name": "inventory", "value": "XYZ456"}]}],
    }

    # Example delivery receipt
    delivery = {
        "id": "delivery-456",
        "kind": "delivery-receipt",
        "created_at": "2023-01-12",
        "headers": [
            {"name": "supplierInternalId", "value": "supplier-456"},
        ],
        "items": [{"articleNumber": "ABC123", "purchaseOrderNumber": "PO123"}],
    }

    # Demo usage - with reference-based logic first
    print("=== Using reference-based logic first ===")

    # Record documents for reference-based pairing
    predictor.clear_documents()
    for doc in [invoice, purchase_order, other_purchase_order, delivery]:
        predictor.record_document(doc)

    print("\n--- Invoice as primary document ---")
    # Try invoice as the primary document with various candidates
    primary_doc = invoice
    candidates = [purchase_order, other_purchase_order, delivery]
    pairings = predictor.predict_pairings(
        primary_doc, candidates, use_reference_logic=True
    )

    print("Ranked pairings with confidence scores:")
    for doc_id, confidence in pairings:
        print(f"{doc_id}: {confidence:.4f}")

    # Get single best pairing
    best_id, best_score = predictor.predict_best_pairing(
        primary_doc, candidates, use_reference_logic=True
    )
    print(f"Best pairing: {best_id} with confidence {best_score:.4f}")

    print("\n--- Purchase order as primary document ---")
    # Try PO as the primary document with various candidates
    primary_doc = purchase_order
    candidates = [invoice, other_purchase_order, delivery]
    pairings = predictor.predict_pairings(
        primary_doc, candidates, use_reference_logic=True
    )

    print("Ranked pairings with confidence scores:")
    for doc_id, confidence in pairings:
        print(f"{doc_id}: {confidence:.4f}")

    # Get single best pairing
    best_id, best_score = predictor.predict_best_pairing(
        primary_doc, candidates, use_reference_logic=True
    )
    print(f"Best pairing: {best_id} with confidence {best_score:.4f}")

    # Demo usage - using SVM only
    print("\n\n=== Using SVM prediction only ===")

    print("\n--- Invoice as primary document ---")
    # Try invoice as the primary document with various candidates
    primary_doc = invoice
    candidates = [purchase_order, other_purchase_order, delivery]
    pairings = predictor.predict_pairings(
        primary_doc, candidates, use_reference_logic=False
    )

    print("Ranked pairings with confidence scores:")
    for doc_id, confidence in pairings:
        print(f"{doc_id}: {confidence:.4f}")

    # Get single best pairing
    best_id, best_score = predictor.predict_best_pairing(
        primary_doc, candidates, use_reference_logic=False
    )
    print(f"Best pairing: {best_id} with confidence {best_score:.4f}")

    print("\n--- Purchase order as primary document ---")
    # Try PO as the primary document with various candidates
    primary_doc = purchase_order
    candidates = [invoice, other_purchase_order, delivery]
    pairings = predictor.predict_pairings(
        primary_doc, candidates, use_reference_logic=False
    )

    print("Ranked pairings with confidence scores:")
    for doc_id, confidence in pairings:
        print(f"{doc_id}: {confidence:.4f}")

    # Get single best pairing
    best_id, best_score = predictor.predict_best_pairing(
        primary_doc, candidates, use_reference_logic=False
    )
    print(f"Best pairing: {best_id} with confidence {best_score:.4f}")
