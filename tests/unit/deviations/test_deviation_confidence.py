"""
Unit tests for deviation confidence field.

Tests cover:
- FieldDeviation model has confidence field with default value
- check_items_differ() sets confidence based on similarity metrics
- Other deviation functions use default confidence of 1.0
"""

import pytest

from itempair_deviations import (
    MIXED_SIMILARITY_CONFIDENCE,
    DocumentKind,
    FieldDeviation,
    check_items_differ,
    create_item_unmatched_deviation,
)


class TestFieldDeviationConfidence:
    """Tests for FieldDeviation confidence field."""

    def test_confidence_field_exists(self):
        """Test that FieldDeviation model has confidence field."""
        deviation = FieldDeviation(
            code="TEST", message="test", severity="info", confidence=0.75
        )
        assert hasattr(deviation, "confidence")
        assert deviation.confidence == 0.75

    def test_confidence_default_is_one(self):
        """Test that confidence defaults to 1.0 when not specified."""
        deviation = FieldDeviation(code="TEST", message="test", severity="info")
        assert deviation.confidence == 1.0

    def test_confidence_range_validation(self):
        """Test that confidence can be set to any float value."""
        for value in [0.0, 0.25, 0.5, 0.75, 1.0]:
            deviation = FieldDeviation(
                code="TEST", message="test", severity="info", confidence=value
            )
            assert deviation.confidence == value

    def test_model_dump_includes_confidence(self):
        """Test that model_dump() includes confidence field."""
        deviation = FieldDeviation(
            code="TEST", message="test", severity="info", confidence=0.8
        )
        dumped = deviation.model_dump()
        assert "confidence" in dumped
        assert dumped["confidence"] == 0.8


class TestItemsDifferConfidence:
    """Tests for check_items_differ() confidence calculation."""

    def test_both_similarities_very_low_high_confidence(self):
        """When both similarities are very low, confidence should be high."""
        similarities = {"item_id": 0.2, "description": 0.1}
        result = check_items_differ(similarities)

        assert result is not None
        assert result.code == "ITEMS_DIFFER"
        # Confidence = 1 - (0.2 + 0.1) / 2 = 0.85
        assert result.confidence == pytest.approx(0.85, rel=0.01)
        assert result.severity == "high"

    def test_both_similarities_low_medium_confidence(self):
        """When both similarities are low, confidence should be medium."""
        similarities = {"item_id": 0.4, "description": 0.3}
        result = check_items_differ(similarities)

        assert result is not None
        assert result.code == "ITEMS_DIFFER"
        # Confidence = 1 - (0.4 + 0.3) / 2 = 0.65
        assert result.confidence == pytest.approx(0.65, rel=0.01)
        assert result.severity == "medium"

    def test_both_similarities_moderate_low_confidence(self):
        """When both similarities are moderate, confidence should be lower."""
        similarities = {"item_id": 0.45, "description": 0.49}
        result = check_items_differ(similarities)

        assert result is not None
        assert result.code == "ITEMS_DIFFER"
        # Confidence = 1 - (0.45 + 0.49) / 2 = 0.53
        assert result.confidence == pytest.approx(0.53, rel=0.01)
        # Not high enough for medium (0.65)
        assert result.severity in ["medium", "low"]

    def test_mixed_signal_uses_constant_confidence(self):
        """When signals are mixed, use MIXED_SIMILARITY_CONFIDENCE constant."""
        similarities = {"item_id": 0.25, "description": 0.65}
        result = check_items_differ(similarities)

        assert result is not None
        assert result.code == "ITEMS_DIFFER"
        assert result.confidence == MIXED_SIMILARITY_CONFIDENCE
        assert result.severity == "medium"

    def test_mixed_signal_reverse_order(self):
        """Test mixed signal with reversed similarity values."""
        similarities = {"item_id": 0.65, "description": 0.25}
        result = check_items_differ(similarities)

        assert result is not None
        assert result.code == "ITEMS_DIFFER"
        assert result.confidence == MIXED_SIMILARITY_CONFIDENCE
        assert result.severity == "medium"

    def test_no_deviation_when_similarities_high(self):
        """When similarities are high, no deviation is returned."""
        similarities = {"item_id": 0.8, "description": 0.9}
        result = check_items_differ(similarities)
        assert result is None

    def test_no_deviation_when_one_similarity_high(self):
        """When one similarity is high enough, no deviation is returned."""
        similarities = {"item_id": 0.3, "description": 0.8}
        result = check_items_differ(similarities)
        assert result is None

    def test_confidence_in_message(self):
        """Test that confidence appears in deviation message."""
        similarities = {"item_id": 0.2, "description": 0.1}
        result = check_items_differ(similarities)

        assert result is not None
        # Message should contain confidence percentage
        assert "85%" in result.message or "0.85" in result.message


class TestDefaultConfidenceValues:
    """Tests that other deviation functions use default confidence of 1.0."""

    def test_item_unmatched_has_default_confidence(self):
        """Test that ITEM_UNMATCHED deviation has confidence 1.0."""
        item_data = {
            "raw_item": {
                "fields": [{"name": "debit", "value": "50.00"}],
            }
        }
        result = create_item_unmatched_deviation(item_data, DocumentKind.INVOICE)

        assert result.code == "ITEM_UNMATCHED"
        assert result.confidence == 1.0

    def test_constant_value(self):
        """Test that MIXED_SIMILARITY_CONFIDENCE is defined correctly."""
        assert MIXED_SIMILARITY_CONFIDENCE == 0.6
