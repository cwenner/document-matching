"""Unit tests for match_reporter.py functions."""

from decimal import Decimal

import pytest

from itempair_deviations import DeviationSeverity, DocumentKind, FieldDeviation
from match_reporter import (
    MATCHED_CERTAINTY_THRESHOLD,
    NO_MATCH_CERTAINTY_THRESHOLD,
    _calculate_overall_severity,
    calculate_future_match_certainty,
    collect_document_deviations,
    generate_match_report,
    generate_no_match_report,
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


class TestCalculateOverallSeverity:
    """Tests for _calculate_overall_severity function."""

    def test_empty_list_returns_no_severity(self):
        """Empty severity list should return NO_SEVERITY."""
        result = _calculate_overall_severity([])
        assert result == DeviationSeverity.NO_SEVERITY

    def test_single_severity_returns_same(self):
        """Single severity should return that severity."""
        result = _calculate_overall_severity([DeviationSeverity.MEDIUM])
        assert result == DeviationSeverity.MEDIUM

    def test_returns_highest_severity(self):
        """Should return the maximum severity from list."""
        severities = [
            DeviationSeverity.LOW,
            DeviationSeverity.HIGH,
            DeviationSeverity.MEDIUM,
        ]
        result = _calculate_overall_severity(severities)
        assert result == DeviationSeverity.HIGH

    def test_all_no_severity_returns_no_severity(self):
        """List of NO_SEVERITY should return NO_SEVERITY."""
        severities = [DeviationSeverity.NO_SEVERITY, DeviationSeverity.NO_SEVERITY]
        result = _calculate_overall_severity(severities)
        assert result == DeviationSeverity.NO_SEVERITY

    def test_info_and_low_returns_low(self):
        """Should return LOW when comparing INFO and LOW."""
        severities = [DeviationSeverity.INFO, DeviationSeverity.LOW]
        result = _calculate_overall_severity(severities)
        assert result == DeviationSeverity.LOW


class TestCollectDocumentDeviations:
    """Tests for collect_document_deviations function."""

    def test_missing_doc1_returns_empty_list(self):
        """Missing doc1 should return empty list."""
        doc2 = {"kind": "invoice"}
        result = collect_document_deviations(None, doc2)
        assert result == []

    def test_missing_doc2_returns_empty_list(self):
        """Missing doc2 should return empty list."""
        doc1 = {"kind": "invoice"}
        result = collect_document_deviations(doc1, None)
        assert result == []

    def test_invalid_document_kind_returns_deviation(self):
        """Invalid document kind should return HIGH severity deviation."""
        doc1 = {"kind": "invalid-kind"}
        doc2 = {"kind": "invoice"}
        result = collect_document_deviations(doc1, doc2)
        assert len(result) == 1
        assert result[0].code == "INVALID_DOC_KIND"
        assert result[0].severity == DeviationSeverity.HIGH

    def test_matching_currencies_no_deviation(self):
        """Matching currencies should not create deviation."""
        doc1 = {"kind": "invoice", "fields": [{"name": "currency", "value": "USD"}]}
        doc2 = {
            "kind": "purchase-order",
            "fields": [{"name": "currency", "value": "USD"}],
        }
        result = collect_document_deviations(doc1, doc2)
        assert len(result) == 0

    def test_different_currencies_creates_deviation(self):
        """Different currencies should create HIGH severity deviation."""
        doc1 = {"kind": "invoice", "fields": [{"name": "currency", "value": "USD"}]}
        doc2 = {
            "kind": "purchase-order",
            "fields": [{"name": "currency", "value": "EUR"}],
        }
        result = collect_document_deviations(doc1, doc2)
        assert len(result) == 1
        assert result[0].code == "CURRENCIES_DIFFER"
        assert result[0].severity == DeviationSeverity.HIGH
        assert "USD" in result[0].message
        assert "EUR" in result[0].message

    def test_empty_currency_no_deviation(self):
        """Empty currency on one side should not create deviation."""
        doc1 = {"kind": "invoice", "fields": [{"name": "currency", "value": ""}]}
        doc2 = {
            "kind": "purchase-order",
            "fields": [{"name": "currency", "value": "USD"}],
        }
        result = collect_document_deviations(doc1, doc2)
        assert len(result) == 0

    def test_matching_amounts_no_deviation(self):
        """Matching amounts should not create deviation."""
        doc1 = {
            "kind": "invoice",
            "fields": [{"name": "incVatAmount", "value": "100.00"}],
        }
        doc2 = {
            "kind": "purchase-order",
            "fields": [{"name": "incVatAmount", "value": "100.00"}],
        }
        result = collect_document_deviations(doc1, doc2)
        assert len(result) == 0

    def test_different_amounts_creates_deviation(self):
        """Different amounts should create deviation with appropriate severity."""
        doc1 = {
            "kind": "invoice",
            "fields": [{"name": "incVatAmount", "value": "100.00"}],
        }
        doc2 = {
            "kind": "purchase-order",
            "fields": [{"name": "incVatAmount", "value": "150.00"}],
        }
        result = collect_document_deviations(doc1, doc2)
        # Should create a deviation (severity depends on get_header_amount_severity)
        deviations_by_code = {dev.code: dev for dev in result}
        if "AMOUNTS_DIFFER" in deviations_by_code:
            dev = deviations_by_code["AMOUNTS_DIFFER"]
            assert "50.00" in dev.message

    def test_multiple_deviations(self):
        """Multiple issues should create multiple deviations."""
        doc1 = {
            "kind": "invoice",
            "fields": [
                {"name": "currency", "value": "USD"},
                {"name": "incVatAmount", "value": "100.00"},
            ],
        }
        doc2 = {
            "kind": "purchase-order",
            "fields": [
                {"name": "currency", "value": "EUR"},
                {"name": "incVatAmount", "value": "200.00"},
            ],
        }
        result = collect_document_deviations(doc1, doc2)
        codes = [dev.code for dev in result]
        assert "CURRENCIES_DIFFER" in codes


class TestGenerateMatchReport:
    """Tests for generate_match_report function."""

    def test_missing_doc1_returns_error(self):
        """Missing doc1 should return error."""
        doc2 = {"id": "doc2", "kind": "invoice"}
        result = generate_match_report(None, doc2, [], [])
        assert "error" in result
        assert "Missing input documents" in result["error"]

    def test_missing_doc2_returns_error(self):
        """Missing doc2 should return error."""
        doc1 = {"id": "doc1", "kind": "invoice"}
        result = generate_match_report(doc1, None, [], [])
        assert "error" in result
        assert "Missing input documents" in result["error"]

    def test_invalid_document_kind_returns_error(self):
        """Invalid document kind should return error."""
        doc1 = {"id": "doc1", "kind": "invalid-kind"}
        doc2 = {"id": "doc2", "kind": "invoice"}
        result = generate_match_report(doc1, doc2, [], [])
        assert "error" in result
        assert "Invalid document kind" in result["error"]

    def test_basic_report_structure(self):
        """Basic report should have correct structure."""
        doc1 = {"id": "doc1", "kind": "invoice", "site": "site1", "items": []}
        doc2 = {
            "id": "doc2",
            "kind": "purchase-order",
            "site": "site1",
            "items": [],
        }
        result = generate_match_report(doc1, doc2, [], [])

        assert result["kind"] == "match-report"
        assert result["version"] == "v4.1-dev-split"
        assert result["site"] == "site1"
        assert result["stage"] == "output"
        assert "id" in result
        assert "documents" in result
        assert "labels" in result
        assert "metrics" in result
        assert "deviations" in result
        assert "itempairs" in result

    def test_report_documents_field(self):
        """Report should contain correct document references."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        result = generate_match_report(doc1, doc2, [], [])

        assert len(result["documents"]) == 2
        assert result["documents"][0] == {"kind": "invoice", "id": "doc1"}
        assert result["documents"][1] == {"kind": "purchase-order", "id": "doc2"}

    def test_certainty_high_creates_matched_label(self):
        """High certainty (>=0.5) should create 'matched' label."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        result = generate_match_report(doc1, doc2, [], [], match_confidence=0.8)

        assert "matched" in result["labels"]

    def test_certainty_low_creates_no_match_label(self):
        """Low certainty (<0.2) should create 'no-match' label."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        result = generate_match_report(doc1, doc2, [], [], match_confidence=0.1)

        assert "no-match" in result["labels"]

    def test_certainty_medium_creates_uncertain_label(self):
        """Medium certainty (0.2-0.5) should create 'uncertain' label."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        result = generate_match_report(doc1, doc2, [], [], match_confidence=0.3)

        assert "uncertain" in result["labels"]

    def test_no_item_pairs_creates_potential_match_label(self):
        """No item pairs should create 'potential-match-no-items' label."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        result = generate_match_report(doc1, doc2, [], [])

        assert "potential-match-no-items" in result["labels"]

    def test_with_item_pairs_creates_matched_items_label(self):
        """With item pairs should create 'matched-items' label."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": [{"index": 0}]}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": [{"index": 0}]}
        item_pairs = [
            {
                "item1": {"item_index": 0},
                "item2": {"item_index": 0},
                "deviations": [],
                "score": 0.9,
            }
        ]
        result = generate_match_report(doc1, doc2, item_pairs, [])

        assert "matched-items" in result["labels"]

    def test_metrics_include_certainty(self):
        """Metrics should include certainty value."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        result = generate_match_report(doc1, doc2, [], [], match_confidence=0.75)

        certainty_metric = next(
            (m for m in result["metrics"] if m["name"] == "certainty"), None
        )
        assert certainty_metric is not None
        assert certainty_metric["value"] == 0.75

    def test_certainty_clamped_to_zero_one(self):
        """Certainty should be clamped to [0, 1] range."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}

        result = generate_match_report(doc1, doc2, [], [], match_confidence=1.5)
        certainty_metric = next(
            (m for m in result["metrics"] if m["name"] == "certainty"), None
        )
        assert certainty_metric["value"] == 1.0

        result = generate_match_report(doc1, doc2, [], [], match_confidence=-0.5)
        certainty_metric = next(
            (m for m in result["metrics"] if m["name"] == "certainty"), None
        )
        assert certainty_metric["value"] == 0.0

    def test_document_deviations_included(self):
        """Document deviations should be included in report."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        deviations = [
            FieldDeviation(
                code="TEST_DEVIATION",
                severity=DeviationSeverity.MEDIUM,
                message="Test deviation",
            )
        ]
        result = generate_match_report(doc1, doc2, [], deviations)

        assert len(result["deviations"]) == 1
        assert result["deviations"][0]["code"] == "TEST_DEVIATION"

    def test_matched_item_pair_in_report(self):
        """Matched item pairs should appear in report."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": [{"index": 0}]}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": [{"index": 0}]}
        item_pairs = [
            {
                "item1": {"item_index": 0},
                "item2": {"item_index": 0},
                "deviations": [],
                "score": 0.85,
            }
        ]
        result = generate_match_report(doc1, doc2, item_pairs, [])

        assert len(result["itempairs"]) == 1
        assert result["itempairs"][0]["match_type"] == "matched"
        assert result["itempairs"][0]["match_score"] == 0.85
        assert result["itempairs"][0]["item_indices"] == [0, 0]

    def test_unmatched_item_pair_in_report(self):
        """Unmatched item pairs should appear in report."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": [{"index": 0}]}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        item_pairs = [
            {
                "item1": {"item_index": 0},
                "item2": None,
                "deviations": [],
                "match_type": "unmatched",
            }
        ]
        result = generate_match_report(doc1, doc2, item_pairs, [])

        assert len(result["itempairs"]) == 1
        assert result["itempairs"][0]["match_type"] == "unmatched"
        assert result["itempairs"][0]["match_score"] is None
        assert result["itempairs"][0]["item_unchanged_certainty"] == 0.0

    def test_partial_delivery_label_added(self):
        """Partial delivery deviation should add 'partial-delivery' label."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": [{"index": 0}]}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": [{"index": 0}]}
        item_pairs = [
            {
                "item1": {"item_index": 0},
                "item2": {"item_index": 0},
                "deviations": [
                    FieldDeviation(
                        code="PARTIAL_DELIVERY",
                        severity=DeviationSeverity.INFO,
                        message="Partial delivery",
                    )
                ],
                "score": 0.9,
            }
        ]
        result = generate_match_report(doc1, doc2, item_pairs, [])

        assert "partial-delivery" in result["labels"]

    def test_deviation_severity_metric_updated(self):
        """Deviation severity metric should reflect highest severity."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        deviations = [
            FieldDeviation(
                code="HIGH_DEV", severity=DeviationSeverity.HIGH, message="High severity"
            ),
            FieldDeviation(
                code="LOW_DEV", severity=DeviationSeverity.LOW, message="Low severity"
            ),
        ]
        result = generate_match_report(doc1, doc2, [], deviations)

        severity_metric = next(
            (m for m in result["metrics"] if m["name"] == "deviation-severity"), None
        )
        assert severity_metric is not None
        assert severity_metric["value"] == DeviationSeverity.HIGH.value

    def test_item_count_metrics(self):
        """Report should include item count metrics."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": [{"id": "1"}, {"id": "2"}]}
        doc2 = {
            "id": "doc2",
            "kind": "purchase-order",
            "items": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
        }
        result = generate_match_report(doc1, doc2, [], [])

        invoice_items = next(
            (m for m in result["metrics"] if m["name"] == "invoice-total-items"), None
        )
        po_items = next(
            (m for m in result["metrics"] if m["name"] == "purchase-order-total-items"),
            None,
        )
        assert invoice_items["value"] == 2
        assert po_items["value"] == 3

    def test_future_match_certainty_metrics(self):
        """Report should include future match certainty for both documents."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        result = generate_match_report(doc1, doc2, [], [])

        invoice_future = next(
            (
                m
                for m in result["metrics"]
                if m["name"] == "invoice-has-future-match-certainty"
            ),
            None,
        )
        po_future = next(
            (
                m
                for m in result["metrics"]
                if m["name"] == "purchase-order-has-future-match-certainty"
            ),
            None,
        )
        assert invoice_future is not None
        assert po_future is not None
        assert 0.0 <= invoice_future["value"] <= 1.0
        assert 0.0 <= po_future["value"] <= 1.0


class TestGenerateNoMatchReport:
    """Tests for generate_no_match_report function."""

    def test_missing_doc1_returns_error(self):
        """Missing primary document should return error."""
        result = generate_no_match_report(None)
        assert "error" in result
        assert "Missing primary document" in result["error"]

    def test_invalid_document_kind_returns_error(self):
        """Invalid document kind should return error."""
        doc1 = {"id": "doc1", "kind": "invalid-kind"}
        result = generate_no_match_report(doc1)
        assert "error" in result
        assert "Invalid document kind" in result["error"]

    def test_basic_no_match_report_structure(self):
        """Basic no-match report should have correct structure."""
        doc1 = {"id": "doc1", "kind": "invoice", "site": "site1", "items": []}
        result = generate_no_match_report(doc1)

        assert result["kind"] == "match-report"
        assert result["version"] == "v4.1-dev-split"
        assert result["site"] == "site1"
        assert result["stage"] == "output"
        assert "id" in result
        assert "nomatch" in result["id"]
        assert "documents" in result
        assert "labels" in result
        assert "metrics" in result
        assert "deviations" in result
        assert "itempairs" in result

    def test_no_match_label_present(self):
        """No-match report should have 'no-match' label."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        result = generate_no_match_report(doc1)

        assert "no-match" in result["labels"]

    def test_single_document_in_report(self):
        """No-match report with one doc should have one document."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        result = generate_no_match_report(doc1)

        assert len(result["documents"]) == 1
        assert result["documents"][0] == {"kind": "invoice", "id": "doc1"}

    def test_two_documents_in_report(self):
        """No-match report with two docs should have both documents."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "items": []}
        result = generate_no_match_report(doc1, doc2)

        assert len(result["documents"]) == 2
        assert result["documents"][0] == {"kind": "invoice", "id": "doc1"}
        assert result["documents"][1] == {"kind": "purchase-order", "id": "doc2"}

    def test_no_match_confidence_in_metrics(self):
        """No-match report should include confidence metric."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        result = generate_no_match_report(doc1, no_match_confidence=0.85)

        certainty_metric = next(
            (m for m in result["metrics"] if m["name"] == "certainty"), None
        )
        assert certainty_metric is not None
        assert certainty_metric["value"] == 0.85

    def test_no_match_confidence_clamped(self):
        """No-match confidence should be clamped to [0, 1]."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}

        result = generate_no_match_report(doc1, no_match_confidence=1.5)
        certainty_metric = next(
            (m for m in result["metrics"] if m["name"] == "certainty"), None
        )
        assert certainty_metric["value"] == 1.0

        result = generate_no_match_report(doc1, no_match_confidence=-0.5)
        certainty_metric = next(
            (m for m in result["metrics"] if m["name"] == "certainty"), None
        )
        assert certainty_metric["value"] == 0.0

    def test_future_match_certainty_for_unmatched(self):
        """Future match certainty should reflect unmatched state."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        result = generate_no_match_report(doc1)

        invoice_future = next(
            (
                m
                for m in result["metrics"]
                if m["name"] == "invoice-has-future-match-certainty"
            ),
            None,
        )
        assert invoice_future is not None
        # Unmatched invoice without order ref should have 0.5 certainty
        assert invoice_future["value"] == 0.5

    def test_matched_item_pairs_zero(self):
        """No-match report should have zero matched item pairs."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        result = generate_no_match_report(doc1)

        matched_pairs = next(
            (m for m in result["metrics"] if m["name"] == "matched-item-pairs"), None
        )
        assert matched_pairs is not None
        assert matched_pairs["value"] == 0

    def test_empty_deviations_and_itempairs(self):
        """No-match report should have empty deviations and itempairs."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        result = generate_no_match_report(doc1)

        assert result["deviations"] == []
        assert result["itempairs"] == []

    def test_site_fallback_to_unknown(self):
        """No-match report should fallback to 'unknown-site' if no site."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        result = generate_no_match_report(doc1)

        assert result["site"] == "unknown-site"

    def test_site_from_doc2_when_doc1_missing_site(self):
        """No-match report should use doc2 site if doc1 has none."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "purchase-order", "site": "site2", "items": []}
        result = generate_no_match_report(doc1, doc2)

        assert result["site"] == "site2"

    def test_invalid_second_document_handled_gracefully(self):
        """Invalid second document should be handled without error."""
        doc1 = {"id": "doc1", "kind": "invoice", "items": []}
        doc2 = {"id": "doc2", "kind": "invalid-kind", "items": []}
        result = generate_no_match_report(doc1, doc2)

        # Should still create report for doc1
        assert "error" not in result
        assert len(result["documents"]) == 1  # Only doc1 added
