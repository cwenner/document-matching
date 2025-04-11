# match_pipeline.py
# This file already has an if __name__ == "__main__": block
# that runs the full pipeline with sample data.

import json
import os
import logging

from docpairing import DocumentPairingPredictor

from document_utils import get_document_items
from itempairing import pair_document_items
from itempair_deviations import collect_itempair_deviations
from match_reporter import (
    generate_match_report,
    generate_no_match_report,
    collect_document_deviations,
)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_sample_data():
    # Using a relative path assuming 'data' is in the parent or current directory structure
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_data_root = os.path.join(script_dir, "..", "data", "converted-shared-data")
    data_root = os.environ.get("SAMPLE_DATA_ROOT", default_data_root)
    if not os.path.isdir(data_root):
        logger.warning(
            f"Sample data directory not found at '{data_root}'. Trying relative path 'data/converted-shared-data'"
        )
        data_root = "data/converted-shared-data"  # Fallback

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
    logger.info("--- Initializing Predictor ---")
    predictor = None
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_model_path = os.path.join(
            script_dir, "..", "data", "models", "document-pairing-svm.pkl"
        )
        model_path = os.environ.get("DOCPAIR_MODEL_PATH", default_model_path)

        if not os.path.exists(model_path):
            fallback_model_path = "data/models/document-pairing-svm.pkl"
            if os.path.exists(fallback_model_path):
                model_path = fallback_model_path
            else:
                raise FileNotFoundError(
                    f"Predictor model file not found. Checked: {os.path.abspath(model_path)} and {os.path.abspath(fallback_model_path)}"
                )

        logger.info(f"Using predictor model from: {os.path.abspath(model_path)}")
        predictor = DocumentPairingPredictor(
            model_path,
            svc_threshold=0.05,
        )
        logger.info("Predictor initialized successfully.")
    except FileNotFoundError as e:
        logger.error(f"Initialization failed: {e}")
        exit(1)
    except Exception as e:
        logger.exception(
            "An unexpected error occurred during predictor initialization."
        )
        exit(1)

    logger.info("--- Loading Data and Recording History ---")
    try:
        sample_data = get_sample_data()
        historical_documents = sample_data["past_documents"]
        input_document = sample_data["target_document"]
        id2doc = {
            doc["id"]: doc
            for doc in historical_documents
            if isinstance(doc, dict) and "id" in doc
        }
        id2doc[input_document["id"]] = input_document

        predictor.clear_documents()
        recorded_count = 0
        for doc in historical_documents:
            if isinstance(doc, dict):
                predictor.record_document(doc)
                recorded_count += 1
        logger.info(f"Recorded {recorded_count} historical documents in predictor.")
    except Exception as e:
        logger.exception("Error during data loading or recording history.")
        exit(1)

    logger.info("--- STEP 1: Predict Document Pairing ---")
    pairings = []
    try:
        pairings = predictor.predict_pairings(
            input_document, historical_documents, use_reference_logic=True
        )
        logger.info("Predicted Document Pairings (Historical Doc ID: Confidence):")
        if pairings:
            for pairing_id, pairing_conf in pairings:
                logger.info(f"  {pairing_id}: {pairing_conf:.4f}")
        else:
            logger.info("  No suitable document pairings predicted.")
    except Exception as e:
        logger.exception("Error occurred during document pairing prediction.")
        pairings = []

    final_report = None

    if pairings:
        matched_doc_id = pairings[0][0]
        logger.info(f"\n--- Processing Top Match: ID {matched_doc_id} ---")

        if matched_doc_id not in id2doc:
            logger.error(
                f"FATAL: Matched document ID {matched_doc_id} not found in loaded historical data map 'id2doc'. This should not happen."
            )
            final_report = generate_no_match_report(input_document)
        else:
            matched_doc = id2doc[matched_doc_id]
            doc1, doc2 = input_document, matched_doc

            logger.info("--- STEP 2a: Collecting Document Deviations ---")
            document_deviations = collect_document_deviations(doc1, doc2)
            logger.info(
                f"Collected {len(document_deviations)} document-level deviations."
            )

            logger.info("--- STEP 2b: Extracting Document Items ---")
            doc1_items = get_document_items(doc1)
            doc2_items = get_document_items(doc2)
            logger.info(
                f"Extracted {len(doc1_items)} items from doc1 (ID: {doc1.get('id')}), {len(doc2_items)} items from doc2 (ID: {doc2.get('id')})."
            )

            processed_item_pairs = []
            if not doc1_items or not doc2_items:
                logger.warning(
                    "One or both documents have no extractable items. Skipping item pairing and deviation steps."
                )
            else:
                logger.info("--- STEP 3a: Pairing Items by Similarity ---")
                matched_item_pairs_raw = pair_document_items(doc1_items, doc2_items)
                logger.info(
                    f"Found {len(matched_item_pairs_raw)} initial item pairs based on similarity."
                )

                logger.info("--- STEP 3b: Collecting Deviations for Each Item Pair ---")
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

                    doc_kinds = [
                        item1_data["document_kind"],
                        item2_data["document_kind"],
                    ]

                    item1_fields = item1_data.get("raw_item", {}).get("fields")
                    item2_fields = item2_data.get("raw_item", {}).get("fields")

                    item_deviations = []
                    if item1_fields is None or item2_fields is None:
                        # Fallback or log warning if 'fields' structure isn't present
                        logger.warning(
                            f"Missing 'fields' list in raw_item for pair indices {item1_data.get('item_index')}/{item2_data.get('item_index')}. Cannot calculate deviations for this pair using standard method."
                        )
                        # Alternative: Could try to assemble fields from item_data if needed, but stick to original logic for now.
                    else:
                        try:
                            item_deviations = collect_itempair_deviations(
                                doc_kinds, [item1_fields, item2_fields]
                            )
                            logger.debug(
                                f"  Pair {item1_data.get('item_index')}/{item2_data.get('item_index')} (Score: {raw_pair.get('score', 0):.3f}): Found {len(item_deviations)} deviations."
                            )
                        except Exception as e:
                            logger.exception(
                                f"Error collecting deviations for pair {item1_data.get('item_index')}/{item2_data.get('item_index')}"
                            )

                    processed_item_pairs.append(
                        {
                            "item1": item1_data,
                            "item2": item2_data,
                            "score": raw_pair.get("score"),
                            "similarities": raw_pair.get("similarities"),
                            "deviations": item_deviations,
                        }
                    )
                logger.info(
                    f"Finished collecting deviations for {len(processed_item_pairs)} item pairs."
                )

            logger.info("--- STEP 4: Generating Match Report ---")
            try:
                final_report = generate_match_report(
                    doc1, doc2, processed_item_pairs, document_deviations
                )
                logger.info(
                    f"Match report generated successfully (ID: {final_report.get('id')})."
                )
            except Exception as e:
                logger.exception("Error occurred during match report generation.")
                final_report = {
                    "error": "Failed to generate final match report",
                    "details": str(e),
                }

    else:
        logger.info("--- STEP 4: Generating No-Match Report ---")
        try:
            final_report = generate_no_match_report(input_document)
            logger.info(
                f"No-match report generated successfully (ID: {final_report.get('id')})."
            )
        except Exception as e:
            logger.exception("Error occurred during no-match report generation.")
            final_report = {
                "error": "Failed to generate no-match report",
                "details": str(e),
            }

    logger.info("\n--- FINAL REPORT ---")
    if final_report:
        try:
            print(json.dumps(final_report, indent=2, default=str))
        except Exception as e:
            logger.error(f"Failed to serialize final report to JSON: {e}")
            print(
                f"Error: Could not display final report.\nReport data: {final_report}"
            )
    else:
        logger.error("No final report was generated.")

    logger.info("\nPipeline finished.")
