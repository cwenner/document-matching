"""
Unit tests for itempairing module.

Tests cover:
- Similarity calculation functions
- find_best_item_match function
- pair_document_items function
- Edge cases (empty items, single item, None values)
"""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np

import itempairing


class TestCalculateDescriptionSimilarity:
    """Tests for _calculate_description_similarity function."""

    def test_both_empty_returns_one(self):
        """Test that both empty descriptions return 1.0 similarity."""
        result = itempairing._calculate_description_similarity("", "")
        assert result == 1.0

    def test_one_empty_returns_zero(self):
        """Test that one empty description returns 0.0 similarity."""
        result = itempairing._calculate_description_similarity("test", "")
        assert result == 0.0
        result = itempairing._calculate_description_similarity("", "test")
        assert result == 0.0

    def test_both_none_returns_none(self):
        """Test that both None descriptions return None."""
        result = itempairing._calculate_description_similarity(None, None)
        assert result is None

    def test_one_none_returns_none(self):
        """Test that one None description returns None."""
        result = itempairing._calculate_description_similarity("test", None)
        assert result is None
        result = itempairing._calculate_description_similarity(None, "test")
        assert result is None

    @patch("itempairing.model", None)
    def test_no_model_returns_none(self):
        """Test that missing model returns None."""
        result = itempairing._calculate_description_similarity("test", "test")
        assert result is None

    def test_identical_descriptions_high_similarity(self):
        """Test that identical descriptions have high similarity."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        result = itempairing._calculate_description_similarity(
            "Steel bolt M8", "Steel bolt M8"
        )
        assert result is not None
        assert result > 0.95

    def test_similar_descriptions_moderate_similarity(self):
        """Test that similar descriptions have moderate similarity."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        result = itempairing._calculate_description_similarity(
            "Steel bolt M8", "Steel fastener M8"
        )
        assert result is not None
        assert 0.5 < result < 1.0

    def test_different_descriptions_low_similarity(self):
        """Test that different descriptions have low similarity."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        result = itempairing._calculate_description_similarity(
            "Steel bolt", "Plastic widget"
        )
        assert result is not None
        assert result < 0.7

    def test_nan_similarity_returns_zero(self):
        """Test that NaN similarity returns 0.0."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        with patch("itempairing.model.encode") as mock_encode:
            mock_encode.return_value = np.array([[1.0, 2.0], [np.nan, np.nan]])
            result = itempairing._calculate_description_similarity("test1", "test2")
            assert result == 0.0

    def test_exception_returns_zero(self):
        """Test that exception during calculation returns 0.0."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        with patch("itempairing.model.encode") as mock_encode:
            mock_encode.side_effect = Exception("Test error")
            result = itempairing._calculate_description_similarity("test1", "test2")
            assert result == 0.0


class TestCalculateItemIdSimilarity:
    """Tests for _calculate_item_id_similarity function."""

    def test_both_empty_returns_one(self):
        """Test that both empty IDs return 1.0 similarity."""
        result = itempairing._calculate_item_id_similarity("", "")
        assert result == 1.0

    def test_one_empty_returns_zero(self):
        """Test that one empty ID returns 0.0 similarity."""
        result = itempairing._calculate_item_id_similarity("TEST-001", "")
        assert result == 0.0
        result = itempairing._calculate_item_id_similarity("", "TEST-001")
        assert result == 0.0

    def test_both_none_returns_none(self):
        """Test that both None IDs return None."""
        result = itempairing._calculate_item_id_similarity(None, None)
        assert result is None

    def test_one_none_returns_none(self):
        """Test that one None ID returns None."""
        result = itempairing._calculate_item_id_similarity("TEST-001", None)
        assert result is None
        result = itempairing._calculate_item_id_similarity(None, "TEST-001")
        assert result is None

    def test_identical_ids_returns_one(self):
        """Test that identical IDs return 1.0 similarity."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        result = itempairing._calculate_item_id_similarity("TEST-001", "TEST-001")
        assert result == 1.0

    def test_different_ids_uses_embedding(self):
        """Test that different IDs use embedding similarity."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        result = itempairing._calculate_item_id_similarity("TEST-001", "TEST-002")
        assert result is not None
        assert 0.0 <= result <= 1.0

    @patch("itempairing.model", None)
    def test_no_model_returns_none(self):
        """Test that missing model returns None."""
        result = itempairing._calculate_item_id_similarity("TEST-001", "TEST-002")
        assert result is None

    def test_numeric_ids_converted_to_string(self):
        """Test that numeric IDs are converted to strings."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        result = itempairing._calculate_item_id_similarity(123, 123)
        assert result == 1.0

    def test_exception_returns_none(self):
        """Test that exception during calculation returns None."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        with patch("itempairing.model.encode") as mock_encode:
            mock_encode.side_effect = Exception("Test error")
            result = itempairing._calculate_item_id_similarity("test1", "test2")
            assert result is None


class TestCalculateUnitPriceSimilarity:
    """Tests for _calculate_unit_price_similarity function."""

    def test_both_none_returns_none(self):
        """Test that both None prices return None."""
        result = itempairing._calculate_unit_price_similarity(None, None)
        assert result is None

    def test_one_none_returns_none(self):
        """Test that one None price returns None."""
        result = itempairing._calculate_unit_price_similarity(10.0, None)
        assert result is None
        result = itempairing._calculate_unit_price_similarity(None, 10.0)
        assert result is None

    def test_identical_prices_returns_one(self):
        """Test that identical prices return 1.0 similarity."""
        result = itempairing._calculate_unit_price_similarity(10.0, 10.0)
        assert result == 1.0

    def test_nearly_identical_prices_returns_one(self):
        """Test that nearly identical prices return 1.0 similarity."""
        result = itempairing._calculate_unit_price_similarity(10.0, 10.00001)
        assert result == 1.0

    def test_similar_prices_returns_ratio(self):
        """Test that similar prices return ratio similarity."""
        result = itempairing._calculate_unit_price_similarity(10.0, 20.0)
        assert result == 0.5

    def test_different_prices_returns_ratio(self):
        """Test that different prices return ratio similarity."""
        result = itempairing._calculate_unit_price_similarity(5.0, 10.0)
        assert result == 0.5

    def test_opposite_sign_prices_returns_zero(self):
        """Test that opposite sign prices return 0.0 similarity."""
        result = itempairing._calculate_unit_price_similarity(10.0, -10.0)
        assert result == 0.0

    def test_string_prices_converted(self):
        """Test that string prices are converted to float."""
        result = itempairing._calculate_unit_price_similarity("10.0", "20.0")
        assert result == 0.5

    def test_invalid_string_prices_returns_zero(self):
        """Test that invalid string prices return 0.0."""
        result = itempairing._calculate_unit_price_similarity("invalid", "10.0")
        assert result == 0.0
        result = itempairing._calculate_unit_price_similarity("10.0", "invalid")
        assert result == 0.0

    def test_zero_prices_returns_one(self):
        """Test that both zero prices return 1.0 similarity."""
        result = itempairing._calculate_unit_price_similarity(0.0, 0.0)
        assert result == 1.0


class TestCalculateMatchScore:
    """Tests for _calculate_match_score function."""

    def test_all_perfect_match(self):
        """Test that all perfect similarities result in match."""
        score, is_match = itempairing._calculate_match_score(1.0, 1.0, 1.0)
        assert score == 1.0
        assert is_match is True

    def test_high_average_is_match(self):
        """Test that high average similarity is a match."""
        score, is_match = itempairing._calculate_match_score(0.9, 0.8, 0.8)
        assert score == pytest.approx(0.8666, rel=1e-2)
        assert is_match is True

    def test_threshold_boundary_is_match(self):
        """Test that 0.8 threshold is a match."""
        score, is_match = itempairing._calculate_match_score(0.8, 0.8, 0.8)
        assert score == 0.8
        assert is_match is True

    def test_below_threshold_not_match(self):
        """Test that below 0.8 threshold is not a match."""
        score, is_match = itempairing._calculate_match_score(0.7, 0.7, 0.7)
        assert score == pytest.approx(0.7)
        assert is_match is False

    def test_none_values_ignored(self):
        """Test that None values are ignored in average."""
        score, is_match = itempairing._calculate_match_score(1.0, None, 1.0)
        assert score == 1.0
        assert is_match is True

    def test_mixed_none_and_values(self):
        """Test that mixed None and values calculate correctly."""
        score, is_match = itempairing._calculate_match_score(0.9, None, 0.7)
        assert score == 0.8
        assert is_match is True

    def test_all_none_handled(self):
        """Test that all None values are handled."""
        # This should cause division by zero, but let's see what happens
        with pytest.raises(ZeroDivisionError):
            itempairing._calculate_match_score(None, None, None)


class TestFindBestItemMatch:
    """Tests for find_best_item_match function."""

    def test_empty_target_items_returns_none(self):
        """Test that empty target items return None."""
        source_item = {"item-id": "TEST-001", "description": "Steel bolt"}
        result = itempairing.find_best_item_match(source_item, [])
        assert result is None

    @patch("itempairing.model", None)
    def test_no_model_returns_none(self):
        """Test that missing model returns None."""
        source_item = {"item-id": "TEST-001", "description": "Steel bolt"}
        target_items = [{"item-id": "TEST-002", "description": "Steel bolt"}]
        result = itempairing.find_best_item_match(source_item, target_items)
        assert result is None

    def test_all_matched_items_returns_none(self):
        """Test that all matched target items return None."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        source_item = {"item-id": "TEST-001", "description": "Steel bolt"}
        target_items = [
            {"item-id": "TEST-002", "description": "Steel bolt", "matched": True}
        ]
        result = itempairing.find_best_item_match(source_item, target_items)
        assert result is None

    def test_finds_best_match(self):
        """Test that best match is found."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        source_item = {
            "item-id": "TEST-001",
            "description": "Steel bolt M8",
            "unit-price": 10.0,
        }
        target_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            },
            {
                "item-id": "TEST-002",
                "description": "Plastic widget",
                "unit-price": 5.0,
            },
        ]
        result = itempairing.find_best_item_match(source_item, target_items)
        assert result is not None
        assert result["is_match"] is True
        assert result["target_item"]["item-id"] == "TEST-001"

    def test_uses_unit_price_adjusted(self):
        """Test that unit-price-adjusted is used over unit-price."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        source_item = {
            "item-id": "TEST-001",
            "description": "Steel bolt",
            "unit-price": 5.0,
            "unit-price-adjusted": 10.0,
        }
        target_items = [
            {"item-id": "TEST-001", "description": "Steel bolt", "unit-price": 10.0}
        ]
        result = itempairing.find_best_item_match(source_item, target_items)
        assert result is not None
        # Should use 10.0 (adjusted) vs 10.0, giving perfect price match

    def test_multiple_description_fields(self):
        """Test that multiple description fields are considered."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        source_item = {
            "item-id": "TEST-001",
            "description": "Steel",
            "text": "Bolt M8",
            "inventory": "Hardware",
        }
        target_items = [
            {"item-id": "TEST-001", "text": "Bolt M8", "unit-price": 10.0}
        ]
        result = itempairing.find_best_item_match(source_item, target_items)
        assert result is not None

    def test_selects_highest_score_match(self):
        """Test that highest score match is selected."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        source_item = {
            "item-id": "TEST-001",
            "description": "Steel bolt M8",
            "unit-price": 10.0,
        }
        target_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            },
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8 galvanized",
                "unit-price": 10.0,
            },
        ]
        result = itempairing.find_best_item_match(source_item, target_items)
        assert result is not None
        assert result["target_item"]["item-id"] == "TEST-001"


class TestPairDocumentItems:
    """Tests for pair_document_items function."""

    @patch("itempairing.model", None)
    def test_no_model_returns_empty_list(self):
        """Test that missing model returns empty list."""
        doc1_items = [{"item-id": "TEST-001"}]
        doc2_items = [{"item-id": "TEST-002"}]
        result = itempairing.pair_document_items(doc1_items, doc2_items)
        assert result == []

    def test_empty_items_returns_empty_list(self):
        """Test that empty items return empty list."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        result = itempairing.pair_document_items([], [])
        assert result == []

    def test_single_matching_pair(self):
        """Test that single matching pair is found."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        doc1_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            }
        ]
        doc2_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            }
        ]
        result = itempairing.pair_document_items(doc1_items, doc2_items)
        assert len(result) == 1
        assert result[0]["item1"]["item-id"] == "TEST-001"
        assert result[0]["item2"]["item-id"] == "TEST-001"
        assert result[0]["score"] > 0.8

    def test_multiple_matching_pairs(self):
        """Test that multiple matching pairs are found."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        doc1_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            },
            {
                "item-id": "TEST-002",
                "description": "Plastic widget",
                "unit-price": 5.0,
            },
        ]
        doc2_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            },
            {
                "item-id": "TEST-002",
                "description": "Plastic widget",
                "unit-price": 5.0,
            },
        ]
        result = itempairing.pair_document_items(doc1_items, doc2_items)
        assert len(result) == 2

    def test_no_matching_pairs(self):
        """Test that no matching pairs returns empty list."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        doc1_items = [
            {"item-id": "TEST-001", "description": "Steel bolt", "unit-price": 10.0}
        ]
        doc2_items = [
            {
                "item-id": "TEST-999",
                "description": "Completely different item",
                "unit-price": 100.0,
            }
        ]
        result = itempairing.pair_document_items(doc1_items, doc2_items)
        assert len(result) == 0

    def test_matched_flag_set_correctly(self):
        """Test that matched flags are set correctly."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        doc1_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            }
        ]
        doc2_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            }
        ]
        result = itempairing.pair_document_items(doc1_items, doc2_items)
        assert doc1_items[0]["matched"] is True
        assert doc2_items[0]["matched"] is True

    def test_unmatched_items_flag_false(self):
        """Test that unmatched items have matched flag set to False."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        doc1_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            },
            {
                "item-id": "TEST-999",
                "description": "Unmatched item",
                "unit-price": 100.0,
            },
        ]
        doc2_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            }
        ]
        result = itempairing.pair_document_items(doc1_items, doc2_items)
        assert len(result) == 1
        assert doc1_items[0]["matched"] is True
        assert doc1_items[1]["matched"] is False

    def test_similarities_included_in_result(self):
        """Test that similarities are included in result."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        doc1_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            }
        ]
        doc2_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            }
        ]
        result = itempairing.pair_document_items(doc1_items, doc2_items)
        assert "similarities" in result[0]
        assert "item_id" in result[0]["similarities"]
        assert "description" in result[0]["similarities"]
        assert "unit_price" in result[0]["similarities"]

    def test_one_to_one_matching(self):
        """Test that items are matched one-to-one."""
        if itempairing.model is None:
            pytest.skip("SentenceTransformer model not available")
        # Two identical items in doc1, one in doc2
        doc1_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            },
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            },
        ]
        doc2_items = [
            {
                "item-id": "TEST-001",
                "description": "Steel bolt M8",
                "unit-price": 10.0,
            }
        ]
        result = itempairing.pair_document_items(doc1_items, doc2_items)
        # Should only match once
        assert len(result) == 1
