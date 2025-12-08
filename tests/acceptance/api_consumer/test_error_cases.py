"""
BDD tests for error_cases.feature scenarios - Document Matching API Error Cases.
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
    str(get_feature_path("api-consumer/error_cases.feature")),
    "No-Match Scenario",
)
def test_no_match_scenario():
    """Test match report with certainty metrics for non-matching documents."""
    pass


@scenario(
    str(get_feature_path("api-consumer/error_cases.feature")),
    "Empty Candidate List",
)
def test_empty_candidate_list():
    """Test empty candidate list returns appropriate response."""
    pass


@scenario(
    str(get_feature_path("api-consumer/error_cases.feature")),
    "Missing Primary Document",
)
def test_missing_primary_document():
    """Test missing primary document returns 400 error."""
    pass


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/error_cases.feature")),
    "Invalid Document Format",
)
def test_invalid_document_format():
    """Test invalid document format returns 400 error.

    NOTE: Currently marked as WIP because the API does not validate document
    structure - accepts any dict and attempts processing.
    """
    pass


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/error_cases.feature")),
    "Invalid Document Kind",
)
def test_invalid_document_kind():
    """Test invalid document kind returns 400 error.

    NOTE: Currently marked as WIP because the API does not validate document
    kind enum - accepts any kind value.
    """
    pass


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/error_cases.feature")),
    "Request Payload Too Large",
)
def test_payload_too_large():
    """Test payload too large returns 413 error.

    NOTE: Currently marked as WIP because the API does not enforce
    candidate document limits.
    """
    pass


# ==============================================================================
# Helper functions
# ==============================================================================


def create_invoice_document(
    doc_id: str = "INV-001",
    supplier_id: str = "SUP-001",
    amount: str = "1000.00",
    order_ref: str = "PO-12345",
) -> dict:
    """Create a standard invoice document."""
    return {
        "version": "v3",
        "id": doc_id,
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": supplier_id},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0001"},
            {"name": "incVatAmount", "value": amount},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": amount},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": order_ref},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Product A"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "debit", "value": amount},
                    {"name": "articleNumber", "value": "ART-001"},
                ]
            }
        ],
    }


def create_po_document(
    doc_id: str = "PO-001",
    supplier_id: str = "SUP-001",
    amount: str = "1000.00",
    order_number: str = "PO-12345",
) -> dict:
    """Create a standard purchase order document."""
    return {
        "version": "v3",
        "id": doc_id,
        "kind": "purchase-order",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": supplier_id},
            {"name": "orderDate", "value": "2025-06-20"},
            {"name": "orderNumber", "value": order_number},
            {"name": "incVatAmount", "value": amount},
            {"name": "currencyCode", "value": "USD"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "id", "value": "IT-001"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "ART-001"},
                    {"name": "description", "value": "Product A"},
                    {"name": "unitAmount", "value": amount},
                    {"name": "quantityOrdered", "value": "1.00"},
                ]
            }
        ],
    }


def create_non_matching_po(
    doc_id: str = "PO-DIFF-001",
    supplier_id: str = "DIFFERENT-SUPPLIER-999",
) -> dict:
    """Create a PO that won't match the invoice."""
    return {
        "version": "v3",
        "id": doc_id,
        "kind": "purchase-order",
        "site": "other-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": supplier_id},
            {"name": "orderDate", "value": "2024-01-15"},
            {"name": "orderNumber", "value": "COMPLETELY-DIFFERENT-REF"},
            {"name": "incVatAmount", "value": "9999.99"},
            {"name": "currencyCode", "value": "EUR"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "id", "value": "IT-DIFF"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "DIFF-ART-999"},
                    {"name": "description", "value": "Completely Different Product"},
                    {"name": "unitAmount", "value": "9999.99"},
                    {"name": "quantityOrdered", "value": "99.00"},
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


@given("I have a primary invoice document")
def primary_invoice(context):
    """Create a primary invoice document."""
    context["document"] = create_invoice_document()


@given("I have a candidate purchase order document that should not match")
def candidate_non_matching_po(context):
    """Create a candidate PO that won't match."""
    context["candidate-documents"] = [create_non_matching_po()]


@given("I have no candidate documents")
def no_candidate_documents(context):
    """Set empty candidate documents list."""
    context["candidate-documents"] = []


@given("I have no primary document")
def no_primary_document(context):
    """Mark that we have no primary document."""
    context["document"] = None


@given("I have candidate purchase order documents")
def candidate_pos(context):
    """Create candidate PO documents."""
    context["candidate-documents"] = [create_po_document()]


@given("I have a primary document with invalid format")
def primary_invalid_format(context):
    """Create a primary document with invalid format (missing required fields)."""
    context["document"] = {
        "invalid": "document",
        "missing": "required fields",
    }


@given("I have valid candidate documents")
def valid_candidates(context):
    """Create valid candidate documents."""
    context["candidate-documents"] = [create_po_document()]


@given("I have a primary document with unsupported kind")
def primary_unsupported_kind(context):
    """Create a primary document with unsupported kind."""
    context["document"] = {
        "version": "v3",
        "id": "DOC-001",
        "kind": "unsupported-document-type",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "SUP-001"},
        ],
        "items": [],
    }


@given("I have a primary document")
def primary_document(context):
    """Create a primary document."""
    context["document"] = create_invoice_document()


@given("I have too many candidate documents exceeding the limit")
def too_many_candidates(context):
    """Create too many candidate documents."""
    # Create many candidates to exceed payload limits
    context["candidate-documents"] = [
        create_po_document(doc_id=f"PO-{i:05d}") for i in range(1000)
    ]


# ==============================================================================
# When step definitions
# ==============================================================================


@when('I send a POST request to "/" with the primary document and candidate document')
def send_post_with_single_candidate(client, context):
    """Send POST request with primary document and single candidate."""
    payload = {
        "document": context["document"],
        "candidate-documents": context.get("candidate-documents", []),
    }
    context["response"] = client.post("/", json=payload)


@when(
    'I send a POST request to "/" with the primary document and an empty list of candidate documents'
)
def send_post_with_empty_candidates(client, context):
    """Send POST request with empty candidate list."""
    payload = {
        "document": context["document"],
        "candidate-documents": [],
    }
    context["response"] = client.post("/", json=payload)


@when(
    'I send a POST request to "/" with a missing primary document and candidate documents'
)
def send_post_without_primary(client, context):
    """Send POST request without primary document."""
    payload = {
        "candidate-documents": context.get("candidate-documents", []),
    }
    context["response"] = client.post("/", json=payload)


@when('I send a POST request to "/" with the primary document and candidate documents')
def send_post_with_candidates(client, context):
    """Send POST request with primary document and candidates."""
    payload = {
        "document": context["document"],
        "candidate-documents": context.get("candidate-documents", []),
    }
    context["response"] = client.post("/", json=payload)


@when(
    'I send a POST request to "/" with the primary document and excessive candidate documents'
)
def send_post_with_excessive_candidates(client, context):
    """Send POST request with too many candidates."""
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
    assert context["response"].status_code == status_code, (
        f"Expected status {status_code}, got {context['response'].status_code}. "
        f"Response: {context['response'].text[:500]}"
    )


@then("the response body should contain a match report")
def check_match_report(context):
    """Check that response contains a match report."""
    response_data = context["response"].json()
    assert isinstance(response_data, dict), "Response should be a dict"


@then("the match report should include certainty metrics")
def check_certainty_metrics(context):
    """Check that match report includes certainty metrics."""
    response_data = context["response"].json()
    metrics = response_data.get("metrics", [])
    assert len(metrics) > 0, "Response should have metrics"
    # Look for certainty metric
    certainty_metrics = [m for m in metrics if "certainty" in m.get("name", "").lower()]
    assert len(certainty_metrics) > 0, f"Expected certainty metrics, got: {metrics}"


@then("the response body should indicate no matches were found")
def check_no_matches_found(context):
    """Check that response indicates no matches."""
    response_data = context["response"].json()
    if isinstance(response_data, list):
        assert len(response_data) == 0, "Expected empty list for no matches"
    else:
        labels = response_data.get("labels", [])
        assert "no-match" in labels, f"Expected 'no-match' in labels, got {labels}"


@then("the response should comply with the API schema")
def check_api_schema_compliance(context):
    """Check that response complies with API schema."""
    response_data = context["response"].json()
    # V3 response should have version field
    if isinstance(response_data, dict):
        assert "version" in response_data or "labels" in response_data


@then("the response body should contain a clear error message")
def check_error_message(context):
    """Check that response contains an error message."""
    response_data = context["response"].json()
    # FastAPI validation errors have "detail" field
    assert (
        "detail" in response_data
    ), f"Expected 'detail' in error response: {response_data}"


@then("the error message should indicate the missing primary document")
def check_missing_document_error(context):
    """Check that error message mentions missing document."""
    response_data = context["response"].json()
    detail = response_data.get("detail", "")
    if isinstance(detail, list):
        # Pydantic validation errors
        detail_str = str(detail)
    else:
        detail_str = str(detail)
    # Check for indication of missing document field
    assert (
        "document" in detail_str.lower() or "field" in detail_str.lower()
    ), f"Expected error to mention document, got: {detail_str}"


@then("the error message should indicate the format issue")
def check_format_error(context):
    """Check that error message mentions format issue."""
    response_data = context["response"].json()
    detail = response_data.get("detail", "")
    if isinstance(detail, list):
        detail_str = str(detail)
    else:
        detail_str = str(detail)
    # Check for indication of format/validation issue
    assert any(
        term in detail_str.lower()
        for term in ["validation", "field", "required", "missing", "type", "invalid"]
    ), f"Expected format error indication, got: {detail_str}"


@then("the error message should indicate the invalid document kind")
def check_invalid_kind_error(context):
    """Check that error message mentions invalid kind."""
    response_data = context["response"].json()
    detail = response_data.get("detail", "")
    if isinstance(detail, list):
        detail_str = str(detail)
    else:
        detail_str = str(detail)
    # Check for indication of kind issue
    assert any(
        term in detail_str.lower()
        for term in ["kind", "type", "unsupported", "invalid", "enum"]
    ), f"Expected kind error indication, got: {detail_str}"


@then("the error message should indicate the payload size issue")
def check_payload_size_error(context):
    """Check that error message mentions payload size."""
    response_data = context["response"].json()
    detail = response_data.get("detail", "")
    detail_str = str(detail)
    # Check for indication of size issue
    assert any(
        term in detail_str.lower()
        for term in ["large", "size", "limit", "exceeded", "too many", "payload"]
    ), f"Expected payload size error indication, got: {detail_str}"
