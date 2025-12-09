"""
Unit tests for itempair_deviations module.

Tests cover:
- _calculate_diff_metrics() - absolute and relative difference calculation
- get_header_amount_severity() - header-level total amount thresholds
- get_line_amount_severity() - line-level item amount thresholds
- get_unit_price_severity() - unit price difference thresholds
- get_quantity_severity() - quantity mismatch thresholds
- get_unmatched_item_severity() - unmatched item severity based on amount
- getkv_value() - key-value extraction from field lists
- check_partial_delivery() - partial delivery detection
- check_quantity_deviation() - quantity mismatch (over-delivery) detection
- check_article_numbers_differ() - article number comparison
- check_itempair_comparison() - generic field comparison logic
- collect_itempair_deviations() - main deviation collection function
"""

from decimal import Decimal

import pytest

from itempair_deviations import (
    DeviationSeverity,
    DocumentKind,
    FieldComparison,
    _calculate_diff_metrics,
    check_article_numbers_differ,
    check_itempair_comparison,
    check_partial_delivery,
    check_quantity_deviation,
    collect_itempair_deviations,
    get_header_amount_severity,
    get_line_amount_severity,
    get_quantity_severity,
    get_unit_price_severity,
    get_unmatched_item_severity,
    getkv_value,
)


class TestCalculateDiffMetrics:
    """Tests for _calculate_diff_metrics() helper function."""

    def test_equal_amounts_returns_unsuccessful(self):
        """Test that equal amounts return success=False with no conversion error."""
        result = _calculate_diff_metrics(Decimal("100.00"), Decimal("100.00"))
        assert result.success is False
        assert result.conversion_error is False
        assert result.abs_diff is None
        assert result.rel_diff is None

    def test_different_amounts_calculates_metrics(self):
        """Test that different amounts calculate absolute and relative diff."""
        result = _calculate_diff_metrics(Decimal("100.00"), Decimal("110.00"))
        assert result.success is True
        assert result.conversion_error is False
        assert result.amount1 == Decimal("100.00")
        assert result.amount2 == Decimal("110.00")
        assert result.abs_diff == Decimal("10.00")
        # rel_diff = 2 * 10 / (100 + 110) = 20 / 210 ≈ 0.0952
        assert result.rel_diff == pytest.approx(Decimal("0.0952"), rel=0.01)

    def test_conversion_error_returns_error(self):
        """Test that invalid amounts return conversion error."""
        result = _calculate_diff_metrics("not_a_number", Decimal("100.00"))
        assert result.success is False
        assert result.conversion_error is True

    def test_handles_floats(self):
        """Test that function handles float inputs."""
        result = _calculate_diff_metrics(100.5, 110.0)
        assert result.success is True
        assert result.abs_diff == Decimal("9.5")

    def test_zero_sum_relative_diff(self):
        """Test relative diff calculation when sum is zero."""
        result = _calculate_diff_metrics(Decimal("-50"), Decimal("50"))
        assert result.success is True
        assert result.abs_diff == Decimal("100")
        assert result.rel_diff == Decimal("0")  # sum is 0


class TestGetHeaderAmountSeverity:
    """Tests for get_header_amount_severity() thresholds."""

    def test_no_severity_within_thresholds(self):
        """Test NO_SEVERITY when abs <= 0.01 AND rel <= 0.001."""
        # abs = 0.01, rel very small
        result = get_header_amount_severity(Decimal("100.00"), Decimal("100.01"))
        assert result == DeviationSeverity.NO_SEVERITY

    def test_low_severity_within_thresholds(self):
        """Test LOW when abs <= 1 AND rel <= 0.01."""
        # abs = 0.50, rel = 2*0.5/(100+100.5) ≈ 0.005
        result = get_header_amount_severity(Decimal("100.00"), Decimal("100.50"))
        assert result == DeviationSeverity.LOW

    def test_medium_severity_within_thresholds(self):
        """Test MEDIUM when abs <= 50 AND rel <= 0.05."""
        # abs = 5, rel = 2*5/(100+105) ≈ 0.0488
        result = get_header_amount_severity(Decimal("100.00"), Decimal("105.00"))
        assert result == DeviationSeverity.MEDIUM

    def test_high_severity_exceeds_thresholds(self):
        """Test HIGH when exceeds medium thresholds."""
        # abs = 100, rel = 2*100/(100+200) = 0.667
        result = get_header_amount_severity(Decimal("100.00"), Decimal("200.00"))
        assert result == DeviationSeverity.HIGH

    def test_equal_amounts_returns_none(self):
        """Test that equal amounts return None (no deviation)."""
        result = get_header_amount_severity(Decimal("100.00"), Decimal("100.00"))
        assert result is None

    def test_conversion_error_returns_low(self):
        """Test that conversion errors return LOW severity."""
        result = get_header_amount_severity("invalid", Decimal("100.00"))
        assert result == DeviationSeverity.LOW


class TestGetLineAmountSeverity:
    """Tests for get_line_amount_severity() thresholds."""

    def test_no_severity_abs_threshold(self):
        """Test NO_SEVERITY when abs <= 0.01."""
        result = get_line_amount_severity(Decimal("10.00"), Decimal("10.009"))
        assert result == DeviationSeverity.NO_SEVERITY

    def test_low_severity_abs_threshold(self):
        """Test LOW when abs <= 1 OR rel <= 0.01."""
        # abs = 0.50, which is <= 1
        result = get_line_amount_severity(Decimal("10.00"), Decimal("10.50"))
        assert result == DeviationSeverity.LOW

    def test_low_severity_rel_threshold(self):
        """Test LOW when rel <= 0.01 even if abs > 1."""
        # abs = 2, rel = 2*2/(200+202) ≈ 0.00995
        result = get_line_amount_severity(Decimal("200.00"), Decimal("202.00"))
        assert result == DeviationSeverity.LOW

    def test_medium_severity_abs_threshold(self):
        """Test MEDIUM when abs <= 10 OR rel <= 0.10."""
        # abs = 5, rel = 2*5/(10+15) = 0.4
        result = get_line_amount_severity(Decimal("10.00"), Decimal("15.00"))
        assert result == DeviationSeverity.MEDIUM

    def test_high_severity_exceeds_thresholds(self):
        """Test HIGH when exceeds medium thresholds."""
        # abs = 50, rel = 2*50/(10+60) ≈ 1.43
        result = get_line_amount_severity(Decimal("10.00"), Decimal("60.00"))
        assert result == DeviationSeverity.HIGH

    def test_equal_amounts_returns_none(self):
        """Test that equal amounts return None (no deviation)."""
        result = get_line_amount_severity(Decimal("50.00"), Decimal("50.00"))
        assert result is None


class TestGetUnitPriceSeverity:
    """Tests for get_unit_price_severity() thresholds."""

    def test_no_severity_abs_threshold(self):
        """Test NO_SEVERITY when abs <= 0.005 OR rel <= 0.005."""
        result = get_unit_price_severity(Decimal("10.00"), Decimal("10.004"))
        assert result == DeviationSeverity.NO_SEVERITY

    def test_no_severity_rel_threshold(self):
        """Test NO_SEVERITY when rel <= 0.005 even if abs > 0.005."""
        # abs = 1, rel = 2*1/(200+201) ≈ 0.00498
        result = get_unit_price_severity(Decimal("200.00"), Decimal("201.00"))
        assert result == DeviationSeverity.NO_SEVERITY

    def test_low_severity_rel_threshold(self):
        """Test LOW when rel <= 0.05."""
        # abs = 0.50, rel = 2*0.5/(10+10.5) ≈ 0.0488
        result = get_unit_price_severity(Decimal("10.00"), Decimal("10.50"))
        assert result == DeviationSeverity.LOW

    def test_medium_severity_rel_threshold(self):
        """Test MEDIUM when rel <= 0.20."""
        # abs = 2, rel = 2*2/(10+12) ≈ 0.182
        result = get_unit_price_severity(Decimal("10.00"), Decimal("12.00"))
        assert result == DeviationSeverity.MEDIUM

    def test_high_severity_exceeds_thresholds(self):
        """Test HIGH when exceeds medium thresholds."""
        # abs = 5, rel = 2*5/(10+15) = 0.4
        result = get_unit_price_severity(Decimal("10.00"), Decimal("15.00"))
        assert result == DeviationSeverity.HIGH

    def test_equal_prices_returns_none(self):
        """Test that equal prices return None (no deviation)."""
        result = get_unit_price_severity(Decimal("25.00"), Decimal("25.00"))
        assert result is None


class TestGetQuantitySeverity:
    """Tests for get_quantity_severity() thresholds."""

    def test_low_severity_both_thresholds(self):
        """Test LOW when abs <= 1 AND rel <= 0.10."""
        # abs = 1, rel = 2*1/(10+11) ≈ 0.095
        result = get_quantity_severity(Decimal("11"), Decimal("10"))
        assert result == DeviationSeverity.LOW

    def test_medium_severity_abs_threshold(self):
        """Test MEDIUM when abs <= 10 OR rel <= 0.50."""
        # abs = 5, rel = 2*5/(10+15) = 0.4
        result = get_quantity_severity(Decimal("15"), Decimal("10"))
        assert result == DeviationSeverity.MEDIUM

    def test_medium_severity_rel_threshold(self):
        """Test MEDIUM when rel <= 0.50 even if abs > 10."""
        # abs = 15, rel = 2*15/(100+115) ≈ 0.14
        result = get_quantity_severity(Decimal("115"), Decimal("100"))
        assert result == DeviationSeverity.MEDIUM

    def test_high_severity_exceeds_thresholds(self):
        """Test HIGH when exceeds medium thresholds."""
        # abs = 50, rel = 2*50/(10+60) ≈ 1.43
        result = get_quantity_severity(Decimal("60"), Decimal("10"))
        assert result == DeviationSeverity.HIGH

    def test_equal_quantities_returns_none(self):
        """Test that equal quantities return None (no deviation)."""
        result = get_quantity_severity(Decimal("10"), Decimal("10"))
        assert result is None


class TestGetUnmatchedItemSeverity:
    """Tests for get_unmatched_item_severity() thresholds."""

    def test_no_severity_threshold(self):
        """Test NO_SEVERITY when line_amount <= 0.01."""
        result = get_unmatched_item_severity(Decimal("0.005"))
        assert result == DeviationSeverity.NO_SEVERITY

    def test_low_severity_threshold(self):
        """Test LOW when line_amount <= 1."""
        result = get_unmatched_item_severity(Decimal("0.50"))
        assert result == DeviationSeverity.LOW

    def test_medium_severity_threshold(self):
        """Test MEDIUM when line_amount <= 10."""
        result = get_unmatched_item_severity(Decimal("5.00"))
        assert result == DeviationSeverity.MEDIUM

    def test_high_severity_threshold(self):
        """Test HIGH when line_amount > 10."""
        result = get_unmatched_item_severity(Decimal("50.00"))
        assert result == DeviationSeverity.HIGH

    def test_none_amount_returns_low(self):
        """Test that None amount returns LOW severity."""
        result = get_unmatched_item_severity(None)
        assert result == DeviationSeverity.LOW

    def test_invalid_amount_returns_low(self):
        """Test that invalid amount returns LOW severity."""
        result = get_unmatched_item_severity("invalid")
        assert result == DeviationSeverity.LOW

    def test_negative_amount_uses_absolute(self):
        """Test that negative amounts use absolute value."""
        result = get_unmatched_item_severity(Decimal("-5.00"))
        assert result == DeviationSeverity.MEDIUM


class TestGetkvValue:
    """Tests for getkv_value() key-value extraction helper."""

    def test_extracts_value_by_name(self):
        """Test that function extracts value by name."""
        kvs = [
            {"name": "field1", "value": "value1"},
            {"name": "field2", "value": "value2"},
        ]
        result = getkv_value(kvs, "field2")
        assert result == "value2"

    def test_returns_none_when_not_found(self):
        """Test that function returns None when name not found."""
        kvs = [{"name": "field1", "value": "value1"}]
        result = getkv_value(kvs, "nonexistent")
        assert result is None

    def test_returns_none_for_none_input(self):
        """Test that function returns None for None input."""
        result = getkv_value(None, "field1")
        assert result is None

    def test_returns_none_for_empty_list(self):
        """Test that function returns None for empty list."""
        result = getkv_value([], "field1")
        assert result is None

    def test_returns_none_for_non_list_input(self):
        """Test that function returns None for non-list input."""
        result = getkv_value("not_a_list", "field1")
        assert result is None

    def test_handles_non_dict_items(self):
        """Test that function handles non-dict items in list."""
        kvs = [{"name": "field1", "value": "value1"}, "not_a_dict"]
        result = getkv_value(kvs, "field1")
        assert result == "value1"


class TestCheckPartialDelivery:
    """Tests for check_partial_delivery() function."""

    def _make_po_fields(self, qty: str) -> list[dict]:
        """Helper to create PO fields."""
        return [{"name": "quantityToInvoice", "value": qty}]

    def _make_invoice_fields(self, qty: str) -> list[dict]:
        """Helper to create invoice fields."""
        return [{"name": "purchaseReceiptDataQuantity", "value": qty}]

    def _make_dr_fields(self, qty: str) -> list[dict]:
        """Helper to create delivery receipt fields."""
        return [{"name": "quantity", "value": qty}]

    def test_partial_delivery_invoice_vs_po(self):
        """Test partial delivery detection for invoice vs PO."""
        result = check_partial_delivery(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_invoice_fields("5"),
                self._make_po_fields("10"),
            ],
        )
        assert result is not None
        assert result.code == "PARTIAL_DELIVERY"
        assert result.severity == DeviationSeverity.INFO
        assert "5 of 10 ordered" in result.message

    def test_partial_delivery_dr_vs_po(self):
        """Test partial delivery detection for DR vs PO."""
        result = check_partial_delivery(
            document_kinds=[DocumentKind.DELIVERY_RECEIPT, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_dr_fields("3"),
                self._make_po_fields("10"),
            ],
        )
        assert result is not None
        assert result.code == "PARTIAL_DELIVERY"
        assert result.severity == DeviationSeverity.INFO

    def test_full_delivery_no_deviation(self):
        """Test that full delivery returns no deviation."""
        result = check_partial_delivery(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_invoice_fields("10"),
                self._make_po_fields("10"),
            ],
        )
        assert result is None

    def test_over_delivery_no_partial_deviation(self):
        """Test that over-delivery doesn't trigger partial delivery."""
        result = check_partial_delivery(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_invoice_fields("15"),
                self._make_po_fields("10"),
            ],
        )
        assert result is None

    def test_no_po_returns_none(self):
        """Test that missing PO returns None."""
        result = check_partial_delivery(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.DELIVERY_RECEIPT],
            document_item_fields=[
                self._make_invoice_fields("5"),
                self._make_dr_fields("5"),
            ],
        )
        assert result is None

    def test_missing_fields_returns_none(self):
        """Test that missing fields return None."""
        result = check_partial_delivery(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[None, self._make_po_fields("10")],
        )
        assert result is None


class TestCheckQuantityDeviation:
    """Tests for check_quantity_deviation() function."""

    def _make_po_fields(self, qty: str) -> list[dict]:
        """Helper to create PO fields."""
        return [{"name": "quantityToInvoice", "value": qty}]

    def _make_invoice_fields(self, qty: str) -> list[dict]:
        """Helper to create invoice fields."""
        return [{"name": "purchaseReceiptDataQuantity", "value": qty}]

    def test_over_delivery_triggers_deviation(self):
        """Test that over-delivery triggers quantity deviation."""
        result = check_quantity_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_invoice_fields("15"),
                self._make_po_fields("10"),
            ],
        )
        assert result is not None
        assert result.code == "QUANTITIES_DIFFER"
        assert "15 vs 10 ordered" in result.message

    def test_under_delivery_no_deviation(self):
        """Test that under-delivery doesn't trigger quantity deviation."""
        result = check_quantity_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_invoice_fields("5"),
                self._make_po_fields("10"),
            ],
        )
        assert result is None

    def test_equal_quantities_no_deviation(self):
        """Test that equal quantities return no deviation."""
        result = check_quantity_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_invoice_fields("10"),
                self._make_po_fields("10"),
            ],
        )
        assert result is None

    def test_severity_based_on_difference(self):
        """Test that severity is calculated based on difference magnitude."""
        # Small over-delivery should be LOW
        result = check_quantity_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_invoice_fields("11"),
                self._make_po_fields("10"),
            ],
        )
        assert result is not None
        assert result.severity == DeviationSeverity.LOW


class TestCheckArticleNumbersDiffer:
    """Tests for check_article_numbers_differ() function."""

    def _make_fields(self, article_number: str | None) -> list[dict] | None:
        """Helper to create item fields with article number."""
        if article_number is None:
            return None
        return [{"name": "inventory", "value": article_number}]

    def test_different_article_numbers_medium_severity(self):
        """Test that different article numbers trigger MEDIUM severity."""
        result = check_article_numbers_differ(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_fields("ART123"),
                self._make_fields("ART456"),
            ],
        )
        assert result is not None
        assert result.code == "ARTICLE_NUMBERS_DIFFER"
        assert result.severity == DeviationSeverity.MEDIUM

    def test_downgrade_to_low_with_high_description_similarity(self):
        """Test that high description similarity downgrades to LOW."""
        result = check_article_numbers_differ(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_fields("ART123"),
                self._make_fields("ART456"),
            ],
            description_similarity=0.95,
        )
        assert result is not None
        assert result.severity == DeviationSeverity.LOW

    def test_same_article_numbers_no_deviation(self):
        """Test that same article numbers return no deviation."""
        result = check_article_numbers_differ(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_fields("ART123"),
                self._make_fields("ART123"),
            ],
        )
        assert result is None

    def test_one_missing_no_deviation(self):
        """Test that one missing article number returns no deviation."""
        result = check_article_numbers_differ(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_fields("ART123"),
                None,
            ],
        )
        assert result is None


class TestCheckItempairComparison:
    """Tests for check_itempair_comparison() function."""

    def test_amounts_differ_comparison(self):
        """Test AMOUNTS_DIFFER comparison with calculated severity."""
        comparison = FieldComparison(
            code="AMOUNTS_DIFFER",
            message="Amounts differ",
            severity=DeviationSeverity.MEDIUM,
            is_item_field=True,
            field_names={
                DocumentKind.INVOICE: "debit",
                DocumentKind.PURCHASE_ORDER: "!quantityToInvoice*unitAmount",
            },
            field_encoded_type=Decimal,
        )
        result = check_itempair_comparison(
            comparison=comparison,
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                [{"name": "debit", "value": "110.00"}],
                [
                    {"name": "quantityToInvoice", "value": "10"},
                    {"name": "unitAmount", "value": "10.00"},
                ],
            ],
        )
        assert result is not None
        assert result.code == "AMOUNTS_DIFFER"
        assert "110.00 vs 100.00" in result.message

    def test_prices_per_unit_differ_comparison(self):
        """Test PRICES_PER_UNIT_DIFFER comparison."""
        comparison = FieldComparison(
            code="PRICES_PER_UNIT_DIFFER",
            message="Unit amounts differ",
            severity=DeviationSeverity.MEDIUM,
            is_item_field=True,
            field_names={
                DocumentKind.INVOICE: "purchaseReceiptDataUnitAmount",
                DocumentKind.PURCHASE_ORDER: "unitAmount",
            },
            field_encoded_type=Decimal,
        )
        result = check_itempair_comparison(
            comparison=comparison,
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                [{"name": "purchaseReceiptDataUnitAmount", "value": "10.50"}],
                [{"name": "unitAmount", "value": "10.00"}],
            ],
        )
        assert result is not None
        assert result.code == "PRICES_PER_UNIT_DIFFER"

    def test_equal_values_no_deviation(self):
        """Test that equal values return no deviation."""
        comparison = FieldComparison(
            code="AMOUNTS_DIFFER",
            message="Amounts differ",
            severity=DeviationSeverity.MEDIUM,
            is_item_field=True,
            field_names={
                DocumentKind.INVOICE: "debit",
                DocumentKind.PURCHASE_ORDER: "!quantityToInvoice*unitAmount",
            },
            field_encoded_type=Decimal,
        )
        result = check_itempair_comparison(
            comparison=comparison,
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                [{"name": "debit", "value": "100.00"}],
                [
                    {"name": "quantityToInvoice", "value": "10"},
                    {"name": "unitAmount", "value": "10.00"},
                ],
            ],
        )
        assert result is None


class TestCollectItempairDeviations:
    """Tests for collect_itempair_deviations() main function."""

    def test_collects_multiple_deviations(self):
        """Test that function collects multiple deviations."""
        result = collect_itempair_deviations(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                [
                    {"name": "debit", "value": "110.00"},
                    {"name": "text", "value": "Steel bolt"},
                    {"name": "purchaseReceiptDataQuantity", "value": "10"},
                    {"name": "purchaseReceiptDataUnitAmount", "value": "11.00"},
                ],
                [
                    {"name": "quantityToInvoice", "value": "10"},
                    {"name": "unitAmount", "value": "10.00"},
                    {"name": "description", "value": "Plastic widget"},
                ],
            ],
            similarities={"description": 0.3},
        )
        # Should detect AMOUNTS_DIFFER, DESCRIPTIONS_DIFFER, PRICES_PER_UNIT_DIFFER
        assert len(result) >= 2
        codes = [d.code for d in result]
        assert "AMOUNTS_DIFFER" in codes
        assert "DESCRIPTIONS_DIFFER" in codes

    def test_partial_delivery_excludes_quantity_deviation(self):
        """Test that partial delivery excludes quantity deviation check."""
        result = collect_itempair_deviations(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                [
                    {"name": "debit", "value": "50.00"},
                    {"name": "text", "value": "Steel bolt"},
                    {"name": "purchaseReceiptDataQuantity", "value": "5"},
                ],
                [
                    {"name": "quantityToInvoice", "value": "10"},
                    {"name": "unitAmount", "value": "10.00"},
                    {"name": "description", "value": "Steel bolt"},
                ],
            ],
        )
        codes = [d.code for d in result]
        assert "PARTIAL_DELIVERY" in codes
        # QUANTITIES_DIFFER should not be present when partial delivery detected
        assert "QUANTITIES_DIFFER" not in codes

    def test_empty_result_for_identical_items(self):
        """Test that identical items return empty result."""
        result = collect_itempair_deviations(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                [
                    {"name": "debit", "value": "100.00"},
                    {"name": "text", "value": "Steel bolt"},
                    {"name": "purchaseReceiptDataQuantity", "value": "10"},
                    {"name": "purchaseReceiptDataUnitAmount", "value": "10.00"},
                ],
                [
                    {"name": "quantityToInvoice", "value": "10"},
                    {"name": "unitAmount", "value": "10.00"},
                    {"name": "description", "value": "Steel bolt"},
                ],
            ],
        )
        assert len(result) == 0

    def test_mismatch_document_kinds_and_fields_returns_empty(self):
        """Test that mismatched lengths return empty result."""
        result = collect_itempair_deviations(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                [{"name": "debit", "value": "100.00"}],
            ],
        )
        assert len(result) == 0

    def test_items_differ_detection(self):
        """Test that ITEMS_DIFFER is detected with low similarities."""
        result = collect_itempair_deviations(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                [
                    {"name": "debit", "value": "100.00"},
                    {"name": "text", "value": "Product A"},
                ],
                [
                    {"name": "quantityToInvoice", "value": "10"},
                    {"name": "unitAmount", "value": "10.00"},
                    {"name": "description", "value": "Product B"},
                ],
            ],
            similarities={"item_id": 0.2, "description": 0.3},
        )
        codes = [d.code for d in result]
        assert "ITEMS_DIFFER" in codes
