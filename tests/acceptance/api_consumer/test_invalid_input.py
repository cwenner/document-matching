"""
Simple BDD tests for invalid input handling - using existing step definitions
"""

import pytest
from pytest_bdd import scenario

# Import from centralized config module
from tests.config import get_feature_path

# Import existing step definitions and fixtures
from tests.acceptance.steps.api_steps import client, context


# Test only the original scenarios from the feature file
@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Missing Primary Document",
)
def test_missing_primary_document():
    """Test API response when primary document is missing."""
    pass


@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Invalid Document Format",
)
def test_invalid_document_format():
    """Test API response when document format is invalid."""
    pass


@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Malformed JSON Payload",
)
def test_malformed_json_payload():
    """Test API response when JSON payload is malformed."""
    pass
