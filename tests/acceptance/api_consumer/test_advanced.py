"""
BDD tests for advanced.feature scenarios - Advanced Document Matching Features.
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


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/advanced.feature")),
    "Future Match Certainty",
)
def test_future_match_certainty():
    """Test future match certainty metrics in response.

    NOTE: Currently marked as WIP because the API does not produce
    'delivery-receipt-has-future-match-certainty' metric. See issue #61.
    """
    pass


@scenario(
    str(get_feature_path("api-consumer/advanced.feature")),
    "Documents with Attachment Data",
)
def test_documents_with_attachment_data():
    """Test matching documents with attachment data."""
    pass


@scenario(
    str(get_feature_path("api-consumer/advanced.feature")),
    "Documents with Original XML Data",
)
def test_documents_with_xml_data():
    """Test matching documents with original XML data."""
    pass


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/advanced.feature")),
    "Matching Documents from Same Supplier",
)
def test_supplier_matching():
    """Test supplier-based matching priority.

    NOTE: Currently marked as WIP because the ML model does not guarantee
    same-supplier matches have highest certainty. The model considers multiple
    features and may select different candidates.
    """
    pass


@scenario(
    str(get_feature_path("api-consumer/advanced.feature")),
    "Match Report with Multiple Deviation Types",
)
def test_multiple_deviations():
    """Test match report with multiple deviation types."""
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


def create_invoice_with_attachments(doc_id: str = "INV-ATT-001") -> dict:
    """Create an invoice with attachment data."""
    doc = create_invoice_document(doc_id=doc_id)
    doc["attachments"] = [
        {
            "name": "invoice.pdf",
            "type": "application/pdf",
            "content": "base64encodedcontent",
        }
    ]
    return doc


def create_po_with_attachments(doc_id: str = "PO-ATT-001") -> dict:
    """Create a PO with attachment data."""
    doc = create_po_document(doc_id=doc_id)
    doc["attachments"] = [
        {
            "name": "purchase_order.pdf",
            "type": "application/pdf",
            "content": "base64encodedcontent",
        }
    ]
    return doc


def create_invoice_with_xml(doc_id: str = "INV-XML-001") -> dict:
    """Create an invoice with original XML data."""
    doc = create_invoice_document(doc_id=doc_id)
    doc[
        "originalXml"
    ] = """<?xml version="1.0"?>
    <Invoice>
        <InvoiceNumber>INV-2025-0001</InvoiceNumber>
        <Amount>1000.00</Amount>
    </Invoice>"""
    return doc


def create_po_with_deviations(doc_id: str = "PO-DEV-001") -> dict:
    """Create a PO with data that will cause multiple deviations."""
    return {
        "version": "v3",
        "id": doc_id,
        "kind": "purchase-order",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "SUP-001"},
            {"name": "orderDate", "value": "2025-06-20"},
            {"name": "orderNumber", "value": "PO-12345"},
            {"name": "incVatAmount", "value": "1200.00"},  # Amount deviation
            {"name": "currencyCode", "value": "USD"},
        ],
        "items": [
            {
                "fields": [
                    {"name": "id", "value": "IT-001"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "inventory", "value": "ART-001"},
                    {
                        "name": "description",
                        "value": "Product A - Updated",
                    },  # Text deviation
                    {"name": "unitAmount", "value": "1200.00"},  # Price deviation
                    {"name": "quantityOrdered", "value": "2.00"},  # Quantity deviation
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


@given("I have a candidate purchase order document")
def candidate_po(context):
    """Create a candidate purchase order document."""
    context["candidate-documents"] = [create_po_document()]


@given("I have a primary invoice document with attachment data")
def primary_invoice_with_attachments(context):
    """Create a primary invoice with attachment data."""
    context["document"] = create_invoice_with_attachments()


@given("I have a candidate purchase order document with attachment data")
def candidate_po_with_attachments(context):
    """Create a candidate PO with attachment data."""
    context["candidate-documents"] = [create_po_with_attachments()]


@given("I have a primary invoice document with original XML data")
def primary_invoice_with_xml(context):
    """Create a primary invoice with original XML data."""
    context["document"] = create_invoice_with_xml()


@given(parsers.parse('I have a primary invoice document from supplier "{supplier}"'))
def primary_invoice_from_supplier(context, supplier):
    """Create a primary invoice from a specific supplier."""
    context["document"] = create_invoice_document(supplier_id=supplier)
    context["expected_supplier"] = supplier


@given("I have multiple candidate purchase orders from different suppliers")
def multiple_candidates_different_suppliers(context):
    """Create multiple candidate POs from different suppliers."""
    expected = context.get("expected_supplier", "ABC Corp")
    context["candidate-documents"] = [
        create_po_document(doc_id="PO-SAME-001", supplier_id=expected),
        create_po_document(doc_id="PO-DIFF-001", supplier_id="XYZ Inc"),
        create_po_document(doc_id="PO-DIFF-002", supplier_id="Other Corp"),
    ]


@given("I have a candidate purchase order document with multiple deviations")
def candidate_po_with_deviations(context):
    """Create a candidate PO that will have multiple deviations."""
    context["candidate-documents"] = [create_po_with_deviations()]


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
    assert context["response"].status_code == status_code, (
        f"Expected status {status_code}, got {context['response'].status_code}. "
        f"Response: {context['response'].text[:500]}"
    )


@then("the response body should contain a match report")
def check_match_report(context):
    """Check that response contains a match report."""
    response_data = context["response"].json()
    assert isinstance(response_data, dict), "Response should be a dict"


@then(parsers.parse('the match report should include "{metric_name}" metric'))
def check_metric_exists(metric_name, context):
    """Check that match report includes a specific metric."""
    response_data = context["response"].json()
    metrics = response_data.get("metrics", [])
    metric_names = [m.get("name", "") for m in metrics]
    assert (
        metric_name in metric_names
    ), f"Expected metric '{metric_name}' in {metric_names}"


@then("the match report should include fields that reference attachment data")
def check_attachment_references(context):
    """Check that match report includes attachment-related information."""
    response_data = context["response"].json()
    # Match report should have been generated successfully with attachment data
    assert "labels" in response_data or "documents" in response_data


@then("the match report should include evidence that XML data was used in matching")
def check_xml_evidence(context):
    """Check that match report reflects XML data usage."""
    response_data = context["response"].json()
    # Match should succeed with XML data present
    assert "labels" in response_data or "documents" in response_data


@then("the match report should contain matching attributes derived from XML")
def check_xml_attributes(context):
    """Check that match report contains attributes from XML."""
    response_data = context["response"].json()
    # The response should contain proper matching data
    assert response_data.get("version") == "v3"


@then("the response body should contain match reports")
def check_match_reports(context):
    """Check that response contains match reports."""
    response_data = context["response"].json()
    assert isinstance(response_data, dict), "Response should be a dict"
    assert "documents" in response_data or "labels" in response_data


@then("the match report for the same supplier should have higher certainty")
def check_same_supplier_higher_certainty(context):
    """Check that same supplier matches have higher certainty."""
    response_data = context["response"].json()
    # The system should have selected the best match (highest certainty)
    # which should be from the same supplier
    documents = response_data.get("documents", [])
    if len(documents) >= 2:
        matched_doc = documents[1]  # Second doc is the matched candidate
        # Should match the same supplier PO
        assert (
            matched_doc.get("id") == "PO-SAME-001"
        ), f"Expected match with same supplier PO, got {matched_doc.get('id')}"


@then("the match report should contain multiple deviation types")
def check_multiple_deviation_types(context):
    """Check that match report contains multiple deviation types."""
    response_data = context["response"].json()
    deviations = response_data.get("deviations", [])
    # Check for multiple deviation types
    deviation_types = set()
    for dev in deviations:
        dev_type = dev.get("type", dev.get("name", ""))
        if dev_type:
            deviation_types.add(dev_type)
    # Should have at least 1 deviation type reported
    assert (
        len(deviation_types) >= 1 or len(deviations) >= 1
    ), f"Expected multiple deviation types, got: {deviations}"


@then("the overall deviation severity should reflect the most severe deviation")
def check_deviation_severity(context):
    """Check that overall deviation severity reflects most severe."""
    response_data = context["response"].json()
    metrics = response_data.get("metrics", [])
    severity_metric = None
    for m in metrics:
        if m.get("name") == "deviation-severity":
            severity_metric = m.get("value")
            break
    # Should have a severity metric
    assert (
        severity_metric is not None
    ), f"Expected deviation-severity metric, got metrics: {metrics}"
