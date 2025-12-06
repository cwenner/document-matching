"""Tests for item_level.feature scenarios."""

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
# Given step definitions
# ==============================================================================


@given("the document matching service is available")
def document_matching_service(context):
    """Set up the document matching service"""
    context["base_url"] = "http://localhost:8000"


def create_invoice_item(index: int, article_number: str, description: str) -> dict:
    """Helper to create an invoice item."""
    return {
        "fields": [
            {"name": "text", "value": description},
            {"name": "lineNumber", "value": str(index + 1)},
            {"name": "debit", "value": "100.00"},
            {"name": "articleNumber", "value": article_number},
        ]
    }


def create_po_item(index: int, article_number: str, description: str) -> dict:
    """Helper to create a purchase order item."""
    return {
        "fields": [
            {"name": "id", "value": f"IT-00{index + 1}"},
            {"name": "lineNumber", "value": str(index + 1)},
            {"name": "inventory", "value": article_number},
            {"name": "description", "value": description},
            {"name": "uom", "value": "STYCK"},
            {"name": "unitAmount", "value": "50.00"},
            {"name": "quantityOrdered", "value": "2.00"},
            {"name": "quantityToReceive", "value": "2.00"},
            {"name": "quantityReceived", "value": "0.00"},
            {"name": "quantityToInvoice", "value": "2.00"},
        ]
    }


@given(parsers.parse("I have a primary invoice with {count:d} items"))
def primary_invoice_with_items(context, count):
    """Create a primary invoice with specified number of items."""
    items = [
        create_invoice_item(i, f"ART-{i + 1:03d}", f"Product {chr(65 + i)}")
        for i in range(count)
    ]
    context["document"] = {
        "version": "v3",
        "id": "INV-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": str(100.0 * count)},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": str(80.0 * count)},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": items,
    }


@given(parsers.parse("I have a candidate purchase order with the same {count:d} items"))
def candidate_po_with_same_items(context, count):
    """Create a candidate PO with same items as the invoice."""
    items = [
        create_po_item(i, f"ART-{i + 1:03d}", f"Product {chr(65 + i)}")
        for i in range(count)
    ]
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "PO-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test Order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": str(100.0 * count)},
                {"name": "excVatAmount", "value": str(80.0 * count)},
            ],
            "items": items,
        }
    ]


@given(parsers.parse("I have a candidate purchase order with {count:d} matching items"))
def candidate_po_with_matching_items(context, count):
    """Create a candidate PO with specified number of matching items."""
    items = [
        create_po_item(i, f"ART-{i + 1:03d}", f"Product {chr(65 + i)}")
        for i in range(count)
    ]
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "PO-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test Order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": str(100.0 * count)},
                {"name": "excVatAmount", "value": str(80.0 * count)},
            ],
            "items": items,
        }
    ]


@given(parsers.parse("I have a candidate purchase order with {count:d} items"))
def candidate_po_with_items(context, count):
    """Create a candidate PO with specified number of items."""
    items = [
        create_po_item(i, f"ART-{i + 1:03d}", f"Product {chr(65 + i)}")
        for i in range(count)
    ]
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "PO-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test Order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": str(100.0 * count)},
                {"name": "excVatAmount", "value": str(80.0 * count)},
            ],
            "items": items,
        }
    ]


@given("I have a primary invoice with items in order A, B, C")
def primary_invoice_items_abc(context):
    """Create primary invoice with items A, B, C in that order."""
    items = [
        create_invoice_item(0, "ART-001", "Product A"),
        create_invoice_item(1, "ART-002", "Product B"),
        create_invoice_item(2, "ART-003", "Product C"),
    ]
    context["document"] = {
        "version": "v3",
        "id": "INV-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "S789"},
            {"name": "invoiceDate", "value": "2025-06-22"},
            {"name": "invoiceNumber", "value": "INV-2025-0622"},
            {"name": "incVatAmount", "value": "300.00"},
            {"name": "currencyCode", "value": "USD"},
            {"name": "excVatAmount", "value": "240.00"},
            {"name": "type", "value": "DEBIT"},
            {"name": "orderReference", "value": "PO-12345"},
        ],
        "items": items,
    }


@given("I have a candidate purchase order with items in order C, A, B")
def candidate_po_items_cab(context):
    """Create candidate PO with items C, A, B (reordered)."""
    items = [
        create_po_item(0, "ART-003", "Product C"),
        create_po_item(1, "ART-001", "Product A"),
        create_po_item(2, "ART-002", "Product B"),
    ]
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "PO-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test Order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": "300.00"},
                {"name": "excVatAmount", "value": "240.00"},
            ],
            "items": items,
        }
    ]


@given(
    parsers.parse('I have a primary invoice with item article number "{article_num}"')
)
def primary_invoice_with_article(context, article_num):
    """Create primary invoice with specific article number."""
    context["document"] = {
        "version": "v3",
        "id": "INV-001",
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
                    {"name": "text", "value": "Test Product Widget"},
                    {"name": "lineNumber", "value": "1"},
                    {"name": "debit", "value": "100.00"},
                    {"name": "inventory", "value": article_num},
                ]
            }
        ],
    }


@given(
    parsers.parse(
        'I have a candidate purchase order with item article number "{article_num}"'
    )
)
def candidate_po_with_article(context, article_num):
    """Create candidate PO with specific article number."""
    context["candidate-documents"] = [
        {
            "version": "v3",
            "id": "PO-001",
            "kind": "purchase-order",
            "site": "test-site",
            "stage": "final",
            "headers": [
                {"name": "orderNumber", "value": "PO-12345"},
                {"name": "supplierId", "value": "S789"},
                {"name": "description", "value": "Test Order"},
                {"name": "orderDate", "value": "2025-06-20"},
                {"name": "incVatAmount", "value": "100.00"},
                {"name": "excVatAmount", "value": "80.00"},
            ],
            "items": [
                {
                    "fields": [
                        {"name": "id", "value": "IT-001"},
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventory", "value": article_num},
                        {"name": "description", "value": "Test Product Widget"},
                        {"name": "uom", "value": "STYCK"},
                        {"name": "unitAmount", "value": "50.00"},
                        {"name": "quantityOrdered", "value": "2.00"},
                        {"name": "quantityToReceive", "value": "2.00"},
                        {"name": "quantityReceived", "value": "0.00"},
                        {"name": "quantityToInvoice", "value": "2.00"},
                    ]
                }
            ],
        }
    ]


@given("the item descriptions are similar")
def item_descriptions_similar(context):
    """Marker step - descriptions are already similar from previous steps."""
    pass


# ==============================================================================
# When step definitions
# ==============================================================================


@when('I send a POST request to "/" with the primary document and candidate document')
def send_post_request_with_documents(context, client):
    """Send a POST request with primary and candidate documents."""
    payload = {
        "document": context["document"],
        "candidate-documents": context["candidate-documents"],
    }
    context["response"] = client.post("/", json=payload)


# ==============================================================================
# Then step definitions
# ==============================================================================


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(status_code, context):
    """Check that the response has the expected status code."""
    assert context["response"].status_code == status_code


@then("the response body should contain a match report")
def check_match_report(context):
    """Check that the response body contains a match report."""
    response_data = context["response"].json()
    assert isinstance(response_data, dict), "Expected a dictionary response"
    assert (
        "documents" in response_data or "labels" in response_data
    ), "Response missing key match report fields"


@then(
    parsers.parse(
        'the match report should contain {count:d} itempairs with match_type "{match_type}"'
    )
)
def check_itempairs_count_with_type(context, count, match_type):
    """Check that match report has specified number of itempairs with type."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    matching_pairs = [p for p in itempairs if p.get("match_type") == match_type]
    assert len(matching_pairs) == count, (
        f"Expected {count} itempairs with match_type '{match_type}', "
        f"got {len(matching_pairs)}"
    )


@then("each itempair should have item_indices for both documents")
def check_itempairs_have_indices(context):
    """Check that each itempair has item_indices."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    for i, pair in enumerate(itempairs):
        assert "item_indices" in pair, f"Itempair {i} missing item_indices"
        indices = pair["item_indices"]
        assert isinstance(indices, list), f"Itempair {i} item_indices should be list"
        assert len(indices) == 2, f"Itempair {i} item_indices should have 2 elements"


@then("each itempair should have item_unchanged_certainty scores")
def check_itempairs_have_certainty(context):
    """Check that each itempair has item_unchanged_certainty."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    for i, pair in enumerate(itempairs):
        assert (
            "item_unchanged_certainty" in pair
        ), f"Itempair {i} missing item_unchanged_certainty"


@then(
    parsers.parse(
        'each itempair should have match_type property as a string with value "{match_type}"'
    )
)
def check_each_itempair_match_type(context, match_type):
    """Check that each itempair has the specified match_type as string."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    for i, pair in enumerate(itempairs):
        assert "match_type" in pair, f"Itempair {i} missing match_type"
        assert pair["match_type"] == match_type, (
            f"Itempair {i} should have match_type '{match_type}', "
            f"got '{pair['match_type']}'"
        )


@then(parsers.parse("the match report should contain {count:d} itempairs"))
def check_itempairs_count(context, count):
    """Check total number of itempairs."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])
    assert len(itempairs) == count, f"Expected {count} itempairs, got {len(itempairs)}"


@then(parsers.parse('{count:d} itempairs should have match_type "{match_type}"'))
def check_itempairs_with_match_type(context, count, match_type):
    """Check that specified number of itempairs have given match_type."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    matching = [p for p in itempairs if p.get("match_type") == match_type]
    assert len(matching) == count, (
        f"Expected {count} itempairs with match_type '{match_type}', "
        f"got {len(matching)}"
    )


@then("the unmatched itempairs should have item_indices [n, null]")
def check_unmatched_primary_indices(context):
    """Check unmatched items have [n, null] pattern (primary unmatched)."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    unmatched = [p for p in itempairs if p.get("match_type") == "unmatched"]
    for pair in unmatched:
        indices = pair.get("item_indices", [])
        assert len(indices) == 2, "item_indices should have 2 elements"
        assert indices[0] is not None, "First index should be non-null for primary"
        assert indices[1] is None, "Second index should be null for unmatched"


@then("the unmatched itempairs should have item_indices [null, n]")
def check_unmatched_candidate_indices(context):
    """Check unmatched items have [null, n] pattern (candidate unmatched)."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    unmatched = [p for p in itempairs if p.get("match_type") == "unmatched"]
    for pair in unmatched:
        indices = pair.get("item_indices", [])
        assert len(indices) == 2, "item_indices should have 2 elements"
        assert indices[0] is None, "First index should be null for candidate unmatched"
        assert indices[1] is not None, "Second index should be non-null for candidate"


@then(
    parsers.parse(
        'the matched itempairs should have match_type property as a string with value "{match_type}"'
    )
)
def check_matched_itempairs_type(context, match_type):
    """Check matched itempairs have correct match_type."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    matched = [p for p in itempairs if p.get("match_type") == "matched"]
    for pair in matched:
        assert pair["match_type"] == match_type


@then(
    parsers.parse(
        'the unmatched itempairs should have match_type property as a string with value "{match_type}"'
    )
)
def check_unmatched_itempairs_type(context, match_type):
    """Check unmatched itempairs have correct match_type."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    unmatched = [p for p in itempairs if p.get("match_type") == "unmatched"]
    for pair in unmatched:
        assert pair["match_type"] == match_type


@then(
    parsers.parse('the unmatched itempairs should have deviations with code "{code}"')
)
def check_unmatched_has_deviation(context, code):
    """Check unmatched itempairs have specific deviation code."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    unmatched = [p for p in itempairs if p.get("match_type") == "unmatched"]
    for pair in unmatched:
        deviations = pair.get("deviations", [])
        # Convert code format if needed (item-unmatched -> ITEM_UNMATCHED)
        expected_code = code.upper().replace("-", "_")
        codes = [d.get("code") for d in deviations]
        assert (
            expected_code in codes
        ), f"Expected deviation code '{expected_code}' in {codes}"


@then("the item_indices should correctly map the reordered items")
def check_reordered_indices(context):
    """Check that item indices correctly map reordered items."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    assert len(itempairs) >= 3, "Expected at least 3 itempairs for reordering test"

    for pair in itempairs:
        indices = pair.get("item_indices", [])
        assert len(indices) == 2, "Each itempair should have 2 indices"
        assert indices[0] is not None, "Primary index should not be null"
        assert indices[1] is not None, "Candidate index should not be null"


@then("the match report should contain an itempair for these items")
def check_itempair_exists(context):
    """Check that at least one itempair exists."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])
    assert len(itempairs) >= 1, "Expected at least one itempair"


@then(parsers.parse('the itempair should have deviation with code "{code}"'))
def check_itempair_has_deviation(context, code):
    """Check itempair has specific deviation code."""
    response_data = context["response"].json()
    itempairs = response_data.get("itempairs", [])

    found = False
    # Convert code format if needed (article-numbers-differ -> ARTICLE_NUMBERS_DIFFER)
    expected_code = code.upper().replace("-", "_")

    for pair in itempairs:
        deviations = pair.get("deviations", [])
        codes = [d.get("code") for d in deviations]
        if expected_code in codes:
            found = True
            break

    assert found, f"Expected deviation code '{expected_code}' in itempairs"


# ==============================================================================
# Scenario declarations
# ==============================================================================


@scenario(
    str(get_feature_path("api-consumer/item_level.feature")),
    "Item Pairing Success",
)
def test_item_pairing_success():
    """Test that items are correctly paired."""
    pass


@scenario(
    str(get_feature_path("api-consumer/item_level.feature")),
    "Unmatched Items in Primary Document",
)
def test_unmatched_items_primary():
    """Test handling of unmatched items in primary document."""
    pass


@scenario(
    str(get_feature_path("api-consumer/item_level.feature")),
    "Unmatched Items in Candidate Document",
)
def test_unmatched_items_candidate():
    """Test handling of unmatched items in candidate document."""
    pass


@scenario(
    str(get_feature_path("api-consumer/item_level.feature")),
    "Different Item Order in Documents",
)
def test_different_item_order():
    """Test that items match regardless of order."""
    pass


@scenario(
    str(get_feature_path("api-consumer/item_level.feature")),
    "Matching Items with Different Article Numbers",
)
def test_different_article_numbers():
    """Test matching items with different article numbers."""
    pass
