"""
Common step definitions for API testing
"""
import json
import pytest
from pytest_bdd import given, when, then, parsers
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))
from app import app

@pytest.fixture
def client():
    """
    Test client for the FastAPI app
    """
    return TestClient(app)


@pytest.fixture
def context():
    """Shared context between steps"""
    return {}


@given("the document matching service is available")
def document_matching_service(context):
    """
    Set up the document matching service
    """
    context["base_url"] = "http://localhost:8000"


@when(parsers.parse('the primary document has a "{field_name}" of "{field_value}"'))
def primary_doc_field(context, field_name, field_value):
    """
    Set a field in the primary document
    """
    if "primary_document" not in context:
        context["primary_document"] = {
            "id": "doc-1",
            "kind": "invoice",
            "headers": [],
            "items": [],
        }

    context["primary_document"]["headers"].append(
        {"name": field_name, "value": field_value}
    )


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(status_code, context):
    """
    Check that the response has the expected status code
    """
    assert context["response"].status_code == status_code


@then(parsers.parse('the response should contain a "{field}" field'))
def response_contains_field(context, field):
    """
    Check that the response contains a specific field
    """
    response_data = context["response"].json()
    assert field in response_data, f"Response should contain '{field}' field"
