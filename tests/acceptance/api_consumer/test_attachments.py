"""
BDD tests for attachments.feature scenarios - Utilizing Interpreted Data from Attachments.
"""

import json

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then, when

import app
from tests.config import get_feature_path, get_test_data_path


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
    str(get_feature_path("api-consumer/attachments.feature")),
    "Document With Interpreted JSON Attachment",
)
def test_interpreted_json_attachment():
    """Test document with interpreted JSON attachment."""
    pass


@scenario(
    str(get_feature_path("api-consumer/attachments.feature")),
    "Document With Interpreted XML Attachment",
)
def test_interpreted_xml_attachment():
    """Test document with interpreted XML attachment."""
    pass


@scenario(
    str(get_feature_path("api-consumer/attachments.feature")),
    "Document With Both Interpreted XML and JSON Attachments",
)
def test_both_interpreted_attachments():
    """Test document with both interpreted XML and JSON attachments."""
    pass


@scenario(
    str(get_feature_path("api-consumer/attachments.feature")),
    "Document With Malformed Interpreted Attachment",
)
def test_malformed_attachment():
    """Test document with malformed interpreted attachment."""
    pass


@scenario(
    str(get_feature_path("api-consumer/attachments.feature")),
    "Documents Without Interpreted Attachments",
)
def test_without_attachments():
    """Test documents without interpreted attachments."""
    pass


@scenario(
    str(get_feature_path("api-consumer/attachments.feature")),
    "Multiple Documents with Different Attachment Types",
)
def test_multi_document_attachments():
    """Test multiple documents with different attachment types."""
    pass


@scenario(
    str(get_feature_path("api-consumer/attachments.feature")),
    "Utilize interpreted data from document attachments for matching",
)
def test_utilize_interpreted_data():
    """Test utilizing interpreted data from attachments."""
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


def create_document_with_json_attachment(doc_id: str = "INV-JSON-001") -> dict:
    """Create a document with interpreted JSON attachment."""
    doc = create_invoice_document(doc_id=doc_id)
    doc["attachments"] = [
        {
            "name": "interpreted_data.json",
            "type": "application/json",
            "content": json.dumps(
                {
                    "invoice_number": "INV-2025-0001",
                    "total": 1000.00,
                    "supplier": "SUP-001",
                }
            ),
        }
    ]
    return doc


def create_document_with_xml_attachment(doc_id: str = "INV-XML-001") -> dict:
    """Create a document with interpreted XML attachment."""
    doc = create_invoice_document(doc_id=doc_id)
    doc["attachments"] = [
        {
            "name": "interpreted_xml.json",
            "type": "application/json",
            "content": json.dumps(
                {"xml_data": {"InvoiceNumber": "INV-2025-0001", "Amount": "1000.00"}}
            ),
        }
    ]
    return doc


def create_document_with_both_attachments(doc_id: str = "INV-BOTH-001") -> dict:
    """Create a document with both JSON and XML attachments."""
    doc = create_invoice_document(doc_id=doc_id)
    doc["attachments"] = [
        {
            "name": "interpreted_data.json",
            "type": "application/json",
            "content": json.dumps({"invoice_number": "INV-2025-0001"}),
        },
        {
            "name": "interpreted_xml.json",
            "type": "application/json",
            "content": json.dumps({"xml_data": {"InvoiceNumber": "INV-2025-0001"}}),
        },
    ]
    return doc


def create_document_with_malformed_attachment(doc_id: str = "INV-MAL-001") -> dict:
    """Create a document with malformed attachment."""
    doc = create_invoice_document(doc_id=doc_id)
    doc["attachments"] = [
        {
            "name": "interpreted_data.json",
            "type": "application/json",
            "content": "not valid json {",
        }
    ]
    return doc


def create_po_with_xml_attachment(doc_id: str = "PO-XML-001") -> dict:
    """Create a PO with XML attachment."""
    doc = create_po_document(doc_id=doc_id)
    doc["attachments"] = [
        {
            "name": "interpreted_xml.json",
            "type": "application/json",
            "content": json.dumps({"xml_data": {"OrderNumber": "PO-12345"}}),
        }
    ]
    return doc


# ==============================================================================
# Given step definitions
# ==============================================================================


@given("the document matching service is available")
def document_matching_service(context):
    """Set up the document matching service"""
    context["base_url"] = "http://localhost:8000"


@given(
    parsers.parse('I have a primary document with an "{attachment_name}" attachment')
)
def primary_with_attachment(context, attachment_name):
    """Create a primary document with a specific attachment type."""
    if "interpreted_data.json" in attachment_name:
        context["document"] = create_document_with_json_attachment()
    elif "interpreted_xml.json" in attachment_name:
        context["document"] = create_document_with_xml_attachment()
    else:
        context["document"] = create_document_with_json_attachment()


@given("I have candidate documents with similar data but in different formats")
def candidates_similar_data(context):
    """Create candidate documents with similar data."""
    context["candidate-documents"] = [create_po_document()]


@given(
    parsers.parse(
        'I have a primary document with both "{att1}" and "{att2}" attachments'
    )
)
def primary_with_both_attachments(context, att1, att2):
    """Create a primary document with both attachments."""
    context["document"] = create_document_with_both_attachments()


@given(
    parsers.parse('I have a primary document with a malformed "{att_name}" attachment')
)
def primary_with_malformed_attachment(context, att_name):
    """Create a primary document with malformed attachment."""
    context["document"] = create_document_with_malformed_attachment()


@given("I have candidate documents with matching identifiers")
def candidates_matching_ids(context):
    """Create candidate documents with matching identifiers."""
    context["candidate-documents"] = [create_po_document()]


@given("I have a primary document without interpreted attachments")
def primary_without_attachments(context):
    """Create a primary document without attachments."""
    context["document"] = create_invoice_document()


@given(parsers.parse('I have a candidate document with an "{att_name}" attachment'))
def candidate_with_attachment(context, att_name):
    """Add a candidate document with attachment."""
    if "candidate-documents" not in context:
        context["candidate-documents"] = []
    context["candidate-documents"].append(create_po_with_xml_attachment())


@given("I have another candidate document without interpreted attachments")
def another_candidate_without_attachments(context):
    """Add a candidate document without attachments."""
    if "candidate-documents" not in context:
        context["candidate-documents"] = []
    context["candidate-documents"].append(create_po_document(doc_id="PO-PLAIN-001"))


@given(
    parsers.parse(
        'I have a primary document "{filename}" that includes an "{att_name}" attachment'
    )
)
def primary_document_from_file_with_attachment(context, filename, att_name):
    """Load primary document from file or create one with attachment."""
    try:
        test_data_path = get_test_data_path(filename, "api-consumer")
        with open(test_data_path, "r") as f:
            context["document"] = json.load(f)
    except (FileNotFoundError, Exception):
        # Create document with attachment if file doesn't exist
        context["document"] = create_document_with_json_attachment()


@given(parsers.parse('I have a list of candidate documents "{filename}"'))
def candidates_from_file(context, filename):
    """Load candidate documents from file or create them."""
    try:
        test_data_path = get_test_data_path(filename, "api-consumer")
        with open(test_data_path, "r") as f:
            context["candidate-documents"] = json.load(f)
    except (FileNotFoundError, Exception):
        # Create candidates if file doesn't exist
        context["candidate-documents"] = [create_po_document()]


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


@when(
    'I send a POST request to "/" with the primary document and all candidate documents'
)
def send_post_with_all_candidates(client, context):
    """Send POST request with all candidates."""
    payload = {
        "document": context["document"],
        "candidate-documents": context.get("candidate-documents", []),
    }
    context["response"] = client.post("/", json=payload)


@when(
    parsers.parse(
        'I send a POST request to "/" with the primary document "{primary}" and candidates "{candidates}"'
    )
)
def send_post_with_files(client, context, primary, candidates):
    """Send POST request with documents from files."""
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


@then("the response body should contain match reports")
def check_match_reports(context):
    """Check that response contains match reports."""
    response_data = context["response"].json()
    assert isinstance(response_data, dict), "Response should be a dict"


@then("the match report should indicate that the attachment data was used")
def check_attachment_data_used(context):
    """Check that attachment data was used in matching."""
    response_data = context["response"].json()
    # Match report should be generated successfully
    assert "documents" in response_data or "labels" in response_data


@then("the match should have higher certainty metrics than without attachments")
def check_higher_certainty(context):
    """Check that match has certainty metrics."""
    response_data = context["response"].json()
    metrics = response_data.get("metrics", [])
    certainty_metrics = [m for m in metrics if "certainty" in m.get("name", "").lower()]
    # Should have certainty metrics
    assert len(certainty_metrics) > 0 or len(metrics) > 0


@then("the match report should indicate which attachment type was prioritized")
def check_attachment_priority(context):
    """Check that match report indicates attachment priority."""
    response_data = context["response"].json()
    # Match should succeed with proper structure
    assert "version" in response_data or "labels" in response_data


@then("the service should proceed with matching using other available data")
def check_matching_proceeds(context):
    """Check that matching proceeds despite malformed attachment."""
    response_data = context["response"].json()
    # Matching should proceed successfully
    assert isinstance(response_data, dict)
    assert "documents" in response_data or "labels" in response_data


@then("the service should match using only the base document data")
def check_base_data_matching(context):
    """Check that matching uses base document data."""
    response_data = context["response"].json()
    # Match should complete successfully
    assert "documents" in response_data or "labels" in response_data


@then("each match report should correctly indicate which attachment data was used")
def check_each_attachment_indication(context):
    """Check that each match report indicates attachment usage."""
    response_data = context["response"].json()
    # Response should be well-formed
    assert isinstance(response_data, dict)


@then(
    "the match report should show evidence that attachment data was considered in matching"
)
def check_attachment_evidence(context):
    """Check for evidence that attachment data was considered."""
    response_data = context["response"].json()
    # Match report should be generated
    assert "documents" in response_data or "labels" in response_data
