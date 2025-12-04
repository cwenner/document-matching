import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then, when

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


@given(
    parsers.parse("I have a primary invoice document with item quantity {quantity:d}")
)
def primary_invoice_with_item_quantity(context, quantity):
    """
    Create a primary invoice document with specific item quantity based on test data
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
            {"name": "incVatAmount", "value": "1000.00"},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": "800.00"},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Test Product B"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "purchaseReceiptDataQuantity", "value": str(quantity)},
                    {"name": "debit", "value": "800.00"},
                ]
            }
        ],
    }


@given(
    parsers.parse("I have a candidate purchase order with item quantity {quantity:d}")
)
def candidate_po_with_item_quantity(context, quantity):
    """
    Create a candidate purchase order document with specific item quantity based on test data
    """
    context["candidate-documents"] = [
        {
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
                {"name": "incVatAmount", "value": "1000.00"},
                {"name": "excVatAmount", "value": "800.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-003"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "E561-13-20"},
                        {"name": "description", "value": "Test Product B"},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": "400.00"},
                        {"name": "quantityOrdered", "value": str(quantity)},
                        {"name": "quantityToReceive", "value": str(quantity)},
                        {"name": "quantityReceived", "value": "0.00"},
                        {"name": "quantityToInvoice", "value": str(quantity)},
                    ]
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


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(status_code, context):
    """
    Check that the response has the expected status code
    """
    assert context["response"].status_code == status_code


@then("the response body should contain a match report")
def response_contains_match_report(context):
    """
    Check that the response contains a match report
    """
    response_data = context["response"].json()
    assert "version" in response_data, "Response should contain version field"
    assert "kind" in response_data, "Response should contain kind field"
    assert response_data["kind"] == "match-report", "Response should be a match-report"


@then(
    parsers.parse(
        'the match report should contain deviation with code "{deviation_code}"'
    )
)
def match_report_includes_deviation(context, deviation_code):
    """
    Check that the match report includes a deviation with a specific code (in itempairs)
    """
    response_data = context["response"].json()

    # Check itempair deviations since quantity deviations are item-level
    itempairs = response_data.get("itempairs", [])
    all_deviation_codes = []

    for itempair in itempairs:
        itempair_deviations = itempair.get("deviations", [])
        for dev in itempair_deviations:
            all_deviation_codes.append(dev.get("code"))

    assert (
        deviation_code in all_deviation_codes
    ), f"Should include deviation with code '{deviation_code}', got codes: {all_deviation_codes}"


@then("the deviation severity should reflect the percentage difference")
def deviation_severity_reflects_percentage(context):
    """
    Check that the deviation severity reflects the percentage difference for quantities
    """
    response_data = context["response"].json()

    # Find quantity deviation in itempairs
    quantities_differ_deviation = None
    itempairs = response_data.get("itempairs", [])

    for itempair in itempairs:
        itempair_deviations = itempair.get("deviations", [])
        for dev in itempair_deviations:
            if dev.get("code") == "QUANTITIES_DIFFER":
                quantities_differ_deviation = dev
                break
        if quantities_differ_deviation:
            break

    assert (
        quantities_differ_deviation is not None
    ), "Should have QUANTITIES_DIFFER deviation"

    # Calculate expected percentage difference: (10 - 8) / 10 = 0.2 = 20%
    primary_quantity = 10
    candidate_quantity = 8
    percentage_diff = (
        abs(primary_quantity - candidate_quantity) / primary_quantity * 100
    )

    # Check that severity is a valid value and makes sense for the percentage difference
    severity = quantities_differ_deviation.get("severity")
    valid_severities = ["low", "medium", "high", "info"]

    assert (
        severity in valid_severities
    ), f"Severity should be one of {valid_severities}, got '{severity}'"

    # For a 20% difference, severity should be reasonable (likely medium or high)
    assert (
        severity != "low"
    ), f"Severity should not be 'low' for significant {percentage_diff:.2f}% difference, got '{severity}'"


@then(
    parsers.parse(
        'the match report should contain item deviation with code "{deviation_code}"'
    )
)
def match_report_contains_item_deviation(context, deviation_code):
    """Check that the match report contains an item-level deviation with specific code."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])
    all_codes = []

    for itempair in itempairs:
        for dev in itempair.get("deviations", []):
            all_codes.append(dev.get("code"))

    assert (
        deviation_code in all_codes
    ), f"Should include item deviation '{deviation_code}', got: {all_codes}"


@then(
    parsers.parse(
        'the {deviation_code} item deviation severity should be "{expected_severity}"'
    )
)
def check_item_deviation_severity(context, deviation_code, expected_severity):
    """Check that a specific item deviation has the expected severity."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    found_deviation = None
    for itempair in itempairs:
        for dev in itempair.get("deviations", []):
            if dev.get("code") == deviation_code:
                found_deviation = dev
                break
        if found_deviation:
            break

    assert found_deviation is not None, f"Should have {deviation_code} deviation"
    assert (
        found_deviation.get("severity") == expected_severity
    ), f"{deviation_code} severity should be '{expected_severity}', got: {found_deviation.get('severity')}"


@then(parsers.parse('the match report should contain "{label}" in labels'))
def match_report_contains_label(context, label):
    """Check that the match report contains a specific label."""
    response_data = context["response"].json()
    labels = response_data.get("labels", [])
    assert label in labels, f"Should contain '{label}' in labels, got: {labels}"


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Match with Quantity Deviations",
)
def test_match_with_quantity_deviations():
    """Test that the service correctly handles quantity deviations between documents."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Quantity deviation - low severity for small excess",
)
def test_quantity_low_severity():
    """Test low severity for small quantity excess."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Quantity deviation - high severity for large excess",
)
def test_quantity_high_severity():
    """Test high severity for large quantity excess."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Match with Partial Delivery",
)
def test_partial_delivery():
    """Test PARTIAL_DELIVERY deviation when qty < PO qty."""
    pass
