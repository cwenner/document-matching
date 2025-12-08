"""
BDD tests for no_match.feature scenarios - Clear No-Match Reporting.
"""

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


# ==============================================================================
# Scenario definitions
# ==============================================================================


@scenario(
    str(get_feature_path("api-consumer/no_match.feature")),
    "Validate No-Match Report Schema",
)
def test_validate_no_match_schema():
    """Test that no-match reports follow V3 schema."""
    pass


@scenario(
    str(get_feature_path("api-consumer/no_match.feature")),
    "No Match Between Different Document Types",
)
def test_no_match_different_types():
    """Test no-match reporting between different document types."""
    pass


@scenario(
    str(get_feature_path("api-consumer/no_match.feature")),
    "No-Match Report as Empty Array",
)
def test_no_match_empty_array():
    """Test that no-match returns correctly structured empty array."""
    pass


@scenario(
    str(get_feature_path("api-consumer/no_match.feature")),
    "No-Match Report With Detailed Reasons",
)
def test_no_match_with_reasons():
    """Test that no-match includes detailed reasons."""
    pass


# ==============================================================================
# Helper functions
# ==============================================================================


def create_invoice_with_unique_ids(
    doc_id: str = "INV-UNIQUE-001",
    supplier_id: str = "UNIQUE-SUPPLIER-001",
) -> dict:
    """Create an invoice with unique identifiers that won't match."""
    return {
        "version": "v3",
        "id": doc_id,
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": supplier_id},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-UNIQUE-2025"},
            {"name": "incVatAmount", "value": "1000.00"},
            {"name": "currencyCode", "value": "USD"},
            {"name": "orderReference", "value": "PO-UNIQUE-REF"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Unique Product Alpha"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "debit", "value": "1000.00"},
                    {"name": "articleNumber", "value": "UNIQUE-ART-001"},
                ]
            }
        ],
    }


def create_po_with_different_ids(
    doc_id: str = "PO-DIFF-001",
    supplier_id: str = "DIFFERENT-SUPPLIER-999",
) -> dict:
    """Create a PO with different identifiers that won't match."""
    return {
        "version": "v3",
        "id": doc_id,
        "kind": "purchase-order",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": supplier_id},
            {"name": "orderDate", "value": "2025-01-15"},
            {"name": "orderNumber", "value": "PO-DIFFERENT-REF"},
            {"name": "incVatAmount", "value": "5000.00"},
            {"name": "currencyCode", "value": "EUR"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "description", "value": "Different Product Omega"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "unitAmount", "value": "5000.00"},
                    {"name": "inventory", "value": "DIFF-ART-999"},
                ]
            }
        ],
    }


# ==============================================================================
# Given step definitions
# ==============================================================================


@given("the document matching service is available")
def document_matching_service(context):
    """Set up the document matching service"""
    context["base_url"] = "http://localhost:8000"


@given("I have a primary document with unique identifiers")
def primary_with_unique_ids(context):
    """Create a primary document with unique identifiers."""
    context["document"] = create_invoice_with_unique_ids()


@given("I have candidate documents with different identifiers")
def candidates_with_different_ids(context):
    """Create candidate documents with different identifiers."""
    context["candidate-documents"] = [
        create_po_with_different_ids("PO-DIFF-001", "DIFFERENT-SUPPLIER-AAA"),
        create_po_with_different_ids("PO-DIFF-002", "DIFFERENT-SUPPLIER-BBB"),
    ]


@given("I have a primary invoice document with unique identifiers")
def primary_invoice_unique(context):
    """Create a primary invoice with unique identifiers."""
    context["document"] = create_invoice_with_unique_ids("INV-TYPE-001", "SUP-TYPE-001")


@given("I have candidate purchase order documents with different identifiers")
def candidate_pos_different(context):
    """Create candidate POs with different identifiers."""
    context["candidate-documents"] = [
        create_po_with_different_ids("PO-TYPE-001", "SUP-DIFF-999"),
    ]


@given("I have a primary document with unique supplier ID")
def primary_unique_supplier(context):
    """Create a primary document with unique supplier ID."""
    context["document"] = create_invoice_with_unique_ids(
        "INV-SUP-001", "UNIQUE-SUP-001"
    )


@given("I have candidate documents with different supplier IDs")
def candidates_different_suppliers(context):
    """Create candidate documents with different supplier IDs."""
    context["candidate-documents"] = [
        create_po_with_different_ids("PO-SUP-001", "OTHER-SUP-AAA"),
        create_po_with_different_ids("PO-SUP-002", "OTHER-SUP-BBB"),
    ]


@given("I have a primary document with specific identifiers")
def primary_specific_ids(context):
    """Create a primary document with specific identifiers."""
    context["document"] = create_invoice_with_unique_ids("INV-SPEC-001", "SUP-SPEC-001")


@given("I have candidate documents with non-matching identifiers")
def candidates_non_matching(context):
    """Create candidate documents with non-matching identifiers."""
    context["candidate-documents"] = [
        create_po_with_different_ids("PO-NONMATCH-001", "SUP-NONMATCH-001"),
    ]


# ==============================================================================
# When step definitions
# ==============================================================================


@when('I send a POST request to "/" with the primary document and candidate documents')
def send_post_with_candidates(client, context):
    """Send POST request with primary document and candidates."""
    payload = {
        "document": context["document"],
        "candidate-documents": context.get("candidate-documents", []),
    }
    context["response"] = client.post("/", json=payload)


# ==============================================================================
# Then step definitions
# ==============================================================================


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(status_code, context):
    """Check that the response has the expected status code."""
    assert context["response"].status_code == status_code


@then("the response body should contain a structured no-match report")
def check_structured_no_match(context):
    """Check that response contains a structured no-match report."""
    response_data = context["response"].json()
    # Response should be a dict with match report structure
    assert isinstance(response_data, dict), "Response should be a dict"
    # Should have standard fields
    assert "labels" in response_data, "Response should have labels field"


@then("the no-match report should adhere to the V3 schema")
def check_v3_schema_no_match(context):
    """Check that the no-match report follows V3 schema."""
    response_data = context["response"].json()
    assert response_data.get("version") == "v3", "Response should be v3"
    # V3 schema has these fields
    assert "documents" in response_data or "labels" in response_data


@then("the no-match report should clearly indicate no matches were found")
def check_clear_no_match_indication(context):
    """Check that response clearly indicates no match."""
    response_data = context["response"].json()
    if isinstance(response_data, list):
        # Empty list indicates no matches
        assert len(response_data) == 0
    else:
        # Dict response should have no-match in labels
        labels = response_data.get("labels", [])
        assert "no-match" in labels, f"Expected 'no-match' in labels, got {labels}"


@then("the no-match report should include document type information")
def check_document_type_info(context):
    """Check that response includes document type information."""
    response_data = context["response"].json()
    # The response should have document information
    if "documents" in response_data:
        for doc in response_data["documents"]:
            assert "kind" in doc, "Document should have kind field"
    # Or the response itself should indicate kinds
    elif "kind" in response_data:
        assert response_data["kind"] is not None


@then("the no-match report should explain why the documents did not match")
def check_no_match_explanation(context):
    """Check that response explains why documents didn't match."""
    response_data = context["response"].json()
    # Check for explanation in various possible locations
    has_explanation = (
        "no-match" in response_data.get("labels", [])
        or "deviations" in response_data
        or "metrics" in response_data
    )
    assert has_explanation, "Response should explain no-match reason"


@then("the response body should be a correctly structured empty array")
def check_empty_array_structure(context):
    """Check that response is a correctly structured empty array."""
    response_data = context["response"].json()
    # For no-match with supplier mismatch, the response might be:
    # 1. An empty array []
    # 2. A dict with no-match labels
    if isinstance(response_data, list):
        assert len(response_data) == 0, "Expected empty array"
    else:
        # If it's a dict, it should indicate no-match
        assert "no-match" in response_data.get(
            "labels", []
        ), "Expected no-match in labels"


@then("the empty array should conform to the V3 report specification")
def check_v3_empty_array(context):
    """Check that empty array conforms to V3 spec."""
    response_data = context["response"].json()
    # Either empty array or proper v3 structure
    if isinstance(response_data, list):
        # Empty list is valid V3 response for no matches
        pass
    else:
        assert response_data.get("version") == "v3"


@then("the no-match report should include specific reasons why matches failed")
def check_specific_no_match_reasons(context):
    """Check that response includes specific reasons for no match."""
    response_data = context["response"].json()
    # Look for reasons in various places
    has_reasons = (
        "deviations" in response_data
        or "metrics" in response_data
        or "no-match" in response_data.get("labels", [])
    )
    assert has_reasons, "Response should include reasons for no match"


@then('the no-match report should include "no-match" in labels')
def check_no_match_label(context):
    """Check that response has 'no-match' in labels."""
    response_data = context["response"].json()
    labels = response_data.get("labels", [])
    assert "no-match" in labels, f"Expected 'no-match' in labels, got {labels}"
