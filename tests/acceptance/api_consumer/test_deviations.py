import pytest
from pytest_bdd import scenario, given, when, then, parsers
from fastapi.testclient import TestClient

import app
from tests.config import get_feature_path


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app.app)


@pytest.fixture
def context():
    """Shared context between steps"""
    return {}


@given("the document matching service is available")
def document_matching_service(context):
    """Set up the document matching service"""
    context["base_url"] = "http://localhost:8000"


@given(parsers.parse('I have a primary invoice document with amount {amount:f}'))
def primary_invoice_with_amount(context, amount):
    """
    Create a primary invoice document with a specific amount based on test data
    """
    context["document"] = {
        "version": "v3",
        "id": "PD-003",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": str(amount)},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": str(amount * 0.8)},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"}
        ],
        "items": [{
            "fields": [
                {"name": "text", "value": "Test Product B"},
                {"name": "lineNumber", "value": "1"},
                {"name": "debit", "value": str(amount * 0.8)}
            ]
        }]
    }


@given(parsers.parse('I have a candidate purchase order with amount {amount:f}'))
def candidate_po_with_amount(context, amount):
    """
    Create a candidate purchase order document with a specific amount based on test data
    """
    context["candidate-documents"] = [{
        "version": "v3",
        "id": "CD-002",
        "kind": "purchase-order",
        "site": "test-site",
        "stage": "final",
        "headers": [
            {"name": "orderNumber", "value": "PO-12345"},
            {"name": "supplierId", "value": "S789"},
            {"name": "description", "value": "XYZ"},
            {"name": "orderDate", "value": "2025-06-20"},
            {"name": "incVatAmount", "value": str(amount)},
            {"name": "excVatAmount", "value": str(amount * 0.8)}
        ],
        "items": [{
            "fields": [
                {"name": "id", "value": "IT-003"},
                {"name": "lineNumber", "value": "1"},
                {"name": "inventory", "value": "E561-13-20"},
                {"name": "description", "value": "Test Product B"},
                {"name": "uom", "value": "STYCK"},
                {"name": "unitAmount", "value": str(amount/2)},
                {"name": "quantityOrdered", "value": "2.00"},
                {"name": "quantityToReceive", "value": "2.00"},
                {"name": "quantityReceived", "value": "0.00"},
                {"name": "quantityToInvoice", "value": "2.00"}
            ]
        }]
    }]


@when('I send a POST request to "/" with the primary document and candidate document')
def send_post_request_with_documents(context, client):
    """
    Send a POST request with primary and candidate documents
    """
    payload = {
        "document": context["document"],
        "candidate-documents": context["candidate-documents"]
    }
    context["response"] = client.post("/", json=payload)


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(status_code, context):
    """
    Check that the response has the expected status code
    """
    assert context["response"].status_code == status_code


@then('the response body should contain a match report')
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
    assert label in labels, f"Match report should contain '{label}' in labels, got: {labels}"


@then(parsers.parse('the match report should include deviation with code "{deviation_code}"'))
def match_report_includes_deviation(context, deviation_code):
    """
    Check that the match report includes a deviation with a specific code
    """
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])
    
    deviation_codes = [dev.get("code") for dev in deviations]
    assert deviation_code in deviation_codes, f"Should include deviation with code '{deviation_code}', got codes: {deviation_codes}"


@then('the deviation severity should reflect the percentage difference')
def deviation_severity_reflects_percentage(context):
    """
    Check that the deviation severity reflects the percentage difference
    """
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])
    
    amounts_differ_deviation = None
    for dev in deviations:
        if dev.get("code") == "total-amounts-differ":
            amounts_differ_deviation = dev
            break
    
    assert amounts_differ_deviation is not None, "Should have total-amounts-differ deviation"
    
    # Calculate expected percentage difference: (1500 - 1450) / 1500 = 0.033 = 3.33%
    primary_amount = 1500.00
    candidate_amount = 1450.00
    percentage_diff = abs(primary_amount - candidate_amount) / primary_amount * 100
    
    # Check that severity is a valid value and makes sense for the percentage difference
    severity = amounts_differ_deviation.get("severity")
    valid_severities = ["low", "medium", "high", "info"]
    
    assert severity in valid_severities, f"Severity should be one of {valid_severities}, got '{severity}'"
    
    # For a 3.33% difference, severity should be reasonable (not "high" for such a small difference)
    assert severity != "high", f"Severity should not be 'high' for small {percentage_diff:.2f}% difference, got '{severity}'"


@scenario(str(get_feature_path("api-consumer/deviations.feature")), "Match with Amount Deviations")
def test_match_with_amount_deviations():
    """Test that the service correctly handles amount deviations between documents."""
    pass
