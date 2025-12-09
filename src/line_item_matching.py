"""
Line Item Matching Heuristic for Invoice-Delivery-PO Three-Way Matching

This module implements a rule-based heuristic to determine if an Invoice and a
Delivery Receipt should be merged into a three-way match with a Purchase Order.

The heuristic works by checking if the Invoice and Delivery Receipt reference
the same PO line items (matched by line number, article number, or description).
"""

import logging
from typing import Dict, List, Optional, Set, Tuple

from document_utils import get_field
from wfields import get_item_article_number, get_item_description

logger = logging.getLogger(__name__)


def normalize_article_number(article_num: Optional[str]) -> Optional[str]:
    """
    Normalize article numbers for comparison by removing spaces, dashes,
    and leading zeros.

    Args:
        article_num: The article number to normalize

    Returns:
        Normalized article number or None if input is None/empty
    """
    if not article_num:
        return None
    normalized = str(article_num).replace("-", "").replace(" ", "").lstrip("0")
    return normalized if normalized else None


def get_po_line_reference(item: dict, doc_kind: str) -> Optional[str]:
    """
    Extract PO line reference from an item.

    For delivery receipts, this looks for purchaseOrderNumber.
    For invoices, this looks for purchaseOrderNumber or orderLineReference.
    For POs, this uses the lineNumber itself.

    Args:
        item: The item dictionary
        doc_kind: The document kind (invoice, delivery-receipt, purchase-order)

    Returns:
        PO line reference string or None
    """
    if doc_kind == "purchase-order":
        # For PO items, the line number IS the reference
        line_num = get_field(item, "lineNumber")
        return str(line_num) if line_num is not None else None

    elif doc_kind == "delivery-receipt":
        # Delivery receipts typically have purchaseOrderNumber per line
        po_num = get_field(item, "purchaseOrderNumber")
        line_ref = get_field(item, "purchaseOrderLineNumber")
        if po_num and line_ref:
            return f"{po_num}-{line_ref}"
        elif line_ref:
            return str(line_ref)
        return None

    elif doc_kind == "invoice":
        # Invoices may have order line references
        line_ref = get_field(item, "orderLineReference")
        po_num = get_field(item, "purchaseOrderNumber")
        if po_num and line_ref:
            return f"{po_num}-{line_ref}"
        elif line_ref:
            return str(line_ref)
        return None

    return None


def extract_line_item_features(item: dict, doc_kind: str) -> Dict[str, any]:
    """
    Extract matching features from a line item for comparison.

    Args:
        item: The item dictionary
        doc_kind: The document kind

    Returns:
        Dictionary with line_number, article_number, description, po_reference
    """
    line_number = get_field(item, "lineNumber")
    article_number = get_item_article_number(item)
    description = get_item_description(item)
    po_reference = get_po_line_reference(item, doc_kind)

    return {
        "line_number": str(line_number) if line_number is not None else None,
        "article_number": normalize_article_number(article_number),
        "description": description.lower() if description else None,
        "po_reference": po_reference,
        "raw_article_number": article_number,
    }


def calculate_line_item_similarity(
    features1: Dict[str, any], features2: Dict[str, any]
) -> float:
    """
    Calculate similarity score between two line items.

    Matching criteria (in order of priority):
    1. Exact PO line reference match (1.0)
    2. Exact article number match (0.9)
    3. Same line number + similar description (0.7)
    4. Similar description only (0.5)

    Args:
        features1: Features from first item
        features2: Features from second item

    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Priority 1: PO line reference match
    if (
        features1["po_reference"]
        and features2["po_reference"]
        and features1["po_reference"] == features2["po_reference"]
    ):
        return 1.0

    # Priority 2: Article number match
    if (
        features1["article_number"]
        and features2["article_number"]
        and features1["article_number"] == features2["article_number"]
    ):
        return 0.9

    # Priority 3: Line number + description similarity
    if (
        features1["line_number"]
        and features2["line_number"]
        and features1["line_number"] == features2["line_number"]
    ):
        if features1["description"] and features2["description"]:
            # Simple token overlap check
            tokens1 = set(features1["description"].split())
            tokens2 = set(features2["description"].split())
            if tokens1 and tokens2:
                overlap = len(tokens1 & tokens2) / max(len(tokens1), len(tokens2))
                if overlap > 0.5:
                    return 0.7
        return 0.6

    # Priority 4: Description similarity only
    if features1["description"] and features2["description"]:
        tokens1 = set(features1["description"].split())
        tokens2 = set(features2["description"].split())
        if tokens1 and tokens2:
            overlap = len(tokens1 & tokens2) / max(len(tokens1), len(tokens2))
            if overlap > 0.7:
                return 0.5

    return 0.0


def get_shared_po_line_items(
    invoice_items: List[dict],
    delivery_items: List[dict],
    po_items: List[dict],
    po_id: str,
) -> Tuple[Set[str], List[Tuple[dict, dict]]]:
    """
    Determine which PO line items are shared between invoice and delivery receipt.

    Args:
        invoice_items: List of invoice item dictionaries
        delivery_items: List of delivery receipt item dictionaries
        po_items: List of PO item dictionaries
        po_id: The PO document ID for reference

    Returns:
        Tuple of (shared_po_line_refs, matched_pairs)
        - shared_po_line_refs: Set of PO line references that appear in both
        - matched_pairs: List of (invoice_item, delivery_item) tuples that match
    """
    # Extract features for all items
    invoice_features = [
        extract_line_item_features(item, "invoice") for item in invoice_items
    ]
    delivery_features = [
        extract_line_item_features(item, "delivery-receipt") for item in delivery_items
    ]
    po_features = [
        extract_line_item_features(item, "purchase-order") for item in po_items
    ]

    # Find which PO lines each invoice/delivery item references
    invoice_to_po_lines: Dict[int, Set[str]] = {}
    delivery_to_po_lines: Dict[int, Set[str]] = {}

    # Match invoice items to PO lines
    for inv_idx, inv_feat in enumerate(invoice_features):
        matching_po_lines = set()
        for po_idx, po_feat in enumerate(po_features):
            similarity = calculate_line_item_similarity(inv_feat, po_feat)
            if similarity >= 0.6:  # Threshold for PO line match
                if po_feat["line_number"]:
                    matching_po_lines.add(po_feat["line_number"])
        invoice_to_po_lines[inv_idx] = matching_po_lines

    # Match delivery items to PO lines
    for del_idx, del_feat in enumerate(delivery_features):
        matching_po_lines = set()
        for po_idx, po_feat in enumerate(po_features):
            similarity = calculate_line_item_similarity(del_feat, po_feat)
            if similarity >= 0.6:  # Threshold for PO line match
                if po_feat["line_number"]:
                    matching_po_lines.add(po_feat["line_number"])
        delivery_to_po_lines[del_idx] = matching_po_lines

    # Find shared PO lines
    shared_po_lines = set()
    for inv_po_lines in invoice_to_po_lines.values():
        for del_po_lines in delivery_to_po_lines.values():
            shared_po_lines.update(inv_po_lines & del_po_lines)

    # Find direct invoice-delivery item matches
    matched_pairs = []
    for inv_idx, inv_feat in enumerate(invoice_features):
        for del_idx, del_feat in enumerate(delivery_features):
            similarity = calculate_line_item_similarity(inv_feat, del_feat)
            if similarity >= 0.6:  # Threshold for direct match
                matched_pairs.append((invoice_items[inv_idx], delivery_items[del_idx]))

    logger.info(
        f"PO {po_id}: Found {len(shared_po_lines)} shared line items, "
        f"{len(matched_pairs)} direct invoice-delivery matches"
    )

    return shared_po_lines, matched_pairs


def should_merge_into_three_way_match(
    invoice_doc: dict, delivery_doc: dict, po_doc: dict
) -> Tuple[bool, Dict[str, any]]:
    """
    Determine if invoice and delivery receipt should be merged with PO
    into a three-way match based on shared line items.

    Args:
        invoice_doc: Invoice document dictionary
        delivery_doc: Delivery receipt document dictionary
        po_doc: Purchase order document dictionary

    Returns:
        Tuple of (should_merge, details)
        - should_merge: Boolean indicating if they should merge
        - details: Dictionary with matching details and reasoning
    """
    invoice_items = invoice_doc.get("items", [])
    delivery_items = delivery_doc.get("items", [])
    po_items = po_doc.get("items", [])

    if not invoice_items or not delivery_items or not po_items:
        logger.warning(
            f"Cannot perform line item matching: missing items in one or more documents"
        )
        return False, {
            "reason": "missing_items",
            "invoice_items": len(invoice_items),
            "delivery_items": len(delivery_items),
            "po_items": len(po_items),
        }

    shared_po_lines, matched_pairs = get_shared_po_line_items(
        invoice_items, delivery_items, po_items, po_doc.get("id", "unknown")
    )

    # Decision logic: merge if there are shared PO line items
    should_merge = len(shared_po_lines) > 0

    details = {
        "shared_po_line_count": len(shared_po_lines),
        "shared_po_lines": sorted(list(shared_po_lines)),
        "matched_pair_count": len(matched_pairs),
        "invoice_item_count": len(invoice_items),
        "delivery_item_count": len(delivery_items),
        "po_item_count": len(po_items),
        "decision": "merge" if should_merge else "no_merge",
        "reason": "shared_line_items" if should_merge else "no_shared_line_items",
    }

    logger.info(
        f"Three-way match decision for Invoice {invoice_doc.get('id')}, "
        f"Delivery {delivery_doc.get('id')}, PO {po_doc.get('id')}: "
        f"{details['decision']} ({details['reason']})"
    )

    return should_merge, details


def group_documents_by_shared_lines(
    invoices: List[dict], deliveries: List[dict], po: dict
) -> List[Dict[str, any]]:
    """
    Group multiple invoices and deliveries that share PO line items.

    Example: If PO has lines [1, 2, 3]:
    - INV-001 covers lines [1, 2], DR-001 covers lines [1, 2] -> Group 1
    - INV-002 covers line [3], DR-002 covers line [3] -> Group 2

    Args:
        invoices: List of invoice documents
        deliveries: List of delivery receipt documents
        po: Purchase order document

    Returns:
        List of groups, each with {invoices: [...], deliveries: [...], po_lines: [...]}
    """
    po_items = po.get("items", [])
    po_features = [
        extract_line_item_features(item, "purchase-order") for item in po_items
    ]
    po_line_numbers = [
        feat["line_number"] for feat in po_features if feat["line_number"]
    ]

    # Build mapping of each document to the PO lines it covers
    invoice_coverage: Dict[str, Set[str]] = {}
    for invoice in invoices:
        inv_id = invoice.get("id")
        inv_items = invoice.get("items", [])
        inv_features = [
            extract_line_item_features(item, "invoice") for item in inv_items
        ]

        covered_lines = set()
        for inv_feat in inv_features:
            for po_feat in po_features:
                if calculate_line_item_similarity(inv_feat, po_feat) >= 0.6:
                    if po_feat["line_number"]:
                        covered_lines.add(po_feat["line_number"])
        invoice_coverage[inv_id] = covered_lines

    delivery_coverage: Dict[str, Set[str]] = {}
    for delivery in deliveries:
        del_id = delivery.get("id")
        del_items = delivery.get("items", [])
        del_features = [
            extract_line_item_features(item, "delivery-receipt") for item in del_items
        ]

        covered_lines = set()
        for del_feat in del_features:
            for po_feat in po_features:
                if calculate_line_item_similarity(del_feat, po_feat) >= 0.6:
                    if po_feat["line_number"]:
                        covered_lines.add(po_feat["line_number"])
        delivery_coverage[del_id] = covered_lines

    # Group invoices and deliveries by shared line coverage
    groups = []
    for inv_id, inv_lines in invoice_coverage.items():
        for del_id, del_lines in delivery_coverage.items():
            shared_lines = inv_lines & del_lines
            if shared_lines:
                # Check if this group already exists
                existing_group = None
                for group in groups:
                    if group["po_lines"] & shared_lines:
                        existing_group = group
                        break

                if existing_group:
                    # Merge into existing group
                    invoice_doc = next(inv for inv in invoices if inv.get("id") == inv_id)
                    delivery_doc = next(
                        deliv for deliv in deliveries if deliv.get("id") == del_id
                    )
                    if invoice_doc not in existing_group["invoices"]:
                        existing_group["invoices"].append(invoice_doc)
                    if delivery_doc not in existing_group["deliveries"]:
                        existing_group["deliveries"].append(delivery_doc)
                    existing_group["po_lines"].update(shared_lines)
                else:
                    # Create new group
                    invoice_doc = next(inv for inv in invoices if inv.get("id") == inv_id)
                    delivery_doc = next(
                        deliv for deliv in deliveries if deliv.get("id") == del_id
                    )
                    groups.append(
                        {
                            "invoices": [invoice_doc],
                            "deliveries": [delivery_doc],
                            "po": po,
                            "po_lines": shared_lines.copy(),
                        }
                    )

    logger.info(
        f"Grouped {len(invoices)} invoices and {len(deliveries)} deliveries "
        f"into {len(groups)} three-way match groups for PO {po.get('id')}"
    )

    return groups


if __name__ == "__main__":
    # Test the heuristic with sample data
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Sample PO with 3 lines
    sample_po = {
        "id": "PO-001",
        "kind": "purchase-order",
        "items": [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "WIDGET-A"},
                    {"name": "description", "value": "Widget A - Red"},
                ]
            },
            {
                "fields": [
                    {"name": "lineNumber", "value": "2"},
                    {"name": "inventory", "value": "WIDGET-B"},
                    {"name": "description", "value": "Widget B - Blue"},
                ]
            },
            {
                "fields": [
                    {"name": "lineNumber", "value": "3"},
                    {"name": "inventory", "value": "WIDGET-C"},
                    {"name": "description", "value": "Widget C - Green"},
                ]
            },
        ],
    }

    # Invoice covering lines 1 and 2
    sample_invoice1 = {
        "id": "INV-001",
        "kind": "invoice",
        "items": [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "WIDGET-A"},
                    {"name": "text", "value": "Widget A - Red"},
                ]
            },
            {
                "fields": [
                    {"name": "lineNumber", "value": "2"},
                    {"name": "inventory", "value": "WIDGET-B"},
                    {"name": "text", "value": "Widget B - Blue"},
                ]
            },
        ],
    }

    # Invoice covering line 3
    sample_invoice2 = {
        "id": "INV-002",
        "kind": "invoice",
        "items": [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "WIDGET-C"},
                    {"name": "text", "value": "Widget C - Green"},
                ]
            }
        ],
    }

    # Delivery covering lines 1 and 2
    sample_delivery1 = {
        "id": "DR-001",
        "kind": "delivery-receipt",
        "items": [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "WIDGET-A"},
                    {"name": "inventoryDescription", "value": "Widget A - Red"},
                ]
            },
            {
                "fields": [
                    {"name": "lineNumber", "value": "2"},
                    {"name": "inventory", "value": "WIDGET-B"},
                    {"name": "inventoryDescription", "value": "Widget B - Blue"},
                ]
            },
        ],
    }

    # Delivery covering line 3
    sample_delivery2 = {
        "id": "DR-002",
        "kind": "delivery-receipt",
        "items": [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "WIDGET-C"},
                    {"name": "inventoryDescription", "value": "Widget C - Green"},
                ]
            }
        ],
    }

    print("\n=== Test 1: Invoice 1 + Delivery 1 (should merge - lines 1,2) ===")
    should_merge, details = should_merge_into_three_way_match(
        sample_invoice1, sample_delivery1, sample_po
    )
    print(f"Result: {should_merge}")
    print(f"Details: {details}")

    print("\n=== Test 2: Invoice 2 + Delivery 2 (should merge - line 3) ===")
    should_merge, details = should_merge_into_three_way_match(
        sample_invoice2, sample_delivery2, sample_po
    )
    print(f"Result: {should_merge}")
    print(f"Details: {details}")

    print("\n=== Test 3: Invoice 1 + Delivery 2 (should NOT merge - no overlap) ===")
    should_merge, details = should_merge_into_three_way_match(
        sample_invoice1, sample_delivery2, sample_po
    )
    print(f"Result: {should_merge}")
    print(f"Details: {details}")

    print("\n=== Test 4: Group all documents ===")
    groups = group_documents_by_shared_lines(
        [sample_invoice1, sample_invoice2], [sample_delivery1, sample_delivery2], sample_po
    )
    print(f"Number of groups: {len(groups)}")
    for i, group in enumerate(groups):
        print(f"\nGroup {i + 1}:")
        print(
            f"  Invoices: {[inv.get('id') for inv in group['invoices']]}"
        )
        print(
            f"  Deliveries: {[deliv.get('id') for deliv in group['deliveries']]}"
        )
        print(f"  PO Lines: {sorted(group['po_lines'])}")
