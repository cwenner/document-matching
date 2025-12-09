import logging
from math import isclose

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


# @TODO we should initialize this in a class rather than at import
try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    logger.exception("Failed to initialize SentenceTransformer model.")
    model = None


def _calculate_description_similarity(desc1, desc2):
    """Calculate semantic similarity between two item descriptions.

    Uses SentenceTransformer embeddings to compute similarity score.

    Args:
        desc1: First description string
        desc2: Second description string

    Returns:
        float: Similarity score between 0 and 1, or None if model unavailable
               Returns 1.0 if both descriptions are empty
               Returns 0.0 if only one description is empty
    """
    if not model:
        logger.warning(
            "SentenceTransformer model not available. Cannot calculate description similarity."
        )
        return None
    if desc1 is None or desc2 is None:
        return None
    if not desc1 and not desc2:
        return 1.0
    if not desc1 or not desc2:
        return 0.0
    try:
        embeddings = model.encode([str(desc1), str(desc2)])
        similarity = np.dot(embeddings[0], embeddings[1])
        return float(similarity) if not np.isnan(similarity) else 0.0
    except Exception as e:
        logger.error(
            f"Error calculating description similarity for '{desc1}' vs '{desc2}': {e}",
            exc_info=False,
        )
        return 0.0


def _calculate_item_id_similarity(id1, id2):
    """Calculate similarity between two item IDs/article numbers.

    Uses SentenceTransformer embeddings for fuzzy matching.
    Returns 1.0 for exact matches.

    Args:
        id1: First item ID string
        id2: Second item ID string

    Returns:
        float: Similarity score between 0 and 1, or None if model unavailable
               Returns 1.0 if IDs are identical or both are empty
               Returns 0.0 if only one ID is empty
    """
    if not model:
        logger.warning(
            "SentenceTransformer model not available. Cannot calculate item ID similarity."
        )
        return None
    if id1 is None or id2 is None:
        return None
    if not id1 and not id2:
        return 1.0
    if not id1 or not id2:
        return 0.0
    s_id1, s_id2 = str(id1), str(id2)
    if s_id1 == s_id2:
        return 1.0
    try:
        embeddings = model.encode([s_id1, s_id2])
        similarity = np.dot(embeddings[0], embeddings[1])
        return float(similarity) if not np.isnan(similarity) else 0.0
    except Exception as e:
        logger.error(
            f"Error calculating item ID similarity for '{id1}' vs '{id2}': {e}",
            exc_info=False,
        )
        return None


def _calculate_unit_price_similarity(up1, up2):
    """Calculate similarity between two unit prices.

    Uses ratio of smaller to larger price for similarity score.
    Returns 1.0 if prices are nearly identical (within 0.00001 relative tolerance).
    Returns 0.0 if prices have opposite signs or cannot be converted.

    Args:
        up1: First unit price (numeric value or string)
        up2: Second unit price (numeric value or string)

    Returns:
        float: Similarity score between 0 and 1, or None if either price is None
               Returns 0.0 if prices cannot be converted to float
    """
    if up1 is None or up2 is None:
        return None
    try:
        f_up1 = float(up1)
        f_up2 = float(up2)
    except (ValueError, TypeError):
        logger.debug(
            f"Could not convert unit prices '{up1}', '{up2}' to float for similarity."
        )
        return 0.0

    if isclose(f_up1, f_up2, rel_tol=1e-5):
        return 1.0
    abs_up1, abs_up2 = abs(f_up1), abs(f_up2)
    if (f_up1 * f_up2) >= 0 and (abs_up1 + abs_up2) > 0:
        return min(abs_up1, abs_up2) / max(abs_up1, abs_up2)
    return 0.0


def _calculate_match_score(item_id_sim, desc_sim, price_sim):
    """Calculate overall match score from individual similarity metrics.

    Computes the average of available similarity scores and determines
    if items are a match based on threshold of 0.8.

    Args:
        item_id_sim: Item ID similarity score (or None)
        desc_sim: Description similarity score (or None)
        price_sim: Unit price similarity score (or None)

    Returns:
        tuple: (match_score, is_match) where match_score is float between 0-1
               and is_match is bool indicating if score >= 0.8
    """
    actual_values = [x for x in [item_id_sim, desc_sim, price_sim] if x is not None]
    match_score = sum(actual_values) / len(actual_values)
    is_match = match_score >= 0.8
    return match_score, is_match

    # @TODO Optimize this against data
    # is_match = (
    #     (item_id_sim >= 0.99)
    #     or (item_id_sim > 0.8 and isclose(price_sim, 1.0) and desc_sim > 0.4)
    #     or (desc_sim > 0.95 and isclose(price_sim, 1.0) and item_id_sim < 0.5)
    # )

    # w_item_id, w_price, w_desc = 10, 10, 1
    # max_score = w_item_id + w_price + w_desc
    # score = (w_item_id * item_id_sim) + (w_price * price_sim) + (w_desc * desc_sim)
    # normalized_score = score / max_score if max_score > 0 else 0.0
    # return normalized_score, is_match


def find_best_item_match(
    source_item_data: dict, target_items_data: list[dict]
) -> dict | None:
    """Find the best matching item from a list of target items.

    Compares source item against all unmatched target items using
    item ID, description, and unit price similarities. Returns the
    highest-scoring match that exceeds the match threshold.

    Args:
        source_item_data: Source item dictionary with fields like item-id,
                         description, unit-price, etc.
        target_items_data: List of target item dictionaries to search

    Returns:
        dict: Dictionary with keys 'target_item', 'score', 'is_match', and
              'similarities', or None if no match found or model unavailable
    """
    if not target_items_data or not model:
        return None

    # source_desc = source_item_data.get("description", "")  # Not used directly, included in source_descs
    source_item_id = source_item_data.get("item-id", "")
    source_price = source_item_data.get(
        "unit-price-adjusted", source_item_data.get("unit-price")
    )

    potential_matches = []
    for target_item in target_items_data:
        if target_item.get("matched"):
            continue

        target_descs = [
            target_item.get("description", ""),
            target_item.get("text", ""),
            target_item.get("inventory", ""),
        ]
        source_descs = [
            source_item_data.get("description", ""),
            source_item_data.get("text", ""),
            source_item_data.get("inventory", ""),
        ]
        target_descs = [x for x in target_descs if x]
        source_descs = [x for x in source_descs if x]
        target_item_id = target_item.get("item-id", "")
        target_price = target_item.get("unit-price")

        item_id_sim = _calculate_item_id_similarity(source_item_id, target_item_id)
        price_sim = _calculate_unit_price_similarity(source_price, target_price)
        desc_sims = [
            _calculate_description_similarity(source_desc, target_desc)
            for source_desc in source_descs
            for target_desc in target_descs
        ]
        desc_sim = max([0.0] + [x for x in desc_sims if x is not None])

        score, is_potential_match = _calculate_match_score(
            item_id_sim, desc_sim, price_sim
        )

        if is_potential_match:
            potential_matches.append(
                {
                    "target_item": target_item,
                    "score": score,
                    "is_match": True,
                    "similarities": {
                        "item_id": item_id_sim,
                        "description": desc_sim,
                        "unit_price": price_sim,
                    },
                }
            )

    return (
        max(potential_matches, key=lambda x: x["score"]) if potential_matches else None
    )


def pair_document_items(
    doc1_items_data: list[dict], doc2_items_data: list[dict]
) -> list[dict]:
    """Match line items between two documents.

    Performs one-to-one matching between items from two documents.
    Each item from doc2 is matched with the best available item from doc1.
    Items are marked as 'matched' to prevent duplicate pairings.

    Args:
        doc1_items_data: List of item dictionaries from first document
        doc2_items_data: List of item dictionaries from second document

    Returns:
        list: List of matched pairs, each containing:
              - item1: Matched item from doc1_items_data
              - item2: Matched item from doc2_items_data
              - score: Overall match score
              - similarities: Dict of individual similarity scores
              Returns empty list if model unavailable
    """
    if not model:
        logger.error(
            "SentenceTransformer model not available. Cannot perform item pairing."
        )
        return []

    for item in doc1_items_data:
        item["matched"] = False
    for item in doc2_items_data:
        item["matched"] = False

    matched_item_pairs = []
    available_doc1_items = [item for item in doc1_items_data if not item.get("matched")]

    for doc2_item in doc2_items_data:
        if doc2_item.get("matched"):
            continue

        best_match_info = find_best_item_match(doc2_item, available_doc1_items)

        if best_match_info:
            doc1_matched_item = best_match_info["target_item"]
            doc1_matched_item["matched"] = True
            doc2_item["matched"] = True
            try:
                available_doc1_items.remove(doc1_matched_item)
            except ValueError:
                logger.warning(
                    f"Item index {doc1_matched_item.get('item_index')} scheduled for removal not found in available pool."
                )

            matched_item_pairs.append(
                {
                    "item1": doc1_matched_item,
                    "item2": doc2_item,
                    "score": best_match_info["score"],
                    "similarities": best_match_info["similarities"],
                }
            )

    logger.info(f"Item pairing process identified {len(matched_item_pairs)} pairs.")
    return matched_item_pairs
