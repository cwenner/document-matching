"""
Unit tests for description deviation severity functions.

Tests cover:
- get_description_deviation_severity() threshold mapping
- _normalize_for_comparison() normalization logic
- check_description_deviation() edge cases
"""

import pytest

from itempair_deviations import (
    DeviationSeverity,
    DocumentKind,
    _normalize_for_comparison,
    check_description_deviation,
    get_description_deviation_severity,
)


class TestGetDescriptionDeviationSeverity:
    """Tests for similarity-to-severity threshold mapping."""

    @pytest.mark.parametrize(
        "similarity,expected_severity",
        [
            # NO_SEVERITY: >= 0.98
            (1.0, DeviationSeverity.NO_SEVERITY),
            (0.99, DeviationSeverity.NO_SEVERITY),
            (0.98, DeviationSeverity.NO_SEVERITY),
            # INFO: >= 0.90 and < 0.98
            (0.97, DeviationSeverity.INFO),
            (0.95, DeviationSeverity.INFO),
            (0.90, DeviationSeverity.INFO),
            # LOW: >= 0.75 and < 0.90
            (0.89, DeviationSeverity.LOW),
            (0.80, DeviationSeverity.LOW),
            (0.75, DeviationSeverity.LOW),
            # MEDIUM: >= 0.50 and < 0.75
            (0.74, DeviationSeverity.MEDIUM),
            (0.60, DeviationSeverity.MEDIUM),
            (0.50, DeviationSeverity.MEDIUM),
            # HIGH: < 0.50
            (0.49, DeviationSeverity.HIGH),
            (0.30, DeviationSeverity.HIGH),
            (0.0, DeviationSeverity.HIGH),
        ],
    )
    def test_severity_thresholds(self, similarity: float, expected_severity: str):
        """Test that severity thresholds are correctly applied."""
        result = get_description_deviation_severity(similarity)
        assert result == expected_severity

    def test_none_similarity_returns_high(self):
        """Test that None similarity returns HIGH severity."""
        result = get_description_deviation_severity(None)
        assert result == DeviationSeverity.HIGH


class TestNormalizeForComparison:
    """Tests for casing/whitespace normalization."""

    def test_none_returns_empty_string(self):
        """Test that None input returns empty string."""
        result = _normalize_for_comparison(None)
        assert result == ""

    def test_lowercase_conversion(self):
        """Test that text is lowercased."""
        result = _normalize_for_comparison("Hello World")
        assert result == "helloworld"

    def test_whitespace_removal(self):
        """Test that all whitespace is removed."""
        result = _normalize_for_comparison("hello   world")
        assert result == "helloworld"

    def test_mixed_whitespace_removal(self):
        """Test that tabs, newlines, and spaces are removed."""
        result = _normalize_for_comparison("hello\t\nworld  test")
        assert result == "helloworldtest"

    def test_empty_string(self):
        """Test that empty string remains empty."""
        result = _normalize_for_comparison("")
        assert result == ""

    def test_only_whitespace(self):
        """Test that whitespace-only string becomes empty."""
        result = _normalize_for_comparison("   \t\n  ")
        assert result == ""


class TestCheckDescriptionDeviation:
    """Tests for check_description_deviation edge cases."""

    def _make_item_fields(self, description: str | None) -> list[dict] | None:
        """Helper to create item fields structure."""
        if description is None:
            return None
        return [{"name": "text", "value": description}]

    def _make_po_item_fields(self, description: str | None) -> list[dict] | None:
        """Helper to create PO item fields structure."""
        if description is None:
            return None
        return [{"name": "description", "value": description}]

    def test_both_empty_no_deviation(self):
        """Test that both empty descriptions result in no deviation."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields(""),
                self._make_po_item_fields(""),
            ],
        )
        assert result is None

    def test_both_whitespace_only_no_deviation(self):
        """Test that both whitespace-only descriptions result in no deviation."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields("   "),
                self._make_po_item_fields("\t\n"),
            ],
        )
        assert result is None

    def test_one_empty_high_severity(self):
        """Test that one empty description results in HIGH severity."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields("Steel bolt M8"),
                self._make_po_item_fields(""),
            ],
        )
        assert result is not None
        assert result.code == "DESCRIPTIONS_DIFFER"
        assert result.severity == DeviationSeverity.HIGH

    def test_casing_only_difference_no_deviation(self):
        """Test that casing-only difference results in no deviation."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields("Steel Bolt"),
                self._make_po_item_fields("steel bolt"),
            ],
        )
        assert result is None

    def test_whitespace_only_difference_no_deviation(self):
        """Test that whitespace-only difference results in no deviation."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields("Steel Bolt"),
                self._make_po_item_fields("Steel  Bolt"),
            ],
        )
        assert result is None

    def test_identical_descriptions_no_deviation(self):
        """Test that identical descriptions result in no deviation."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields("10mm galvanized bolt"),
                self._make_po_item_fields("10mm galvanized bolt"),
            ],
        )
        assert result is None

    def test_different_descriptions_uses_similarity(self):
        """Test that different descriptions use similarity for severity."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields("Steel bolt M8"),
                self._make_po_item_fields("Plastic widget"),
            ],
            description_similarity=0.30,
        )
        assert result is not None
        assert result.code == "DESCRIPTIONS_DIFFER"
        assert result.severity == DeviationSeverity.HIGH

    def test_different_descriptions_medium_severity(self):
        """Test that moderately different descriptions get MEDIUM severity."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields("Steel fastener"),
                self._make_po_item_fields("Metal fastener bolt"),
            ],
            description_similarity=0.60,
        )
        assert result is not None
        assert result.code == "DESCRIPTIONS_DIFFER"
        assert result.severity == DeviationSeverity.MEDIUM

    def test_missing_item_fields_returns_none(self):
        """Test that missing item fields result in no deviation."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields("Steel bolt"),
                None,
            ],
        )
        assert result is None

    def test_field_names_in_deviation(self):
        """Test that field names are correctly populated in deviation."""
        result = check_description_deviation(
            document_kinds=[DocumentKind.INVOICE, DocumentKind.PURCHASE_ORDER],
            document_item_fields=[
                self._make_item_fields("Steel bolt"),
                self._make_po_item_fields("Plastic widget"),
            ],
            description_similarity=0.30,
        )
        assert result is not None
        assert result.field_names == ["text", "description"]
