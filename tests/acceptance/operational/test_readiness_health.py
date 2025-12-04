import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then, when

import app

# Import common step definitions
from tests.acceptance.steps.api_steps import context  # noqa: F401

# Import from centralized config module
from tests.config import get_feature_path

# --- Feature: API Readiness and Health Checks ---


# Background
@given(parsers.parse('the matching service is expected to be running at "{base_url}"'))
def matching_service_base_url(context, base_url):
    # Use dictionary access as context is a dict in the test fixture
    context["base_url"] = base_url


@scenario(
    str(get_feature_path("operational/readiness_health.feature")),
    "Readiness probe indicates service is ready",
)
def test_readiness_probe():
    pass


@scenario(
    str(get_feature_path("operational/readiness_health.feature")),
    "Liveness probe indicates service is healthy",
)
def test_liveness_probe():
    pass


# FastAPI TestClient fixture
@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app.app)


# --- Common When Step ---
@when(parsers.parse('I send a GET request to "{path}"'))
def send_get_request(context, client, path):
    # Use dictionary access as context is a dict in the test fixture
    # For testing, we don't need the base_url as the TestClient handles the path directly
    context["response"] = client.get(path)

    # Store the path for later assertions if needed
    context["request_path"] = path


@then(parsers.parse("the response status code should be {status_code:d}"))
def response_status_code(context, status_code):
    assert context["response"].status_code == status_code


@then(
    parsers.parse(
        'the JSON response should contain a field "{field_name}" with value "{field_value}"'
    )
)
def json_response_contains_field_value(context, field_name, field_value):
    response_json = context["response"].json()
    assert (
        field_name in response_json
    ), f"Field '{field_name}' not in response {response_json}"
    assert (
        str(response_json[field_name]) == field_value
    ), f"Field '{field_name}' value mismatch: expected '{field_value}', got '{response_json[field_name]}'"
