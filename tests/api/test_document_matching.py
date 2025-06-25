import json
import pytest
import sys
from pathlib import Path
from pytest_bdd import scenario, given, when, then, parsers
from fastapi.testclient import TestClient

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
from app import app


@scenario(
    "../../features/api/document_matching_scenarios.feature", "Empty candidate list"
)
def test_empty_candidate_list():
    """Test that the service handles empty candidate lists correctly."""
    pass


@scenario(
    "../../features/api/document_matching_scenarios.feature", "Supplier ID mismatch"
)
def test_supplier_id_mismatch():
    """Test that the service handles documents with mismatched supplier IDs correctly."""
    pass


@scenario(
    "../../features/api/document_matching_scenarios.feature",
    "Match on purchase order number",
)
def test_po_match():
    """Test that the service correctly matches documents based on shared purchase order number."""
    pass


@pytest.fixture
def client():
    """
    Test client for the FastAPI app
    """
    return TestClient(app)


@pytest.fixture
def context():
    """Shared context between steps"""
    return {}


@given(parsers.parse('the matching service is expected to be running at "{url}"'))
def document_matching_service_url(url, context):
    """
    Set the service URL for tests
    """
    context["base_url"] = url


@given(parsers.parse('I have a primary document defined as "{filename}"'))
def primary_document(filename, context):
    """
    Load a primary document from test data
    """
    test_data_path = (
        Path(__file__).parent.parent.parent / "features" / "test_data" / filename
    )
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
    test_data_path = (
        Path(__file__).parent.parent.parent / "features" / "test_data" / filename
    )
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


@when('I send a POST request to "/" with the primary document and candidate documents')
def send_post_with_primary_and_candidates(client, context):
    """
    Send a POST request to root endpoint with primary document and candidate documents
    """
    payload = {
        "document": context["primary_document"],
        "candidate-documents": context["candidate_documents"],
    }
    response = client.post("/", json=payload)
    context["response"] = response


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


@then("the response body should contain exactly one match with the shared PO number")
def check_po_match_response(context):
    """
    Check that the response body contains exactly one match based on the shared purchase order number
    """
    response_data = context["response"].json()

    # Verify that the response indicates a match
    assert "labels" in response_data, "Response should have labels field"
    assert "match" in response_data["labels"], "Expected 'match' in labels"

    # Check that there's exactly one document match
    assert "documents" in response_data, "Response should have documents field"
    assert (
        len(response_data["documents"]) == 2
    ), "Expected exactly two documents (primary and match)"
    assert sorted([doc["id"] for doc in response_data["documents"]]) == sorted(
        [
            context["primary_document"]["id"],
            context["candidate_documents"][0]["id"],
        ]
    )
