"""
Test configurable confidence thresholds (Issue #105).
"""

import os
from unittest.mock import patch

import pytest


class TestConfigurableThresholds:
    """Test that confidence thresholds can be configured via environment variables."""

    def test_default_thresholds(self):
        """Test that default threshold values are used when no env vars are set."""
        # Import after ensuring no env vars are set
        with patch.dict(os.environ, {}, clear=False):
            # Force re-import to pick up the env vars
            import importlib
            import match_reporter

            importlib.reload(match_reporter)

            # Default values
            assert match_reporter.MATCHED_CERTAINTY_THRESHOLD == 0.5
            assert match_reporter.NO_MATCH_CERTAINTY_THRESHOLD == 0.2

    def test_custom_match_threshold(self):
        """Test that MATCH_CONFIDENCE_THRESHOLD env var is respected."""
        with patch.dict(os.environ, {"MATCH_CONFIDENCE_THRESHOLD": "0.7"}, clear=False):
            import importlib
            import match_reporter

            importlib.reload(match_reporter)

            assert match_reporter.MATCHED_CERTAINTY_THRESHOLD == 0.7

    def test_custom_no_match_threshold(self):
        """Test that NO_MATCH_CONFIDENCE_THRESHOLD env var is respected."""
        with patch.dict(
            os.environ, {"NO_MATCH_CONFIDENCE_THRESHOLD": "0.1"}, clear=False
        ):
            import importlib
            import match_reporter

            importlib.reload(match_reporter)

            assert match_reporter.NO_MATCH_CERTAINTY_THRESHOLD == 0.1

    def test_both_custom_thresholds(self):
        """Test that both threshold env vars can be set simultaneously."""
        with patch.dict(
            os.environ,
            {
                "MATCH_CONFIDENCE_THRESHOLD": "0.8",
                "NO_MATCH_CONFIDENCE_THRESHOLD": "0.15",
            },
            clear=False,
        ):
            import importlib
            import match_reporter

            importlib.reload(match_reporter)

            assert match_reporter.MATCHED_CERTAINTY_THRESHOLD == 0.8
            assert match_reporter.NO_MATCH_CERTAINTY_THRESHOLD == 0.15

    def test_invalid_threshold_uses_default(self):
        """Test that invalid threshold values fall back to defaults."""
        with patch.dict(
            os.environ, {"MATCH_CONFIDENCE_THRESHOLD": "invalid"}, clear=False
        ):
            import importlib
            import match_reporter

            importlib.reload(match_reporter)

            # Should fall back to default
            assert match_reporter.MATCHED_CERTAINTY_THRESHOLD == 0.5

    def test_out_of_range_threshold_uses_default(self):
        """Test that out-of-range threshold values fall back to defaults."""
        with patch.dict(
            os.environ,
            {
                "MATCH_CONFIDENCE_THRESHOLD": "1.5",  # > 1.0
                "NO_MATCH_CONFIDENCE_THRESHOLD": "-0.1",  # < 0.0
            },
            clear=False,
        ):
            import importlib
            import match_reporter

            importlib.reload(match_reporter)

            # Should fall back to defaults
            assert match_reporter.MATCHED_CERTAINTY_THRESHOLD == 0.5
            assert match_reporter.NO_MATCH_CERTAINTY_THRESHOLD == 0.2

    def test_boundary_values(self):
        """Test that boundary values (0.0 and 1.0) are accepted."""
        with patch.dict(
            os.environ,
            {
                "MATCH_CONFIDENCE_THRESHOLD": "1.0",
                "NO_MATCH_CONFIDENCE_THRESHOLD": "0.0",
            },
            clear=False,
        ):
            import importlib
            import match_reporter

            importlib.reload(match_reporter)

            assert match_reporter.MATCHED_CERTAINTY_THRESHOLD == 1.0
            assert match_reporter.NO_MATCH_CERTAINTY_THRESHOLD == 0.0
