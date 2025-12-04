"""Unit tests for match_reporter.py functions."""

import pytest

from itempair_deviations import DocumentKind
from match_reporter import (
    MATCHED_CERTAINTY_THRESHOLD,
    NO_MATCH_CERTAINTY_THRESHOLD,
    calculate_future_match_certainty,
)


class TestCalculateFutureMatchCertainty:
    """Tests for calculate_future_match_certainty function."""

    # Invoice tests
    def test_invoice_matched_returns_low_certainty(self):
        """Matched invoice has low probability of getting more matches."""
        doc = {"kind": "invoice"}
        result = calculate_future_match_certainty(
            doc, DocumentKind.INVOICE, is_matched=True
        )
        assert result == 0.1

    def test_invoice_unmatched_with_order_ref_returns_high_certainty(self):
        """Unmatched invoice with order reference likely to find PO."""
        doc = {
            "kind": "invoice",
            "fields": [{"name": "orderReference", "value": "PO-123"}],
        }
        result = calculate_future_match_certainty(
            doc, DocumentKind.INVOICE, is_matched=False
        )
        assert result == 0.85

    def test_invoice_unmatched_without_order_ref_returns_medium_certainty(self):
        """Unmatched invoice without order reference is uncertain."""
        doc = {"kind": "invoice"}
        result = calculate_future_match_certainty(
            doc, DocumentKind.INVOICE, is_matched=False
        )
        assert result == 0.5

    # Purchase order tests
    def test_purchase_order_matched_returns_medium_certainty(self):
        """Matched PO may still get delivery receipt."""
        doc = {"kind": "purchase-order"}
        result = calculate_future_match_certainty(
            doc, DocumentKind.PURCHASE_ORDER, is_matched=True
        )
        assert result == 0.3

    def test_purchase_order_unmatched_returns_high_certainty(self):
        """Unmatched PO likely to get invoice."""
        doc = {"kind": "purchase-order"}
        result = calculate_future_match_certainty(
            doc, DocumentKind.PURCHASE_ORDER, is_matched=False
        )
        assert result == 0.7

    # Delivery receipt tests
    def test_delivery_receipt_matched_returns_low_certainty(self):
        """Matched delivery receipt is usually terminal."""
        doc = {"kind": "delivery-receipt"}
        result = calculate_future_match_certainty(
            doc, DocumentKind.DELIVERY_RECEIPT, is_matched=True
        )
        assert result == 0.1

    def test_delivery_receipt_unmatched_returns_medium_certainty(self):
        """Unmatched delivery receipt may get PO match."""
        doc = {"kind": "delivery-receipt"}
        result = calculate_future_match_certainty(
            doc, DocumentKind.DELIVERY_RECEIPT, is_matched=False
        )
        assert result == 0.6

    # Range validation
    def test_all_return_values_in_valid_range(self):
        """All return values should be in [0.0, 1.0] range."""
        doc_types = [
            (DocumentKind.INVOICE, {"kind": "invoice"}),
            (
                DocumentKind.INVOICE,
                {
                    "kind": "invoice",
                    "fields": [{"name": "orderReference", "value": "X"}],
                },
            ),
            (DocumentKind.PURCHASE_ORDER, {"kind": "purchase-order"}),
            (DocumentKind.DELIVERY_RECEIPT, {"kind": "delivery-receipt"}),
        ]

        for kind, doc in doc_types:
            for is_matched in [True, False]:
                result = calculate_future_match_certainty(doc, kind, is_matched)
                assert (
                    0.0 <= result <= 1.0
                ), f"Failed for {kind}, is_matched={is_matched}"


class TestCertaintyThresholds:
    """Tests for certainty threshold constants."""

    def test_matched_threshold_is_half(self):
        """MATCHED_CERTAINTY_THRESHOLD should be 0.5."""
        assert MATCHED_CERTAINTY_THRESHOLD == 0.5

    def test_no_match_threshold_is_point_two(self):
        """NO_MATCH_CERTAINTY_THRESHOLD should be 0.2."""
        assert NO_MATCH_CERTAINTY_THRESHOLD == 0.2

    def test_thresholds_are_ordered(self):
        """No-match threshold should be less than matched threshold."""
        assert NO_MATCH_CERTAINTY_THRESHOLD < MATCHED_CERTAINTY_THRESHOLD
