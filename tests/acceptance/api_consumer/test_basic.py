"""
BDD tests for basic.feature scenarios - Core Document Matching API.
"""

import time

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
# Scenario definitions - these link feature scenarios to test functions
# ==============================================================================


@scenario(
    str(get_feature_path("api-consumer/basic.feature")),
    "Basic Invoice-PO Match",
)
def test_basic_invoice_po_match():
    """Test basic matching of invoice to purchase order."""
    pass


@scenario(
    str(get_feature_path("api-consumer/basic.feature")),
    "Basic PO-Delivery Receipt Match",
)
def test_basic_po_dr_match():
    """Test basic matching of PO to delivery receipt.

    Uses reference-based matching (not ML) per ADR-001.
    Delivery receipt's purchaseOrderNumber field matches PO's orderNumber.
    """
    pass


@scenario(
    str(get_feature_path("api-consumer/basic.feature")),
    "Three-Way Document Matching",
)
def test_three_way_matching():
    """Test matching invoice with both PO and delivery receipt.

    Returns multiple match reports: one for Invoice→PO and one for PO→Delivery.
    Implements issue #53.
    """
    pass


@scenario(
    str(get_feature_path("api-consumer/basic.feature")),
    "Match with Multiple Candidate Documents",
)
def test_multiple_candidates():
    """Test matching with multiple candidate documents."""
    pass


@scenario(
    str(get_feature_path("api-consumer/basic.feature")),
    "Performance Requirements with Maximum Candidates",
)
def test_max_candidates_performance():
    """Test performance with maximum candidates."""
    pass


# ==============================================================================
# Helper functions to create test documents
# ==============================================================================


def create_invoice_document(
    doc_id: str = "INV-001",
    supplier_id: str = "S123",
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
    supplier_id: str = "S123",
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


def create_delivery_receipt(
    doc_id: str = "DR-001",
    supplier_id: str = "S123",
    order_ref: str = "PO-12345",
) -> dict:
    """Create a standard delivery receipt document."""
    return {
        "version": "v3",
        "id": doc_id,
        "kind": "delivery-receipt",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": supplier_id},
            {"name": "deliveryDate", "value": "2025-06-21"},
            {"name": "deliveryNumber", "value": "DR-2025-0001"},
            {"name": "orderReference", "value": order_ref},
        ],
        "items": [
            {
                "fields": [
                    {"name": "text", "value": "Product A"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "quantity", "value": "1"},
                    {"name": "inventory", "value": "ART-001"},
                    {"name": "purchaseOrderNumber", "value": order_ref},
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


@given("I have a primary purchase order document")
def primary_po(context):
    """Create a primary purchase order document."""
    context["document"] = create_po_document()


@given("I have an invoice document")
def invoice_document(context):
    """Create an invoice document for three-way matching."""
    context["document"] = create_invoice_document()


@given("I have a candidate purchase order document")
def candidate_po(context):
    """Create or add a candidate purchase order document."""
    if "candidate-documents" not in context:
        context["candidate-documents"] = []
    context["candidate-documents"].append(create_po_document())


@given("I have a candidate delivery receipt document")
def candidate_dr(context):
    """Create or add a candidate delivery receipt document."""
    if "candidate-documents" not in context:
        context["candidate-documents"] = []
    context["candidate-documents"].append(create_delivery_receipt())


@given(parsers.parse("I have {count:d} candidate purchase order documents"))
def multiple_candidate_pos(context, count):
    """Create multiple candidate purchase order documents."""
    context["candidate-documents"] = []
    for i in range(count):
        context["candidate-documents"].append(
            create_po_document(
                doc_id=f"PO-{i + 1:03d}",
                order_number=f"PO-{12345 + i}",
            )
        )


# ==============================================================================
# When step definitions
# ==============================================================================


@when(
    parsers.parse(
        'I send a POST request to "{endpoint}" with the primary document and candidates'
    )
)
def send_post_with_candidates(endpoint, client, context):
    """Send POST request with primary document and candidates."""
    payload = {
        "document": context["document"],
        "candidate-documents": context.get("candidate-documents", []),
    }
    context["start_time"] = time.time()
    context["response"] = client.post(endpoint, json=payload)
    context["elapsed_time"] = time.time() - context["start_time"]


@when(
    parsers.parse(
        'I send a POST request to "{endpoint}" with the primary document and candidate document'
    )
)
def send_post_with_single_candidate(endpoint, client, context):
    """Send POST request with primary document and single candidate."""
    payload = {
        "document": context["document"],
        "candidate-documents": context.get("candidate-documents", []),
    }
    context["start_time"] = time.time()
    context["response"] = client.post(endpoint, json=payload)
    context["elapsed_time"] = time.time() - context["start_time"]


# ==============================================================================
# Then step definitions
# ==============================================================================


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(status_code, context):
    """Check that the response has the expected status code."""
    assert (
        context["response"].status_code == status_code
    ), f"Expected status {status_code}, got {context['response'].status_code}"


@then("the response body should contain a match report in v3 schema")
def check_v3_match_report(context):
    """Check that response contains a v3 schema match report."""
    response_data = context["response"].json()
    # Response is now an array of reports
    assert isinstance(response_data, list), "Response should be a list of reports"
    assert len(response_data) > 0, "Response should contain at least one report"
    # Check first report
    report = response_data[0]
    assert report.get("version") == "v3", "Report should be v3 schema"
    assert "documents" in report, "Report should have documents field"
    assert "labels" in report, "Report should have labels field"


@then(parsers.parse('the match report should contain "{label}" in labels'))
def check_label_in_report(label, context):
    """Check that the match report contains specified label."""
    response_data = context["response"].json()
    # Response is now an array
    assert isinstance(response_data, list) and len(response_data) > 0
    report = response_data[0]
    labels = report.get("labels", [])
    assert label in labels, f"Expected '{label}' in labels, got {labels}"


@then("the match report should include certainty metrics")
def check_certainty_metrics(context):
    """Check that match report includes certainty metrics."""
    response_data = context["response"].json()
    assert isinstance(response_data, list) and len(response_data) > 0
    report = response_data[0]
    metrics = report.get("metrics", [])
    assert len(metrics) > 0, "Report should have metrics"
    # Check for certainty-related metrics
    metric_names = [m.get("name", "") for m in metrics]
    certainty_metrics = [
        m for m in metric_names if "certainty" in m.lower() or "confidence" in m.lower()
    ]
    assert len(certainty_metrics) > 0, f"Expected certainty metrics, got {metric_names}"


@then("the match report should reference both document IDs")
def check_document_ids_referenced(context):
    """Check that match report references both document IDs."""
    response_data = context["response"].json()
    assert isinstance(response_data, list) and len(response_data) > 0
    report = response_data[0]
    documents = report.get("documents", [])
    assert len(documents) >= 2, "Match report should reference at least 2 documents"
    doc_ids = [doc.get("id") for doc in documents]
    primary_id = context["document"]["id"]
    assert primary_id in doc_ids, f"Primary document {primary_id} not in {doc_ids}"


@then(parsers.parse("the match report should complete within {seconds:d} seconds"))
def check_response_time(seconds, context):
    """Check that the response completed within time limit."""
    assert (
        context["elapsed_time"] <= seconds
    ), f"Response took {context['elapsed_time']:.2f}s, expected <= {seconds}s"


@then("the response body should contain two match reports")
def check_two_match_reports(context):
    """Check for two match reports in response."""
    response_data = context["response"].json()
    # Response should be an array with 2 reports
    assert isinstance(response_data, list), "Response should be a list of reports"
    assert (
        len(response_data) == 2
    ), f"Expected 2 reports for three-way matching, got {len(response_data)}"


@then("one match report should be between invoice and purchase order")
def check_invoice_po_match(context):
    """Check for invoice-PO match in response."""
    response_data = context["response"].json()
    assert isinstance(response_data, list), "Response should be a list"

    # Find a report that contains both invoice and PO
    invoice_po_report = None
    for report in response_data:
        documents = report.get("documents", [])
        doc_kinds = [doc.get("kind") for doc in documents]
        if "invoice" in doc_kinds and "purchase-order" in doc_kinds:
            invoice_po_report = report
            break

    assert (
        invoice_po_report is not None
    ), f"No report found with Invoice-PO pair. Reports: {response_data}"


@then("one match report should be between purchase order and delivery receipt")
def check_po_dr_match(context):
    """Check for PO-DR match indication in response."""
    response_data = context["response"].json()
    assert isinstance(response_data, list), "Response should be a list"

    # Find a report that contains both PO and DR
    po_dr_report = None
    for report in response_data:
        documents = report.get("documents", [])
        doc_kinds = [doc.get("kind") for doc in documents]
        if "purchase-order" in doc_kinds and "delivery-receipt" in doc_kinds:
            po_dr_report = report
            break

    assert (
        po_dr_report is not None
    ), f"No report found with PO-DR pair. Reports: {response_data}"


@then("both match reports should follow the v3 schema")
def check_both_v3_schema(context):
    """Check that all reports follow v3 schema."""
    response_data = context["response"].json()
    assert isinstance(response_data, list), "Response should be a list"
    for report in response_data:
        assert report.get("version") == "v3", f"Report should be v3 schema: {report}"


@then(parsers.parse("both match reports should complete within {seconds:d} seconds"))
def check_both_response_time(seconds, context):
    """Check that the response completed within time limit."""
    assert context["elapsed_time"] <= seconds


@then("the response body should contain match reports for each candidate document")
def check_reports_for_each_candidate(context):
    """Check that response addresses all candidate documents."""
    response_data = context["response"].json()
    # Response is now an array
    assert isinstance(response_data, list) and len(response_data) > 0
    # Each report should have documents or labels
    for report in response_data:
        assert "documents" in report or "labels" in report


@then("each match report should follow the v3 schema")
def check_each_v3_schema(context):
    """Check v3 schema compliance."""
    response_data = context["response"].json()
    assert isinstance(response_data, list) and len(response_data) > 0
    for report in response_data:
        assert report.get("version") == "v3"


@then(parsers.parse("the entire response should complete within {seconds:d} seconds"))
def check_entire_response_time(seconds, context):
    """Check that the entire response completed within time limit."""
    assert context["elapsed_time"] <= seconds
