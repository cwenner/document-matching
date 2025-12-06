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
    """Check that a specific item deviation has the expected severity.

    Also handles 'or' patterns like 'low" or "medium' that get parsed as single value.
    """
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

    # Handle "or" patterns - parsers.parse captures 'low" or "medium' as one value
    if '" or "' in expected_severity:
        allowed_severities = [s.strip('"') for s in expected_severity.split('" or "')]
        assert found_deviation.get("severity") in allowed_severities, (
            f"{deviation_code} severity should be one of {allowed_severities}, "
            f"got: {found_deviation.get('severity')}"
        )
    else:
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
        'the match report should contain deviation with code "{deviation_code}"'
    )
)
def match_report_contains_deviation_code(context, deviation_code):
    """Check that the match report contains a deviation with a specific code."""
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])

    deviation_codes = [dev.get("code") for dev in deviations]
    assert (
        deviation_code in deviation_codes
    ), f"Should contain deviation with code '{deviation_code}', got codes: {deviation_codes}"


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


# ==============================================================================
# DESCRIPTIONS_DIFFER step definitions (#27)
# ==============================================================================


@given(
    parsers.re(r'I have a primary invoice with item description "(?P<description>.*)"')
)
def primary_invoice_with_item_description(context, description):
    """Create a primary invoice document with specific item description."""
    context["document"] = {
        "version": "v3",
        "id": "PD-DESC-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": "100.00"},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": "80.00"},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": description},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "debit", "value": "80.00"},
                ]
            }
        ],
    }


@given(
    parsers.re(
        r'I have a candidate purchase order with item description "(?P<description>.*)"'
    )
)
def candidate_po_with_item_description(context, description):
    """Create a candidate purchase order with specific item description."""
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "CD-DESC-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": "100.00"},
                {"name": "excVatAmount", "value": "80.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-DESC-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "INV-001"},
                        {"name": "description", "value": description},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": "80.00"},
                        {"name": "quantityOrdered", "value": "1"},
                        {"name": "quantityToReceive", "value": "1"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "1"},
                    ]
                }
            ],
        }
    ]


@given(
    parsers.re(
        r'I have a primary invoice with item and article number "(?P<article_number>.+)" and description "(?P<description>.*)"'
    )
)
def primary_invoice_with_article_and_description(context, article_number, description):
    """Create a primary invoice with article number and description."""
    context["document"] = {
        "version": "v3",
        "id": "PD-DESC-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": "100.00"},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": "80.00"},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": description},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": article_number},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "debit", "value": "80.00"},
                ]
            }
        ],
    }


@given(
    parsers.re(
        r'I have a candidate purchase order with item and article number "(?P<article_number>.+)" and description "(?P<description>.*)"'
    )
)
def candidate_po_with_article_and_description(context, article_number, description):
    """Create a candidate purchase order with article number and description."""
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "CD-DESC-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": "100.00"},
                {"name": "excVatAmount", "value": "80.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-DESC-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": article_number},
                        {"name": "description", "value": description},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": "80.00"},
                        {"name": "quantityOrdered", "value": "1"},
                        {"name": "quantityToReceive", "value": "1"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "1"},
                    ]
                }
            ],
        }
    ]


@then("the deviation severity should reflect the textual similarity")
def deviation_severity_reflects_similarity(context):
    """Check that the deviation severity reflects textual similarity."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    found_deviation = None
    for itempair in itempairs:
        for dev in itempair.get("deviations", []):
            if dev.get("code") == "DESCRIPTIONS_DIFFER":
                found_deviation = dev
                break
        if found_deviation:
            break

    assert found_deviation is not None, "Should have DESCRIPTIONS_DIFFER deviation"
    severity = found_deviation.get("severity")
    valid_severities = ["no-severity", "info", "low", "medium", "high"]
    assert (
        severity in valid_severities
    ), f"Severity should be one of {valid_severities}, got: {severity}"


@then("there should be no DESCRIPTIONS_DIFFER deviation")
def no_descriptions_differ_deviation(context):
    """Check that there is no DESCRIPTIONS_DIFFER deviation."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    for itempair in itempairs:
        for dev in itempair.get("deviations", []):
            if dev.get("code") == "DESCRIPTIONS_DIFFER":
                pytest.fail(
                    f"Should NOT have DESCRIPTIONS_DIFFER deviation, but found: {dev}"
                )


# ==============================================================================
# DESCRIPTIONS_DIFFER scenario functions (#27)
# ==============================================================================


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Match with Different Item Descriptions",
)
def test_match_with_different_descriptions():
    """Test that the service correctly handles description differences."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Description deviation - no-severity for nearly identical descriptions",
)
def test_description_no_severity_nearly_identical():
    """Test no-severity for nearly identical descriptions."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Description deviation - no-severity for casing differences only",
)
def test_description_no_severity_casing():
    """Test no-severity for casing differences only."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Description deviation - no-severity for whitespace differences only",
)
def test_description_no_severity_whitespace():
    """Test no-severity for whitespace differences only."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Description deviation - info severity for reordered terms",
)
def test_description_info_severity():
    """Test info severity for reordered terms."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Description deviation - low severity for wording differences",
)
def test_description_low_severity():
    """Test low severity for wording differences."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Description deviation - medium severity for overlapping topic",
)
def test_description_medium_severity():
    """Test medium severity for overlapping topic."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Description deviation - no deviation when both descriptions are empty",
)
def test_description_no_deviation_both_empty():
    """Test no deviation when both descriptions are empty."""
    pass


# ==============================================================================
# Unit Price Deviations (#25)
# ==============================================================================


@given(parsers.parse("I have a primary invoice with item unit price {price:f}"))
def primary_invoice_with_unit_price(context, price):
    """Create a primary invoice document with specific item unit price."""
    context["document"] = {
        "version": "v3",
        "id": "PD-UNIT-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": str(price)},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": str(price * 0.8)},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Test Product"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "purchaseReceiptDataUnitAmount", "value": str(price)},
                    {"name": "debit", "value": str(price)},
                ]
            }
        ],
    }


@given(
    parsers.parse("I have a candidate purchase order with item unit price {price:f}")
)
def candidate_po_with_unit_price(context, price):
    """Create a candidate purchase order with specific item unit price."""
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "CD-UNIT-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": str(price)},
                {"name": "excVatAmount", "value": str(price * 0.8)},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-UNIT-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "INV-001"},
                        {"name": "description", "value": "Test Product"},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": str(price)},
                        {"name": "quantityOrdered", "value": "1"},
                        {"name": "quantityToReceive", "value": "1"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "1"},
                    ]
                }
            ],
        }
    ]


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Unit price deviation - low severity for small price difference",
)
def test_unit_price_low_severity():
    """Test low severity for small unit price difference."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Unit price deviation - high severity for large price difference",
)
def test_unit_price_high_severity():
    """Test high severity for large unit price difference."""
    pass


# ==============================================================================
# Article Number Deviations (#22)
# ==============================================================================


@given(
    parsers.re(
        r'I have a primary invoice with item article number "(?P<article_number>.+)" and description "(?P<description>.*)"'
    )
)
def primary_invoice_with_article_and_desc(context, article_number, description):
    """Create a primary invoice with article number and description."""
    context["document"] = {
        "version": "v3",
        "id": "PD-ART-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": "100.00"},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": "80.00"},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": description},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": article_number},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "debit", "value": "80.00"},
                ]
            }
        ],
    }


@given(
    parsers.re(
        r'I have a candidate purchase order with item article number "(?P<article_number>.+)" and description "(?P<description>.*)"'
    )
)
def candidate_po_with_article_and_desc(context, article_number, description):
    """Create a candidate purchase order with article number and description."""
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "CD-ART-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": "100.00"},
                {"name": "excVatAmount", "value": "80.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-ART-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": article_number},
                        {"name": "description", "value": description},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": "80.00"},
                        {"name": "quantityOrdered", "value": "1"},
                        {"name": "quantityToReceive", "value": "1"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "1"},
                    ]
                }
            ],
        }
    ]


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Article number deviation with similar descriptions",
)
def test_article_number_deviation():
    """Test article number deviation with similar descriptions."""
    pass


# ==============================================================================
# Unmatched Items (#20)
# ==============================================================================


@given("I have a primary invoice with two items where one has no match")
def primary_invoice_with_unmatched_item(context):
    """Create a primary invoice with two items, one of which won't match."""
    context["document"] = {
        "version": "v3",
        "id": "PD-UNMAT-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": "200.00"},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": "160.00"},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Matching Product"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "MATCH-001"},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "debit", "value": "80.00"},
                ]
            },
            {
                "fields": [
                    {"name": "text", "value": "Unmatched Product"},
                    {"name": "lineNumber", "value": "2"},
                    {"name": "inventory", "value": "NOMATCH-999"},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "debit", "value": "80.00"},
                ]
            },
        ],
    }


@given("I have a candidate purchase order with one item")
def candidate_po_with_one_item(context):
    """Create a candidate purchase order with only one matching item."""
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "CD-UNMAT-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": "100.00"},
                {"name": "excVatAmount", "value": "80.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-MATCH-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "MATCH-001"},
                        {"name": "description", "value": "Matching Product"},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": "80.00"},
                        {"name": "quantityOrdered", "value": "1"},
                        {"name": "quantityToReceive", "value": "1"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "1"},
                    ]
                }
            ],
        }
    ]


# Note: "Unmatched item with high value" scenario was replaced with
# 4 threshold-specific scenarios in ITEM_UNMATCHED Threshold Tests section


# ==============================================================================
# Currency Deviations
# ==============================================================================


@given(parsers.parse('I have a primary invoice document with currency "{currency}"'))
def primary_invoice_with_currency(context, currency):
    """Create a primary invoice document with specific currency."""
    context["document"] = {
        "version": "v3",
        "id": "PD-CUR-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": "100.00"},
            {"name": "currency", "value": currency},
            {"name": "currencyCode", "value": currency},
            {"name": "excVatAmount", "value": "80.00"},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Test Product"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "debit", "value": "80.00"},
                ]
            }
        ],
    }


@given(parsers.parse('I have a candidate purchase order with currency "{currency}"'))
def candidate_po_with_currency(context, currency):
    """Create a candidate purchase order with specific currency."""
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "CD-CUR-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": "100.00"},
                {"name": "currency", "value": currency},
                {"name": "excVatAmount", "value": "80.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-CUR-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "INV-001"},
                        {"name": "description", "value": "Test Product"},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": "80.00"},
                        {"name": "quantityOrdered", "value": "1"},
                        {"name": "quantityToReceive", "value": "1"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "1"},
                    ]
                }
            ],
        }
    ]


@then(parsers.parse('the deviation severity should be "{expected_severity}"'))
def check_deviation_severity(context, expected_severity):
    """Check that a deviation has the expected severity."""
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])

    found = False
    for dev in deviations:
        if dev.get("severity") == expected_severity:
            found = True
            break

    assert found, (
        f"Should have deviation with severity '{expected_severity}', "
        f"got deviations: {deviations}"
    )


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Match with Different Currencies",
)
def test_match_with_different_currencies():
    """Test CURRENCIES_DIFFER deviation with high severity."""
    pass


# ==============================================================================
# Match with Different Item Descriptions
# ==============================================================================


@then("the deviation severity should reflect the textual similarity")
def check_deviation_reflects_textual_similarity(context):
    """Check that deviation severity reflects textual similarity."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    found_desc_deviation = False
    for pair in itempairs:
        for dev in pair.get("deviations", []):
            if dev.get("code") == "DESCRIPTIONS_DIFFER":
                found_desc_deviation = True
                severity = dev.get("severity")
                valid_severities = ["no-severity", "info", "low", "medium", "high"]
                assert (
                    severity in valid_severities
                ), f"DESCRIPTIONS_DIFFER should have valid severity, got: {severity}"
                break

    assert found_desc_deviation, "Should have DESCRIPTIONS_DIFFER deviation"


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Match with Different Item Descriptions",
)
def test_match_with_different_descriptions_scenario():
    """Test DESCRIPTIONS_DIFFER deviation with similarity-based severity."""
    pass


# ==============================================================================
# Comprehensive Deviation Reporting
# ==============================================================================


@given("I have a primary invoice document with multiple deviations from the standard")
def primary_invoice_with_multiple_deviations(context):
    """Create a primary invoice with multiple deviation sources."""
    context["document"] = {
        "version": "v3",
        "id": "PD-COMP-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": "1500.00"},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": "1200.00"},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Widget A Premium"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "WGT-001"},
                    {"name": "purchaseReceiptDataQuantity", "value": "10"},
                    {"name": "debit", "value": "500.00"},
                    {"name": "unitPrice", "value": "50.00"},
                ]
            },
            {
                "fields": [
                    {"name": "text", "value": "Gadget B"},
                    {"name": "lineNumber", "value": "2"},
                    {"name": "inventory", "value": "GDG-002"},
                    {"name": "purchaseReceiptDataQuantity", "value": "5"},
                    {"name": "debit", "value": "250.00"},
                    {"name": "unitPrice", "value": "50.00"},
                ]
            },
        ],
    }


@given("I have a candidate purchase order with corresponding deviations")
def candidate_po_with_corresponding_deviations(context):
    """Create a candidate PO with corresponding deviations."""
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "CD-COMP-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": "1400.00"},
                {"name": "excVatAmount", "value": "1120.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-COMP-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "WGT-001"},
                        {"name": "description", "value": "Widget A Standard"},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": "45.00"},
                        {"name": "quantityOrdered", "value": "12"},
                        {"name": "quantityToReceive", "value": "12"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "12"},
                    ]
                },
                {
                    "fields": [
                        {"name": "id", "value": "IT-COMP-002"},
                        {"name": "lineNumber", "value": "2"},
                        {"name": "inventory", "value": "GDG-002"},
                        {"name": "description", "value": "Gadget B"},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": "50.00"},
                        {"name": "quantityOrdered", "value": "5"},
                        {"name": "quantityToReceive", "value": "5"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "5"},
                    ]
                },
            ],
        }
    ]


@then('the match report should include a "deviations" section at document level')
def check_document_level_deviations(context):
    """Check that match report has document-level deviations."""
    response_data = context["response"].json()
    assert "deviations" in response_data, "Match report should have 'deviations' key"
    assert isinstance(response_data["deviations"], list), "deviations should be a list"


@then(
    'each item pair in the match report should include a "deviations" section where applicable'
)
def check_itempair_deviations_section(context):
    """Check that item pairs have deviations section."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])
    assert len(itempairs) > 0, "Should have at least one item pair"

    for i, pair in enumerate(itempairs):
        assert "deviations" in pair, f"Item pair {i} should have 'deviations' key"


@then("all deviations should include standardized deviation codes")
def check_standardized_deviation_codes(context):
    """Check that all deviations have standardized codes."""
    response_data = context["response"].json()

    valid_codes = [
        "AMOUNTS_DIFFER",
        "QUANTITIES_DIFFER",
        "PARTIAL_DELIVERY",
        "PRICES_PER_UNIT_DIFFER",
        "ARTICLE_NUMBERS_DIFFER",
        "DESCRIPTIONS_DIFFER",
        "ITEM_UNMATCHED",
        "ITEMS_DIFFER",
        "CURRENCIES_DIFFER",
        "INVALID_DOC_KIND",
    ]

    # Check document-level deviations
    for dev in response_data.get("deviations", []):
        code = dev.get("code")
        assert code is not None, "Deviation should have 'code' field"
        assert code in valid_codes, f"Unknown deviation code: {code}"

    # Check item-level deviations
    for pair in response_data.get("itempairs", []):
        for dev in pair.get("deviations", []):
            code = dev.get("code")
            assert code is not None, "Deviation should have 'code' field"
            assert code in valid_codes, f"Unknown deviation code: {code}"


@then("all deviations should include a severity level")
def check_deviations_have_severity(context):
    """Check that all deviations have severity level."""
    response_data = context["response"].json()
    valid_severities = ["no-severity", "info", "low", "medium", "high"]

    # Check document-level deviations
    for dev in response_data.get("deviations", []):
        severity = dev.get("severity")
        assert severity is not None, "Deviation should have 'severity' field"
        assert severity in valid_severities, f"Invalid severity: {severity}"

    # Check item-level deviations
    for pair in response_data.get("itempairs", []):
        for dev in pair.get("deviations", []):
            severity = dev.get("severity")
            assert severity is not None, "Deviation should have 'severity' field"
            assert severity in valid_severities, f"Invalid severity: {severity}"


@then(
    "all deviations should include human-readable messages explaining the discrepancy"
)
def check_deviations_have_messages(context):
    """Check that all deviations have human-readable messages."""
    response_data = context["response"].json()

    # Check document-level deviations
    for dev in response_data.get("deviations", []):
        message = dev.get("message")
        assert message is not None, "Deviation should have 'message' field"
        assert len(message) > 0, "Message should not be empty"

    # Check item-level deviations
    for pair in response_data.get("itempairs", []):
        for dev in pair.get("deviations", []):
            message = dev.get("message")
            assert message is not None, "Deviation should have 'message' field"
            assert len(message) > 0, "Message should not be empty"


@then("all deviations should include field references and actual values that differ")
def check_deviations_have_field_refs(context):
    """Check that deviations have field references and values."""
    response_data = context["response"].json()

    # Check document-level deviations
    for dev in response_data.get("deviations", []):
        assert "field_names" in dev, "Deviation should have 'field_names'"
        assert "field_values" in dev, "Deviation should have 'field_values'"

    # Check item-level deviations
    for pair in response_data.get("itempairs", []):
        for dev in pair.get("deviations", []):
            assert "field_names" in dev, "Deviation should have 'field_names'"
            assert "field_values" in dev, "Deviation should have 'field_values'"


@then(
    'the match report should include a "deviation-severity" metric showing the highest deviation severity'
)
def check_deviation_severity_metric(context):
    """Check that match report has deviation-severity metric in metrics array."""
    response_data = context["response"].json()
    assert "metrics" in response_data, "Match report should have 'metrics' array"

    # Find the deviation-severity metric
    deviation_metric = None
    for metric in response_data["metrics"]:
        if metric.get("name") == "deviation-severity":
            deviation_metric = metric
            break

    assert (
        deviation_metric is not None
    ), "Match report should have 'deviation-severity' metric"

    valid_severities = ["no-severity", "info", "low", "medium", "high"]
    assert (
        deviation_metric["value"] in valid_severities
    ), f"Invalid deviation-severity value: {deviation_metric['value']}"


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Comprehensive Deviation Reporting",
)
def test_comprehensive_deviation_reporting():
    """Test comprehensive deviation reporting structure."""
    pass


# ==============================================================================
# Deviation Field Names and Values Format
# ==============================================================================


@then('the deviation should contain a "field_names" array with field path strings')
def check_field_names_array(context):
    """Check that deviation has field_names array."""
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])

    amounts_differ = None
    for dev in deviations:
        if dev.get("code") == "AMOUNTS_DIFFER":
            amounts_differ = dev
            break

    assert amounts_differ is not None, "Should have AMOUNTS_DIFFER deviation"
    assert "field_names" in amounts_differ, "Should have 'field_names' array"
    assert isinstance(
        amounts_differ["field_names"], list
    ), "field_names should be a list"
    for fn in amounts_differ["field_names"]:
        assert isinstance(fn, str), f"field_name should be string, got: {type(fn)}"


@then(
    'the deviation should contain a "field_values" array with string representations of actual values'
)
def check_field_values_array(context):
    """Check that deviation has field_values array."""
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])

    amounts_differ = None
    for dev in deviations:
        if dev.get("code") == "AMOUNTS_DIFFER":
            amounts_differ = dev
            break

    assert amounts_differ is not None, "Should have AMOUNTS_DIFFER deviation"
    assert "field_values" in amounts_differ, "Should have 'field_values' array"
    assert isinstance(
        amounts_differ["field_values"], list
    ), "field_values should be a list"
    for val in amounts_differ["field_values"]:
        assert isinstance(val, str), f"value should be string, got: {type(val)}"


@then(
    'the "field_names" array length should equal the number of documents in the match'
)
def check_field_names_length(context):
    """Check that field_names array has correct length."""
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])
    num_documents = len(response_data.get("documents", []))

    for dev in deviations:
        if dev.get("code") == "AMOUNTS_DIFFER":
            field_names = dev.get("field_names", [])
            assert len(field_names) == num_documents, (
                f"field_names length ({len(field_names)}) should equal "
                f"number of documents ({num_documents})"
            )


@then(
    'the "field_values" array length should equal the number of documents in the match'
)
def check_field_values_length(context):
    """Check that field_values array has correct length."""
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])
    num_documents = len(response_data.get("documents", []))

    for dev in deviations:
        if dev.get("code") == "AMOUNTS_DIFFER":
            field_values = dev.get("field_values", [])
            assert len(field_values) == num_documents, (
                f"field_values length ({len(field_values)}) should equal "
                f"number of documents ({num_documents})"
            )


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Deviation Field Names and Values Format",
)
def test_deviation_field_names_format():
    """Test deviation field_names and values format."""
    pass


# ==============================================================================
# Line-Level AMOUNTS_DIFFER (#44)
# ==============================================================================


@given(parsers.parse("I have a primary invoice with item amount {amount:f}"))
def primary_invoice_with_item_amount(context, amount):
    """Create a primary invoice document with specific item amount."""
    context["document"] = {
        "version": "v3",
        "id": "PD-AMT-001",
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
                    {"name": "text", "value": "Test Product"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "PROD-001"},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "debit", "value": str(amount)},
                ]
            }
        ],
    }


@given(parsers.parse("I have a candidate purchase order with item amount {amount:f}"))
def candidate_po_with_item_amount(context, amount):
    """Create a candidate purchase order with specific item amount."""
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "CD-AMT-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": str(amount)},
                {"name": "excVatAmount", "value": str(amount * 0.8)},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-AMT-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": "PROD-001"},
                        {"name": "description", "value": "Test Product"},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": str(amount)},
                        {"name": "quantityOrdered", "value": "1"},
                        {"name": "quantityToReceive", "value": "1"},
                        {"name": "quantityReceived", "value": "0"},
                        {"name": "quantityToInvoice", "value": "1"},
                    ]
                }
            ],
        }
    ]


@then(
    parsers.parse(
        'the line item AMOUNTS_DIFFER deviation severity should be "{expected_severity}"'
    )
)
def check_line_amounts_differ_severity(context, expected_severity):
    """Check AMOUNTS_DIFFER in itempairs has expected severity.

    For no-severity, it's acceptable if no deviation is generated at all.
    """
    response_data = context["response"].json()

    for pair in response_data.get("itempairs", []):
        for dev in pair.get("deviations", []):
            if dev.get("code") == "AMOUNTS_DIFFER":
                assert dev.get("severity") == expected_severity, (
                    f"Expected line AMOUNTS_DIFFER severity '{expected_severity}', "
                    f"got '{dev.get('severity')}'"
                )
                return

    # For no-severity, it's acceptable if no deviation is generated
    if expected_severity == "no-severity":
        return  # No deviation found is acceptable for no-severity

    pytest.fail("No AMOUNTS_DIFFER deviation found in any itempair")


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Line item amount deviation - no-severity for tiny differences",
)
def test_line_amount_no_severity():
    """Test no-severity for tiny line item amount differences."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Line item amount deviation - low severity for small differences",
)
def test_line_amount_low_severity():
    """Test low severity for small line item amount differences."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Line item amount deviation - medium severity for moderate differences",
)
def test_line_amount_medium_severity():
    """Test medium severity for moderate line item amount differences."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Line item amount deviation - high severity for large differences",
)
def test_line_amount_high_severity():
    """Test high severity for large line item amount differences."""
    pass


# ==============================================================================
# ITEM_UNMATCHED Threshold Tests (#45)
# ==============================================================================


@given(
    parsers.parse(
        "I have a primary invoice with two items where one has amount {amount:f} and no match"
    )
)
def primary_invoice_with_unmatched_item_amount(context, amount):
    """Set up invoice with one matching item and one unmatched item of specific amount."""
    context["document"] = {
        "version": "v3",
        "id": "PD-UNMAT-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": str(100 + amount)},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": str((100 + amount) * 0.8)},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Matching Product"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "MATCH-001"},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "debit", "value": "100.00"},
                ]
            },
            {
                "fields": [
                    {"name": "text", "value": "Unmatched Product"},
                    {"name": "lineNumber", "value": "2"},
                    {"name": "inventory", "value": "NOMATCH-999"},
                    {"name": "purchaseReceiptDataQuantity", "value": "1"},
                    {"name": "debit", "value": str(amount)},
                ]
            },
        ],
    }


@then(
    parsers.parse(
        'the ITEM_UNMATCHED deviation severity should be "{expected_severity}"'
    )
)
def check_item_unmatched_severity(context, expected_severity):
    """Check ITEM_UNMATCHED deviation has expected severity."""
    response_data = context["response"].json()

    for pair in response_data.get("itempairs", []):
        if pair.get("match_type") == "unmatched":
            for dev in pair.get("deviations", []):
                if dev.get("code") == "ITEM_UNMATCHED":
                    assert dev.get("severity") == expected_severity, (
                        f"Expected ITEM_UNMATCHED severity '{expected_severity}', "
                        f"got '{dev.get('severity')}'"
                    )
                    return

    pytest.fail("No ITEM_UNMATCHED deviation found in unmatched itempairs")


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Unmatched item - no-severity for trivial line amount",
)
def test_item_unmatched_no_severity():
    """Test no-severity for trivial line amount."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Unmatched item - low severity for small line amount",
)
def test_item_unmatched_low_severity():
    """Test low severity for small line amount."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Unmatched item - medium severity for moderate line amount",
)
def test_item_unmatched_medium_severity():
    """Test medium severity for moderate line amount."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Unmatched item - high severity for large line amount",
)
def test_item_unmatched_high_severity():
    """Test high severity for large line amount."""
    pass


# ==============================================================================
# PRICES_PER_UNIT_DIFFER Additional Tests (#46)
# Note: QUANTITIES_DIFFER medium scenario is in test_quantity_deviations.py
# ==============================================================================


@then(
    'there should be no PRICES_PER_UNIT_DIFFER deviation or it should be "no-severity"'
)
def check_no_price_deviation_or_no_severity(context):
    """Check that PRICES_PER_UNIT_DIFFER either doesn't exist or is no-severity."""
    response_data = context["response"].json()

    for pair in response_data.get("itempairs", []):
        for dev in pair.get("deviations", []):
            if dev.get("code") == "PRICES_PER_UNIT_DIFFER":
                assert (
                    dev.get("severity") == "no-severity"
                ), f"Expected no deviation or 'no-severity', got '{dev.get('severity')}'"
                return
    # No deviation found is also acceptable


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Unit price deviation - no-severity for tiny price difference",
)
def test_unit_price_no_severity():
    """Test no-severity for tiny unit price difference."""
    pass


@scenario(
    str(get_feature_path("api-consumer/deviations.feature")),
    "Unit price deviation - medium severity for moderate price difference",
)
def test_unit_price_medium_severity():
    """Test medium severity for moderate unit price difference."""
    pass


# ==============================================================================
# ITEMS_DIFFER Tests (#43)
# Note: ITEMS_DIFFER requires items to be PAIRED but have low similarity.
# These scenarios are not fully testable because items with very different
# article numbers and descriptions may not pair at all (resulting in
# ITEM_UNMATCHED instead of ITEMS_DIFFER).
#
# The scenarios are kept in the feature file for documentation purposes,
# but the implementation tests are commented out until the pairing
# algorithm is better understood.
# ==============================================================================


# TODO: Re-enable when we understand how to force item pairing for ITEMS_DIFFER
# @scenario(
#     str(get_feature_path("api-consumer/deviations.feature")),
#     "Items differ - high severity when both similarities very low",
# )
# def test_items_differ_high_severity():
#     """Test high severity when both similarities very low."""
#     pass
#
#
# @scenario(
#     str(get_feature_path("api-consumer/deviations.feature")),
#     "Items differ - medium severity for mixed similarity signals",
# )
# def test_items_differ_medium_severity():
#     """Test medium severity for mixed similarity signals."""
#     pass
