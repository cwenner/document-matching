import json
import logging
import os

# Keep existing imports
from docpairing import DocumentPairingPredictor
from itempair_deviations import (
    FieldDeviation,
    collect_itempair_deviations,
    create_item_unmatched_deviation,
)
from itempairing import pair_document_items
from match_reporter import DeviationSeverity  # Import DeviationSeverity for adaptation
from match_reporter import (
    collect_document_deviations,
    generate_match_report,
    generate_no_match_report,
)
from wfields import get_document_items, unpack_attachments

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_matching_pipeline(
    predictor: DocumentPairingPredictor,
    input_document: dict,
    historical_documents: list[dict],
):
    """
    Runs the full matching pipeline for a given input document against historical ones.

    Args:
        predictor: An initialized DocumentPairingPredictor instance.
        input_document: The target document dictionary.
        historical_documents: A list of candidate document dictionaries.

    Returns:
        A dictionary representing the match report (either match or no-match).
        Returns None if a critical error occurs during processing.
    """
    logger.info(
        f"--- Running Pipeline for Document ID: {input_document.get('id', 'N/A')} ---"
    )

    if not predictor:
        logger.error("Predictor is not initialized. Cannot run pipeline.")
        return None  # Or raise an exception

    # Extract attachments
    unpack_attachments(input_document)
    for candidate_doc in historical_documents:
        unpack_attachments(candidate_doc)

    # --- Record History (Crucial for Predictor State) ---
    try:
        id2doc = {
            doc["id"]: doc
            for doc in historical_documents
            if isinstance(doc, dict) and "id" in doc
        }
        # Add the input document itself in case it's needed for lookups (e.g., transitive)
        # Note: predictor.record_document handles duplicates gracefully by updating
        if "id" in input_document:
            id2doc[input_document["id"]] = input_document
        else:
            logger.warning("Input document is missing an 'id'.")

        predictor.clear_documents()
        recorded_count = 0
        for doc in historical_documents:
            predictor.record_document(doc)
            recorded_count += 1
        # Also record the input document itself for feature generation etc.
        if isinstance(input_document, dict):
            predictor.record_document(input_document)
            recorded_count += 1
        logger.info(f"Recorded {recorded_count} documents in predictor for this run.")
        # Re-populate id2document map AFTER recording, as record_document might modify/store them
        id2doc = predictor.id2document.copy()

    except Exception as e:
        logger.exception("Error during data recording for pipeline run.")
        # Generate a simple no-match report indicating the error
        error_report = generate_no_match_report(input_document)
        error_report["labels"].append("pipeline-error")
        error_report["deviations"] = [
            {
                "code": "pipeline-setup-error",
                "message": f"Failed to record documents: {e}",
                "severity": "high",
            }
        ]
        return error_report

    # --- STEP 1: Predict Document Pairing ---
    pairings = []
    try:
        # Use the provided historical_documents as candidates
        pairings = predictor.predict_pairings(
            input_document,
            historical_documents,
            use_reference_logic=True,
        )
        logger.info("Predicted Document Pairings (Historical Doc ID: Confidence):")
        if pairings:
            for pairing_id, pairing_conf in pairings:
                logger.info(f"  {pairing_id}: {pairing_conf:.4f}")
        else:
            logger.info("  No suitable document pairings predicted.")
    except Exception:
        logger.exception("Error occurred during document pairing prediction.")
        pairings = []

    final_report = None

    # --- Process Matches or Generate No-Match Report ---
    if pairings:
        # Assume top pairing is the best match for now
        matched_doc_id = pairings[0][0]
        match_confidence = pairings[0][1]  # Keep confidence for use in report
        logger.info(
            f"\n--- Processing Top Match: ID {matched_doc_id} (Confidence: {match_confidence:.4f}) ---"
        )

        if matched_doc_id not in id2doc:
            logger.error(
                f"FATAL: Matched document ID {matched_doc_id} not found in recorded documents map 'id2doc'. This should not happen."
            )
            # Generate a no-match report, maybe add specific error label/deviation
            final_report = generate_no_match_report(input_document)
            final_report["labels"].append("internal-error")
            final_report["deviations"] = [
                {
                    "code": "match-lookup-failed",
                    "message": f"Matched ID {matched_doc_id} not found.",
                    "severity": "high",
                }
            ]

        else:
            matched_doc = id2doc[matched_doc_id]
            doc1, doc2 = input_document, matched_doc

            # Ensure correct order if needed (e.g., always Invoice then PO) - reporter might handle this
            # For now, keep the order input_document, matched_doc

            logger.info("--- STEP 2a: Collecting Document Deviations ---")
            document_deviations = []
            try:
                document_deviations = collect_document_deviations(doc1, doc2)
                logger.info(
                    f"Collected {len(document_deviations)} document-level deviations."
                )
            except Exception as e:
                raise e

            logger.info("--- STEP 2b: Extracting Document Items ---")
            doc1_items, doc2_items = [], []
            try:
                doc1_items = get_document_items(doc1)
                doc2_items = get_document_items(doc2)
                logger.info(
                    f"Extracted {len(doc1_items)} items from doc1 (ID: {doc1.get('id')}), {len(doc2_items)} items from doc2 (ID: {doc2.get('id')})."
                )
            except Exception as e:
                raise e

            processed_item_pairs = []
            if not doc1_items or not doc2_items:
                logger.warning(
                    "One or both documents have no extractable items. Skipping item pairing and deviation steps."
                )
            else:
                try:
                    logger.info("--- STEP 3a: Pairing Items by Similarity ---")
                    # Ensure the item pairing function can handle the extracted format
                    matched_item_pairs_raw = pair_document_items(doc1_items, doc2_items)
                    logger.info(
                        f"Found {len(matched_item_pairs_raw)} initial item pairs based on similarity."
                    )

                    logger.info(
                        "--- STEP 3b: Collecting Deviations for Each Item Pair ---"
                    )
                    pair_count = 0
                    for raw_pair in matched_item_pairs_raw:
                        pair_count += 1
                        item1_data = raw_pair.get("item1")
                        item2_data = raw_pair.get("item2")

                        if not item1_data or not item2_data:
                            logger.warning(
                                f"Skipping deviation check for raw pair {pair_count} due to missing item data."
                            )
                            continue

                        # Get necessary info for collect_itempair_deviations
                        # It expects list of kinds and list of fields lists
                        doc_kinds = [
                            item1_data["document_kind"],
                            item2_data["document_kind"],
                        ]
                        # Access the 'raw_item' which should hold the original structure
                        item1_fields = item1_data.get("raw_item", {}).get("fields")
                        item2_fields = item2_data.get("raw_item", {}).get("fields")

                        item_deviations = []
                        # Handle cases where items might not have the 'fields' list directly
                        if item1_fields is None or item2_fields is None:
                            logger.warning(
                                f"Missing 'fields' list in raw_item for pair indices {item1_data.get('item_index')}/{item2_data.get('item_index')}. Cannot calculate deviations for this pair using standard method."
                                # Potential fallback: try extracting fields differently if needed
                            )
                        else:
                            try:
                                item_deviations = collect_itempair_deviations(
                                    doc_kinds,
                                    [item1_fields, item2_fields],
                                    raw_pair.get("similarities"),
                                )
                                logger.debug(
                                    f"  Pair {item1_data.get('item_index')}/{item2_data.get('item_index')} (Score: {raw_pair.get('score', 0):.3f}): Found {len(item_deviations)} deviations."
                                )
                            except Exception as e_dev:
                                logger.exception(
                                    f"Error collecting deviations for pair {item1_data.get('item_index')}/{item2_data.get('item_index')}"
                                )
                                # Add a deviation indicating this failure?
                                item_deviations.append(
                                    FieldDeviation(
                                        code="deviation-calc-failed",
                                        message=str(e_dev),
                                        severity=DeviationSeverity.HIGH,
                                    )
                                )

                        processed_item_pairs.append(
                            {
                                "item1": item1_data,
                                "item2": item2_data,
                                "score": raw_pair.get("score"),
                                "similarities": raw_pair.get(
                                    "similarities"
                                ),  # Keep for potential debugging/reporting
                                "deviations": item_deviations,
                            }
                        )
                    logger.info(
                        f"Finished collecting deviations for {len(processed_item_pairs)} item pairs."
                    )

                    for item in doc1_items:
                        if not item.get("matched"):
                            doc_kind = item.get("document_kind")
                            if doc_kind:
                                unmatched_deviation = create_item_unmatched_deviation(
                                    item, doc_kind
                                )
                                processed_item_pairs.append(
                                    {
                                        "item1": item,
                                        "item2": None,
                                        "score": None,
                                        "similarities": None,
                                        "deviations": [unmatched_deviation],
                                        "match_type": "unmatched",
                                    }
                                )

                    for item in doc2_items:
                        if not item.get("matched"):
                            doc_kind = item.get("document_kind")
                            if doc_kind:
                                unmatched_deviation = create_item_unmatched_deviation(
                                    item, doc_kind
                                )
                                processed_item_pairs.append(
                                    {
                                        "item1": None,
                                        "item2": item,
                                        "score": None,
                                        "similarities": None,
                                        "deviations": [unmatched_deviation],
                                        "match_type": "unmatched",
                                    }
                                )

                    unmatched_count = len(
                        [
                            p
                            for p in processed_item_pairs
                            if p.get("match_type") == "unmatched"
                        ]
                    )
                    if unmatched_count > 0:
                        logger.info(f"Found {unmatched_count} unmatched items.")

                except Exception as e_item_processing:
                    logger.exception(
                        "Error during item pairing or deviation collection."
                    )
                    # Add a deviation to the main report?
                    document_deviations.append(
                        FieldDeviation(
                            code="item-processing-failed",
                            message=str(e_item_processing),
                            severity=DeviationSeverity.HIGH,
                        )
                    )

            logger.info("--- STEP 4: Generating Match Report ---")
            try:
                final_report = generate_match_report(
                    doc1,
                    doc2,
                    processed_item_pairs,
                    document_deviations,
                    match_confidence=match_confidence,
                )
                logger.info(
                    f"Match report generated successfully (ID: {final_report.get('id')})."
                )
            except Exception as e:
                logger.exception("Error occurred during match report generation.")
                # Fallback: create a basic error report
                final_report = {
                    "error": "Failed to generate final match report",
                    "details": str(e),
                    "documents": [  # Try to include basic doc info
                        {"kind": doc1.get("kind", "unknown"), "id": doc1.get("id")},
                        {"kind": doc2.get("kind", "unknown"), "id": doc2.get("id")},
                    ],
                    "labels": ["match", "report-generation-error"],
                }

    else:  # No pairings predicted
        logger.info("--- STEP 4: Generating No-Match Report ---")
        try:
            final_report = generate_no_match_report(input_document)
            logger.info(
                f"No-match report generated successfully (ID: {final_report.get('id')})."
            )
        except Exception as e:
            logger.exception("Error occurred during no-match report generation.")
            # Fallback: basic error report
            final_report = {
                "error": "Failed to generate no-match report",
                "details": str(e),
                "documents": [  # Try to include basic doc info
                    {
                        "kind": input_document.get("kind", "unknown"),
                        "id": input_document.get("id"),
                    },
                ],
                "labels": ["no-match", "report-generation-error"],
            }

    logger.info(
        f"--- Pipeline Finished for Document ID: {input_document.get('id', 'N/A')} ---"
    )
    return final_report


# Helper for __main__ test
def get_sample_data() -> dict:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_data_root = os.path.join(script_dir, "..", "data", "converted-shared-data")
    data_root = os.environ.get("SAMPLE_DATA_ROOT", default_data_root)
    if not os.path.isdir(data_root):
        logger.warning(
            f"Sample data directory not found at '{data_root}'. Trying relative path 'data/converted-shared-data'"
        )
        data_root = "data/converted-shared-data"

    docs = {}
    file_paths = {
        "invoice1": "invoices/badger-logistics/91426726-62c5-4349-9f3d-cb11070e8177/final.json",
        "invoice2": "invoices/badger-logistics/7de2ded1-2794-411c-a669-2ebaac289f5c/final.json",
        "delivery434": "delivery-receipts/badger-logistics/00434/final.json",
        "delivery431": "delivery-receipts/badger-logistics/00431/final.json",
        "po434": "purchase-orders/badger-logistics/8e82a889-8bab-464b-9626-c0c80a6e3899/final.json",
    }

    logger.info(f"Loading sample data from: {os.path.abspath(data_root)}")
    successful_loads = 0
    for name, rel_path in file_paths.items():
        # Normalize path separators for cross-platform compatibility
        norm_rel_path = os.path.normpath(rel_path)
        full_path = os.path.join(data_root, norm_rel_path)
        try:
            with open(full_path, "r") as f:
                docs[name] = json.load(f)
            logger.info(
                f"  Loaded: {name} ({docs[name].get('kind', 'N/A')} ID: {docs[name].get('id', 'N/A')})"
            )
            successful_loads += 1
        except FileNotFoundError:
            logger.error(f"  File not found - {full_path}")
            docs[name] = None
        except json.JSONDecodeError:
            logger.error(f"  Could not decode JSON - {full_path}")
            docs[name] = None
        except Exception as e:
            logger.error(f"  Unexpected error loading {full_path}: {e}")
            docs[name] = None

    if successful_loads == 0:
        raise RuntimeError(
            f"Failed to load any sample data files from {os.path.abspath(data_root)}. Please check the path and data existence."
        )

    loaded_docs = {k: v for k, v in docs.items() if v is not None}
    if "invoice1" not in loaded_docs:
        raise ValueError(
            "Target document 'invoice1' (invoice1) failed to load. Cannot proceed."
        )

    target_doc = loaded_docs["invoice1"]
    sample_invoices = [d for k, d in loaded_docs.items() if k.startswith("invoice")]
    sample_delivery_receipts = [
        d for k, d in loaded_docs.items() if k.startswith("delivery")
    ]
    sample_purchase_orders = [d for k, d in loaded_docs.items() if k.startswith("po")]
    other_invoices = [inv for inv in sample_invoices if inv["id"] != target_doc["id"]]
    past_docs = sample_delivery_receipts + sample_purchase_orders + other_invoices

    logger.info(f"Target document: {target_doc.get('id', 'N/A')}")
    logger.info(
        f"Historical documents ({len(past_docs)}): {[d.get('id', 'N/A') for d in past_docs]}"
    )

    return dict(
        target_document=target_doc,
        invoices=other_invoices,
        delivery_receipts=sample_delivery_receipts,
        purchase_orders=sample_purchase_orders,
        past_documents=past_docs,
    )


if __name__ == "__main__":
    logger.info("--- Initializing SVM (__main__ Test) ---")
    predictor = None
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_model_path = os.path.join(
            script_dir, "..", "data", "models", "document-pairing-svm.pkl"
        )
        model_path = os.environ.get("DOCPAIR_MODEL_PATH", default_model_path)

        if not os.path.exists(model_path):
            alt_path1 = os.path.join(
                script_dir, "data", "models", "document-pairing-svm.pkl"
            )
            alt_path2 = "data/models/document-pairing-svm.pkl"
            if os.path.exists(alt_path1):
                model_path = alt_path1
            elif os.path.exists(alt_path2):
                model_path = alt_path2
            else:
                raise FileNotFoundError(
                    f"SVM model file not found. Checked: {os.path.abspath(model_path)}, {os.path.abspath(alt_path1)}, {os.path.abspath(alt_path2)}"
                )

        logger.info(f"Using SVM model from: {os.path.abspath(model_path)}")
        predictor = DocumentPairingPredictor(model_path, svc_threshold=0.15)
        logger.info("Predictor initialized successfully.")

    except FileNotFoundError as e:
        logger.error(f"Initialization failed: {e}")
        exit(1)
    except Exception:
        logger.exception(
            "An unexpected error occurred during predictor initialization."
        )
        exit(1)

    logger.info("--- Loading Sample Data (__main__ Test) ---")
    try:
        sample_data = get_sample_data()
        historical_documents: list[dict] = sample_data["past_documents"]
        input_document: dict = sample_data["target_document"]
    except Exception:
        logger.exception("Error loading sample data.")
        exit(1)

    logger.info("--- Running Pipeline via run_matching_pipeline (__main__ Test) ---")
    final_report = run_matching_pipeline(
        predictor,
        input_document,
        historical_documents,
    )

    logger.info("\n--- FINAL REPORT (Standalone Test) ---")
    if final_report:
        # from app import adapt_report_to_v3
        # final_report = adapt_report_to_v3(final_report)
        try:
            print(json.dumps(final_report, indent=2, default=str))
        except Exception as e:
            logger.error(f"Failed to serialize final report to JSON: {e}")
            print(
                f"Error: Could not display final report.\nReport data: {final_report}"
            )
    else:
        logger.error("No final report was generated by the pipeline.")

    logger.info("\nStandalone Pipeline Test finished.")
