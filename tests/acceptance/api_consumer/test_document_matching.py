import json
import pytest
from pathlib import Path
from pytest_bdd import scenario, given, when, then, parsers
from fastapi.testclient import TestClient

import app

# Import from centralized config module
from tests.config import get_feature_path, get_test_data_path

# Import common step definitions
from tests.acceptance.steps.api_steps import client, context, document_matching_service, check_status_code


@scenario(str(get_feature_path("api-consumer/no_match.feature")), "Empty candidate list")
def test_empty_candidate_list():
    """Test that the service handles empty candidate lists correctly."""
    pass


@scenario(str(get_feature_path("api-consumer/no_match.feature")), "Supplier ID mismatch")
def test_supplier_id_mismatch():
    """Test that the service handles documents with mismatched supplier IDs correctly."""
    pass


@scenario(str(get_feature_path("api-consumer/basic.feature")), "Document with matching PO number")
def test_po_match():
    """Test that the service correctly matches documents based on shared purchase order number."""
    pass


@pytest.fixture
def client():
    """
    Test client for the FastAPI app
    """
    return TestClient(app.app)


@pytest.fixture
def context():
    """Shared context between steps"""
    return {}


@given("the document matching service is available")
def document_matching_service(context):
    """
    Set up the document matching service for testing
    """
    # For testing purposes, we assume the service is running locally
    context["base_url"] = "http://localhost:8000"


@given(parsers.parse('I have a primary document defined as "{filename}"'))
def primary_document(filename, context):
    """
    Load a primary document from test data
    """
    test_data_path = get_test_data_path(filename)
    with open(test_data_path, "r") as f:
        context["primary_document"] = json.load(f)


@given("no candidate documents are provided")
def no_candidate_documents(context):
    """
    Set empty list for candidate documents in context
    """
    context["candidate_documents"] = []


@given(parsers.parse('I have a list of candidate documents defined as "{filename}"'))
def candidate_documents(filename, context):
    """
    Load candidate documents from test data
    """
    test_data_path = get_test_data_path(filename)
    with open(test_data_path, "r") as f:
        context["candidate_documents"] = json.load(f)


@when(
    'I send a POST request to "/" with the primary document and an empty list of candidate documents'
)
def send_post_with_primary_and_empty_candidates(client, context):
    """
    Send a POST request to root endpoint with primary document and empty candidates
    """
    payload = {
        "document": context["primary_document"],
        "candidate-documents": context["candidate_documents"],
    }
    response = client.post("/", json=payload)
    context["response"] = response


@when(
    parsers.parse(
        'I send a POST request to "{endpoint}" with the primary document and candidate documents'
    )
)
def send_post_with_primary_and_candidates(endpoint, client, context):
    """
    Send a POST request to root endpoint with primary document and candidate documents
    """
    payload = {
        "document": context["primary_document"],
        "candidate-documents": context["candidate_documents"],
    }
    context["response"] = client.post(endpoint, json=payload)


@when(
    parsers.parse(
        'I send a POST request to "{endpoint}" with the primary document and candidates'
    )
)
def send_post_with_primary_and_candidates_alt(endpoint, client, context):
    """
    Alternative phrasing for sending a POST request with primary and candidate documents
    """
    payload = {
        "document": context["primary_document"],
        "candidate-documents": context["candidate_documents"],
    }
    context["response"] = client.post(endpoint, json=payload)


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(status_code, context):
    """
    Check that the response has the expected status code
    """
    assert context["response"].status_code == status_code


@then("the response body should indicate no matches were found")
def check_empty_response(context):
    """
    Check that the response body indicates no matches were found
    """
    response_data = context["response"].json()
    # There are multiple ways the API might indicate no matches:
    # 1. An empty list
    # 2. A response with "no-match" in labels
    # 3. A response with empty itempairs
    # 4. A response with no matches field or empty matches array

    if isinstance(response_data, list):
        assert len(response_data) == 0, "Expected empty list but got non-empty list"
    else:
        # If it's an object structure, we need to check the specifics of the response
        # Check for labels indicating no matches
        if "labels" in response_data:
            assert (
                "no-match" in response_data["labels"]
            ), "Expected 'no-match' in labels"
        # Check for empty itempairs
        elif "itempairs" in response_data:
            assert (
                len(response_data["itempairs"]) == 0
            ), "Expected empty itempairs array"
        # Check for empty matches array if present
        elif "matches" in response_data:
            assert len(response_data["matches"]) == 0, "Expected empty matches array"
        else:
            # If we can't find explicit no-match indicators, fail
            assert False, "Response doesn't indicate no matches found"


# Previous check_po_match_response function removed to avoid duplication
# Now using check_match_with_po_number for match report verification


@then("the response body should contain a match report")
def check_match_report(context):
    """
    Check that the response body contains a match report
    """
    response_data = context["response"].json()

    # Verify structure of match report
    assert isinstance(
        response_data, dict
    ), "Expected a dictionary response for match report"

    # Match report should have certain key fields
    assert (
        "documents" in response_data or "labels" in response_data
    ), "Response missing key match report fields"


@then("the response should comply with the API schema")
def check_schema_compliance(context):
    """
    Check that the response complies with the API schema
    """
    # This is a more detailed schema validation
    # For now, we'll do a basic check of required fields
    response_data = context["response"].json()

    # Basic schema validation
    if isinstance(response_data, dict):
        # Should have key fields for a response
        assert any(
            key in response_data
            for key in ["documents", "labels", "itempairs", "deviations"]
        ), "Response missing required fields according to schema"
    elif isinstance(response_data, list):
        # Empty list is valid for no matches
        pass
    else:
        assert False, "Response is neither an object nor an array as required by schema"


@then(
    "the match report should contain exactly one match between the primary document and a candidate document"
)
def check_match_between_documents(context):
    """
    Check that the match report shows a match between documents with the same PO number
    """
    response_data = context["response"].json()

    # Verify that the response indicates a match
    assert "labels" in response_data, "Response should have labels field"
    assert "match" in response_data["labels"], "Expected 'match' in labels"

    # Check that the documents in the match are the ones with the shared PO number
    assert "documents" in response_data, "Response should have documents field"
    assert (
        len(response_data["documents"]) == 2
    ), "Expected exactly two documents (primary and match)"

    # Verify that the matched documents have the correct IDs
    doc_ids = sorted([doc["id"] for doc in response_data["documents"]])
    expected_ids = sorted(
        [context["primary_document"]["id"], context["candidate_documents"][0]["id"]]
    )
    assert (
        doc_ids == expected_ids
    ), f"Expected document IDs {expected_ids}, but got {doc_ids}"

    # We don't check the PO number directly since it's not in the match report
    # The PO number match is implied by the documents being listed as matched


@then("the match report should include document IDs from the candidate documents")
def check_document_ids_in_match_report(context):
    """
    Check that the match report includes document IDs from candidate documents
    """
    response_data = context["response"].json()

    # Check that there's a documents field
    assert "documents" in response_data, "Response should have documents field"

    # Get the document IDs from the response
    response_doc_ids = sorted([doc["id"] for doc in response_data["documents"]])

    # Get the expected document IDs (primary + at least one candidate)
    primary_id = context["primary_document"]["id"]
    candidate_ids = [doc["id"] for doc in context["candidate_documents"]]

    # Verify at least one candidate document ID is included
    found_candidate = False
    for candidate_id in candidate_ids:
        if candidate_id in response_doc_ids:
            found_candidate = True
            break

    assert found_candidate, "No candidate document IDs found in match report"
    assert (
        primary_id in response_doc_ids
    ), "Primary document ID not found in match report"
