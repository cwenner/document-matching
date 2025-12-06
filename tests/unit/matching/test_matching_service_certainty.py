"""Unit tests for matching_service.py certainty values in dummy functions."""

import pytest

from matching_service import MatchingService


class TestDummyReportCertaintyValues:
    """Tests that dummy reports use calculated/constant certainty values, not hardcoded magic numbers."""

    @pytest.fixture
    def service(self):
        """Create a matching service instance."""
        return MatchingService()

    # Test that certainty is not the old hardcoded value
    def test_dummy_no_match_report_certainty_not_hardcoded(self, service):
        """Certainty in no-match report should not be the old hardcoded 0.95."""
        document = {"id": "test-1", "kind": "invoice", "site": "test-site"}
        report = service._dummy_no_match_report(document)

        certainty_metric = next(
            (m for m in report["metrics"] if m["name"] == "certainty"), None
        )
        assert certainty_metric is not None
        # Should be 0.5 (DUMMY_CERTAINTY), not 0.95
        assert certainty_metric["value"] != 0.95
        assert certainty_metric["value"] == 0.5

    def test_dummy_match_report_certainty_not_hardcoded(self, service):
        """Certainty in match report should not be the old hardcoded 0.93."""
        document = {"id": "test-2", "kind": "invoice", "site": "test-site"}
        report = service._dummy_match_report(document)

        certainty_metric = next(
            (m for m in report["metrics"] if m["name"] == "certainty"), None
        )
        assert certainty_metric is not None
        # Should be 0.5 (DUMMY_CERTAINTY), not 0.93
        assert certainty_metric["value"] != 0.93
        assert certainty_metric["value"] == 0.5

    def test_dummy_no_match_future_certainty_is_calculated(self, service):
        """Future match certainty in no-match report should use calculated values."""
        # Unmatched invoice without order ref returns 0.5
        document = {"id": "test-3", "kind": "invoice", "site": "test-site"}
        report = service._dummy_no_match_report(document)

        future_metric = next(
            (
                m
                for m in report["metrics"]
                if m["name"] == "invoice-has-future-match-certainty"
            ),
            None,
        )
        assert future_metric is not None
        # Should be 0.5 (unmatched invoice without order ref), not 0.88
        assert future_metric["value"] != 0.88
        assert future_metric["value"] == 0.5

    def test_dummy_match_future_certainty_is_calculated(self, service):
        """Future match certainty in match report should use calculated values."""
        document = {"id": "test-4", "kind": "invoice", "site": "test-site"}
        report = service._dummy_match_report(document)

        future_metric = next(
            (
                m
                for m in report["metrics"]
                if m["name"] == "invoice-has-future-match-certainty"
            ),
            None,
        )
        assert future_metric is not None
        # For matched invoice, should be 0.1 (already matched, less likely more)
        assert future_metric["value"] != 0.98
        assert future_metric["value"] == 0.1

    def test_dummy_match_item_certainty_not_hardcoded(self, service):
        """Item unchanged certainty should not be hardcoded 0.88."""
        document = {"id": "test-5", "kind": "invoice", "site": "test-site"}
        report = service._dummy_match_report(document)

        assert len(report["itempairs"]) > 0
        item_certainty = report["itempairs"][0].get("item_unchanged_certainty")
        assert item_certainty is not None
        # Should be 0.5 (DUMMY_CERTAINTY), not 0.88
        assert item_certainty != 0.88
        assert item_certainty == 0.5


class TestDummyReportCertaintyRanges:
    """Tests that all certainty values are in valid [0.0, 1.0] range."""

    @pytest.fixture
    def service(self):
        """Create a matching service instance."""
        return MatchingService()

    def test_all_no_match_certainty_values_in_range(self, service):
        """All certainty values in no-match report should be in [0.0, 1.0]."""
        document = {"id": "range-test-1", "kind": "invoice", "site": "test-site"}
        report = service._dummy_no_match_report(document)

        for metric in report["metrics"]:
            if "certainty" in metric["name"]:
                assert (
                    0.0 <= metric["value"] <= 1.0
                ), f"Metric {metric['name']} out of range: {metric['value']}"

    def test_all_match_certainty_values_in_range(self, service):
        """All certainty values in match report should be in [0.0, 1.0]."""
        document = {"id": "range-test-2", "kind": "invoice", "site": "test-site"}
        report = service._dummy_match_report(document)

        for metric in report["metrics"]:
            if "certainty" in metric["name"]:
                assert (
                    0.0 <= metric["value"] <= 1.0
                ), f"Metric {metric['name']} out of range: {metric['value']}"

        for pair in report["itempairs"]:
            if "item_unchanged_certainty" in pair:
                assert (
                    0.0 <= pair["item_unchanged_certainty"] <= 1.0
                ), f"item_unchanged_certainty out of range: {pair['item_unchanged_certainty']}"
