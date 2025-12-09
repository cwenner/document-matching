"""Unit tests for line_item_matching module"""

import pytest

from src.line_item_matching import (
    calculate_line_item_similarity,
    extract_line_item_features,
    get_shared_po_line_items,
    group_documents_by_shared_lines,
    normalize_article_number,
    should_merge_into_three_way_match,
)


class TestNormalizeArticleNumber:
    def test_removes_dashes_and_spaces(self):
        assert normalize_article_number("ABC-123 456") == "ABC123456"

    def test_removes_leading_zeros(self):
        assert normalize_article_number("00123") == "123"

    def test_handles_none(self):
        assert normalize_article_number(None) is None

    def test_handles_empty_string(self):
        assert normalize_article_number("") is None

    def test_handles_only_zeros(self):
        assert normalize_article_number("000") is None

    def test_preserves_alphanumeric(self):
        assert normalize_article_number("ABC123") == "ABC123"


class TestExtractLineItemFeatures:
    def test_extracts_po_item_features(self):
        item = {
            "fields": [
                {"name": "lineNumber", "value": "1"},
                {"name": "inventory", "value": "WIDGET-A"},
                {"name": "description", "value": "Red Widget"},
            ]
        }
        features = extract_line_item_features(item, "purchase-order")
        assert features["line_number"] == "1"
        assert features["article_number"] == "WIDGETA"
        assert features["description"] == "red widget"
        assert features["po_reference"] == "1"

    def test_extracts_invoice_item_features(self):
        item = {
            "fields": [
                {"name": "lineNumber", "value": "2"},
                {"name": "inventory", "value": "PART-123"},
                {"name": "text", "value": "Blue Part"},
            ]
        }
        features = extract_line_item_features(item, "invoice")
        assert features["line_number"] == "2"
        assert features["article_number"] == "PART123"
        assert features["description"] == "blue part"

    def test_extracts_delivery_item_features(self):
        item = {
            "fields": [
                {"name": "lineNumber", "value": "3"},
                {"name": "inventory", "value": "ITEM-456"},
                {"name": "inventoryDescription", "value": "Green Item"},
            ]
        }
        features = extract_line_item_features(item, "delivery-receipt")
        assert features["line_number"] == "3"
        assert features["article_number"] == "ITEM456"
        assert features["description"] == "green item"

    def test_handles_missing_fields(self):
        item = {"fields": []}
        features = extract_line_item_features(item, "purchase-order")
        assert features["line_number"] is None
        assert features["article_number"] is None
        assert features["description"] is None


class TestCalculateLineItemSimilarity:
    def test_exact_po_reference_match(self):
        features1 = {
            "po_reference": "PO123-1",
            "article_number": None,
            "line_number": None,
            "description": None,
        }
        features2 = {
            "po_reference": "PO123-1",
            "article_number": None,
            "line_number": None,
            "description": None,
        }
        assert calculate_line_item_similarity(features1, features2) == 1.0

    def test_exact_article_number_match(self):
        features1 = {
            "po_reference": None,
            "article_number": "WIDGET123",
            "line_number": None,
            "description": None,
        }
        features2 = {
            "po_reference": None,
            "article_number": "WIDGET123",
            "line_number": None,
            "description": None,
        }
        assert calculate_line_item_similarity(features1, features2) == 0.9

    def test_line_number_plus_description_match(self):
        features1 = {
            "po_reference": None,
            "article_number": None,
            "line_number": "1",
            "description": "red widget part",
        }
        features2 = {
            "po_reference": None,
            "article_number": None,
            "line_number": "1",
            "description": "red widget component",
        }
        score = calculate_line_item_similarity(features1, features2)
        assert score >= 0.6  # Should match on line number + some description overlap

    def test_no_match(self):
        features1 = {
            "po_reference": None,
            "article_number": "ABC",
            "line_number": "1",
            "description": "item a",
        }
        features2 = {
            "po_reference": None,
            "article_number": "XYZ",
            "line_number": "2",
            "description": "item b",
        }
        assert calculate_line_item_similarity(features1, features2) == 0.0


class TestGetSharedPOLineItems:
    def test_finds_shared_lines(self):
        po_items = [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "WIDGET-A"},
                ]
            },
            {
                "fields": [
                    {"name": "lineNumber", "value": "2"},
                    {"name": "inventory", "value": "WIDGET-B"},
                ]
            },
        ]

        invoice_items = [
            {"fields": [{"name": "inventory", "value": "WIDGET-A"}]},
        ]

        delivery_items = [
            {"fields": [{"name": "inventory", "value": "WIDGET-A"}]},
        ]

        shared_lines, matched_pairs = get_shared_po_line_items(
            invoice_items, delivery_items, po_items, "PO-001"
        )

        assert "1" in shared_lines
        assert "2" not in shared_lines
        assert len(matched_pairs) > 0

    def test_no_shared_lines(self):
        po_items = [
            {
                "fields": [
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "WIDGET-A"},
                ]
            },
            {
                "fields": [
                    {"name": "lineNumber", "value": "2"},
                    {"name": "inventory", "value": "WIDGET-B"},
                ]
            },
        ]

        invoice_items = [
            {"fields": [{"name": "inventory", "value": "WIDGET-A"}]},
        ]

        delivery_items = [
            {"fields": [{"name": "inventory", "value": "WIDGET-B"}]},
        ]

        shared_lines, matched_pairs = get_shared_po_line_items(
            invoice_items, delivery_items, po_items, "PO-001"
        )

        assert len(shared_lines) == 0


class TestShouldMergeIntoThreeWayMatch:
    def test_merge_when_shared_lines(self):
        po = {
            "id": "PO-001",
            "items": [
                {
                    "fields": [
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "WIDGET-A"},
                    ]
                }
            ],
        }

        invoice = {
            "id": "INV-001",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-A"}]}],
        }

        delivery = {
            "id": "DR-001",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-A"}]}],
        }

        should_merge, details = should_merge_into_three_way_match(invoice, delivery, po)

        assert should_merge is True
        assert details["decision"] == "merge"
        assert details["shared_po_line_count"] > 0

    def test_no_merge_when_no_shared_lines(self):
        po = {
            "id": "PO-001",
            "items": [
                {
                    "fields": [
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "WIDGET-A"},
                    ]
                },
                {
                    "fields": [
                        {"name": "lineNumber", "value": "2"},
                        {"name": "inventory", "value": "WIDGET-B"},
                    ]
                },
            ],
        }

        invoice = {
            "id": "INV-001",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-A"}]}],
        }

        delivery = {
            "id": "DR-001",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-B"}]}],
        }

        should_merge, details = should_merge_into_three_way_match(invoice, delivery, po)

        assert should_merge is False
        assert details["decision"] == "no_merge"
        assert details["shared_po_line_count"] == 0

    def test_handles_missing_items(self):
        po = {"id": "PO-001", "items": []}
        invoice = {"id": "INV-001", "items": []}
        delivery = {"id": "DR-001", "items": []}

        should_merge, details = should_merge_into_three_way_match(invoice, delivery, po)

        assert should_merge is False
        assert details["reason"] == "missing_items"


class TestGroupDocumentsBySharedLines:
    def test_groups_by_shared_lines(self):
        po = {
            "id": "PO-001",
            "items": [
                {
                    "fields": [
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "WIDGET-A"},
                    ]
                },
                {
                    "fields": [
                        {"name": "lineNumber", "value": "2"},
                        {"name": "inventory", "value": "WIDGET-B"},
                    ]
                },
            ],
        }

        invoice1 = {
            "id": "INV-001",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-A"}]}],
        }

        invoice2 = {
            "id": "INV-002",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-B"}]}],
        }

        delivery1 = {
            "id": "DR-001",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-A"}]}],
        }

        delivery2 = {
            "id": "DR-002",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-B"}]}],
        }

        groups = group_documents_by_shared_lines(
            [invoice1, invoice2], [delivery1, delivery2], po
        )

        # Should create 2 groups: one for line 1, one for line 2
        assert len(groups) == 2

        # Verify each group has the correct documents
        group_invoice_ids = [
            {inv.get("id") for inv in group["invoices"]} for group in groups
        ]
        group_delivery_ids = [
            {deliv.get("id") for deliv in group["deliveries"]} for group in groups
        ]

        assert {"INV-001"} in group_invoice_ids
        assert {"INV-002"} in group_invoice_ids
        assert {"DR-001"} in group_delivery_ids
        assert {"DR-002"} in group_delivery_ids

    def test_single_group_for_overlapping_lines(self):
        po = {
            "id": "PO-001",
            "items": [
                {
                    "fields": [
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "WIDGET-A"},
                    ]
                }
            ],
        }

        invoice1 = {
            "id": "INV-001",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-A"}]}],
        }

        delivery1 = {
            "id": "DR-001",
            "items": [{"fields": [{"name": "inventory", "value": "WIDGET-A"}]}],
        }

        groups = group_documents_by_shared_lines([invoice1], [delivery1], po)

        # Should create 1 group with both documents
        assert len(groups) == 1
        assert len(groups[0]["invoices"]) == 1
        assert len(groups[0]["deliveries"]) == 1
        assert groups[0]["invoices"][0]["id"] == "INV-001"
        assert groups[0]["deliveries"][0]["id"] == "DR-001"
