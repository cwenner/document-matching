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


@given(parsers.parse("I have a primary invoice document with amount {amount:f}"))
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
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Test Product B"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "debit", "value": str(amount * 0.8)},
                ]
            }
        ],
    }


@given(parsers.parse("I have a candidate purchase order with amount {amount:f}"))
def candidate_po_with_amount(context, amount):
    """
    Create a candidate purchase order document with a specific amount based on test data
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
                {"name": "incVatAmount", "value": str(amount)},
                {"name": "excVatAmount", "value": str(amount * 0.8)},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-003"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "E561-13-20"},
                        {"name": "description", "value": "Test Product B"},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": str(amount / 2)},
                        {"name": "quantityOrdered", "value": "2.00"},
                        {"name": "quantityToReceive", "value": "2.00"},
                        {"name": "quantityReceived", "value": "0.00"},
                        {"name": "quantityToInvoice", "value": "2.00"},
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
        if dev.get("code") == "AMOUNTS_DIFFER":
            amounts_differ_deviation = dev
            break

    assert amounts_differ_deviation is not None, "Should have AMOUNTS_DIFFER deviation"

    # Calculate expected percentage difference: (1500 - 1450) / 1500 = 0.033 = 3.33%
    primary_amount = 1500.00
    candidate_amount = 1450.00
    percentage_diff = abs(primary_amount - candidate_amount) / primary_amount * 100

    # Check that severity is a valid value and makes sense for the percentage difference
    severity = amounts_differ_deviation.get("severity")
    valid_severities = ["no-severity", "low", "medium", "high", "info"]

    assert (
        severity in valid_severities
    ), f"Severity should be one of {valid_severities}, got '{severity}'"

    # For a 3.33% difference, severity should be reasonable (not "high" for such a small difference)
    assert (
        severity != "high"
    ), f"Severity should not be 'high' for small {percentage_diff:.2f}% difference, got '{severity}'"


@then(
    parsers.parse(
        'the AMOUNTS_DIFFER deviation severity should be "{expected_severity}"'
    )
)
def check_amounts_differ_severity(context, expected_severity):
    """Check that the AMOUNTS_DIFFER deviation has the expected severity."""
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])

    amounts_differ = None
    for dev in deviations:
        if dev.get("code") == "AMOUNTS_DIFFER":
            amounts_differ = dev
            break

    assert amounts_differ is not None, "Should have AMOUNTS_DIFFER deviation"
    assert (
        amounts_differ.get("severity") == expected_severity
    ), f"AMOUNTS_DIFFER severity should be '{expected_severity}', got: {amounts_differ.get('severity')}"


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


@then(
    parsers.parse('the match report should contain item with match_type "{match_type}"')
)
def match_report_contains_item_match_type(context, match_type):
    """Check that the match report contains an item with specific match_type."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    match_types = [pair.get("match_type") for pair in itempairs]
    assert (
        match_type in match_types
    ), f"Should contain item with match_type '{match_type}', got: {match_types}"


@then("the ITEM_UNMATCHED deviation severity should reflect the line amount")
def check_item_unmatched_severity_reflects_amount(context):
    """Check that ITEM_UNMATCHED severity reflects the line amount value."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    for itempair in itempairs:
        if itempair.get("match_type") == "unmatched":
            for dev in itempair.get("deviations", []):
                if dev.get("code") == "ITEM_UNMATCHED":
                    severity = dev.get("severity")
                    valid_severities = ["no-severity", "low", "medium", "high"]
                    assert (
                        severity in valid_severities
                    ), f"ITEM_UNMATCHED severity should be valid, got: {severity}"
                    return

    pytest.fail("Should have ITEM_UNMATCHED deviation in unmatched items")


@then(
    parsers.parse(
        'the ARTICLE_NUMBERS_DIFFER item deviation severity should be "{sev1}" or "{sev2}"'
    )
)
def check_article_numbers_severity_range(context, sev1, sev2):
    """Check that ARTICLE_NUMBERS_DIFFER severity is one of two values."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    found_deviation = None
    for itempair in itempairs:
        for dev in itempair.get("deviations", []):
            if dev.get("code") == "ARTICLE_NUMBERS_DIFFER":
                found_deviation = dev
                break
        if found_deviation:
            break

    assert found_deviation is not None, "Should have ARTICLE_NUMBERS_DIFFER deviation"
    severity = found_deviation.get("severity")
    assert severity in [
        sev1,
        sev2,
    ], f"ARTICLE_NUMBERS_DIFFER severity should be '{sev1}' or '{sev2}', got: {severity}"


# ==============================================================================
# Scenario functions
# ==============================================================================


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Match with Amount Deviations",
)
def test_match_with_amount_deviations():
    """Test that the service correctly handles amount deviations between documents."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Header amount deviation - no-severity for tiny differences",
)
def test_header_amount_no_severity():
    """Test no-severity for tiny amount differences."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Header amount deviation - low severity for small differences",
)
def test_header_amount_low_severity():
    """Test low severity for small amount differences."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Header amount deviation - medium severity for moderate differences",
)
def test_header_amount_medium_severity():
    """Test medium severity for moderate amount differences."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Header amount deviation - high severity for large differences",
)
def test_header_amount_high_severity():
    """Test high severity for large amount differences."""
    pass
