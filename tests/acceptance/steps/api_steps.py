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


@given(parsers.parse("I have a primary invoice document with amount {amount:f}"))
def primary_invoice_with_amount(context, amount):
    """
    Create a primary invoice document with a specific amount
    """
    context["document"] = {
        "id": "invoice-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "total_amount", "value": str(amount)},
            {"name": "currency", "value": "USD"},
        ],
        "items": [
            {
                "description": "Test Item",
                "quantity": 1,
                "unit_price": amount,
                "total_price": amount,
            }
        ],
    }


@given(parsers.parse("I have a candidate purchase order with amount {amount:f}"))
def candidate_po_with_amount(context, amount):
    """
    Create a candidate purchase order document with a specific amount
    """
    context["candidate-documents"] = [
        {
            "id": "po-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "input",
            "headers": [
                {"name": "total_amount", "value": str(amount)},
                {"name": "currency", "value": "USD"},
            ],
            "items": [
                {
                    "description": "Test Item",
                    "quantity": 1,
                    "unit_price": amount,
                    "total_price": amount,
                }
            ],
        }
    ]


@when('I send a POST request to "/" with the primary document and candidate document')
def send_post_request_with_documents(context, client):
    """
    Send a POST request with primary and candidate documents
    """
    payload = {
        "document": context["document"],
        "candidate-documents": context["candidate-documents"],
    }
    context["response"] = client.post("/", json=payload)


@then("the response body should contain a match report")
def response_contains_match_report(context):
    """
    Check that the response contains a match report
    """
    response_data = context["response"].json()
    assert "version" in response_data, "Response should contain version field"
    assert "kind" in response_data, "Response should contain kind field"
    assert response_data["kind"] == "match-report", "Response should be a match-report"


@then(parsers.parse('the match report should contain "{label}" in labels'))
def match_report_contains_label(context, label):
    """
    Check that the match report contains a specific label
    """
    response_data = context["response"].json()
    labels = response_data.get("labels", [])
    assert (
        label in labels
    ), f"Match report should contain '{label}' in labels, got: {labels}"


@then(
    parsers.parse(
        'the match report should include deviation with code "{deviation_code}"'
    )
)
def match_report_includes_deviation(context, deviation_code):
    """
    Check that the match report includes a deviation with a specific code
    """
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])

    deviation_codes = [dev.get("code") for dev in deviations]
    assert (
        deviation_code in deviation_codes
    ), f"Should include deviation with code '{deviation_code}', got codes: {deviation_codes}"


@then("the deviation severity should reflect the percentage difference")
def deviation_severity_reflects_percentage(context):
    """
    Check that the deviation severity reflects the percentage difference
    """
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])

    amounts_differ_deviation = None
    for dev in deviations:
        if dev.get("code") == "amounts-differ":
            amounts_differ_deviation = dev
            break

    assert amounts_differ_deviation is not None, "Should have amounts-differ deviation"

    # Calculate expected percentage difference: (1500 - 1450) / 1500 = 0.033 = 3.33%
    primary_amount = 1500.00
    candidate_amount = 1450.00
    percentage_diff = abs(primary_amount - candidate_amount) / primary_amount * 100

    # Check if severity is appropriate for the percentage difference
    # Small difference (< 5%) should be "low", medium (5-15%) should be "medium", high (>15%) should be "high"
    severity = amounts_differ_deviation.get("severity")
    if percentage_diff < 5:
        expected_severity = "low"
    elif percentage_diff < 15:
        expected_severity = "medium"
    else:
        expected_severity = "high"

    assert (
        severity == expected_severity
    ), f"Expected severity '{expected_severity}' for {percentage_diff:.2f}% difference, got '{severity}'"
