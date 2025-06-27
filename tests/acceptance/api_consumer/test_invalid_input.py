"""
BDD tests for invalid input handling in the document matching API
"""

import json
import pytest
from pathlib import Path
from pytest_bdd import scenario, given, when, then, parsers
from fastapi.testclient import TestClient

import app

# Import from centralized config module
from tests.config import get_feature_path, get_test_data_path

# Import all step definitions from api_steps module
# This ensures pytest-bdd can find the common step definitions
import tests.acceptance.steps.api_steps  # This imports all step definitions

# Also import the specific fixtures we need
from tests.acceptance.steps.api_steps import client, context


# Original scenarios from invalid_input.feature - should run by default
@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Missing Primary Document",
)
def test_missing_primary_document():
    """Test API response when primary document is missing."""
    pass


@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Invalid Document Format",
)
def test_invalid_document_format():
    """Test API response when document format is invalid."""
    pass


@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Malformed JSON Payload",
)
def test_malformed_json_payload():
    """Test API response when JSON payload is malformed."""
    pass


@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Candidate Documents Not an Array",
)
def test_candidates_not_array():
    """Test API response when candidates are not provided as array."""
    pass


@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Unsupported Content Type",
)
def test_unsupported_content_type():
    """Test API response when content type is unsupported."""
    pass


@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Missing Required Document Fields",
)
def test_missing_required_fields():
    """Test API response when required document fields are missing."""
    pass


@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")), "Invalid Field Values"
)
def test_invalid_field_values():
    """Test API response when document field values are invalid."""
    pass


@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Handle invalid request payload gracefully",
)
def test_handle_invalid_payload():
    """Test API graceful handling of invalid request payload."""
    pass


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")), "Empty Request Body"
)
def test_empty_request_body():
    """Test API response when request body is empty - WIP."""
    pass


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")), "Wrong HTTP Method"
)
def test_wrong_http_method():
    """Test API response when wrong HTTP method is used - WIP."""
    pass


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")), "Null Document Field"
)
def test_null_document_field():
    """Test API response when document field is null - WIP."""
    pass


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Document Field Not an Object",
)
def test_document_not_object():
    """Test API response when document field is not an object - WIP."""
    pass


@pytest.mark.wip
@scenario(
    str(get_feature_path("api-consumer/invalid_input.feature")),
    "Null Candidate Documents Field",
)
def test_null_candidates():
    """Test API response when candidate documents field is null - WIP."""
    pass


# Common step definitions needed by all scenarios
@given("the document matching service is available")
def document_matching_service_available(context):
    """Set up the document matching service for testing"""
    context["base_url"] = "http://localhost:8000"


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_response_status_code(status_code, context):
    """Check that the response has the expected status code"""
    assert context["response"].status_code == status_code


# Step definitions for invalid input scenarios
@given("I have no primary document")
def no_primary_document(context):
    """Set context to have no primary document"""
    context["primary_document"] = None


@given("I have a list of valid candidate documents")
def valid_candidate_documents(context):
    """Load valid candidate documents from test data"""
    test_data_path = get_test_data_path("candidates_valid.json")
    with open(test_data_path, "r") as f:
        context["candidate_documents"] = json.load(f)


@given("I have a primary document with invalid format")
def primary_document_invalid_format(context):
    """Load a primary document with invalid format from test data"""
    test_data_path = get_test_data_path("primary_doc_invalid_format.json")
    with open(test_data_path, "r") as f:
        context["primary_document"] = json.load(f)


@given("I have a malformed JSON payload")
def malformed_json_payload(context):
    """Set up a malformed JSON payload"""
    context["malformed_payload"] = '{"document": {"id": "test", "incomplete": }'


@given("I have a valid primary document")
def valid_primary_document(context):
    """Load a valid primary document from test data"""
    test_data_path = get_test_data_path("primary_doc_shared_po.json")
    with open(test_data_path, "r") as f:
        context["primary_document"] = json.load(f)


@given("I have candidate documents incorrectly formatted as a single object")
def candidates_as_single_object(context):
    """Set candidate documents as a single object instead of array"""
    context["candidate_documents"] = {
        "version": "v3",
        "id": "CD-001",
        "kind": "purchase-order",
    }


@given("I have documents in an unsupported format")
def unsupported_format_documents(context):
    """Set up documents for unsupported content type test"""
    context["document_data"] = "plain text document content"


@given("I have a primary document missing required fields")
def primary_document_missing_fields(context):
    """Load a primary document missing required fields from test data"""
    test_data_path = get_test_data_path("primary_doc_missing_fields.json")
    with open(test_data_path, "r") as f:
        context["primary_document"] = json.load(f)


@given("I have a primary document with invalid field values")
def primary_document_invalid_values(context):
    """Load a primary document with invalid field values from test data"""
    test_data_path = get_test_data_path("primary_doc_invalid_values.json")
    with open(test_data_path, "r") as f:
        context["primary_document"] = json.load(f)


@given(parsers.parse('I have an invalid request payload defined as "{filename}"'))
def invalid_request_payload(context, filename):
    """Load an invalid request payload from test data"""
    test_data_path = get_test_data_path(filename)
    with open(test_data_path, "r") as f:
        context["invalid_payload"] = json.load(f)


@given("I have an empty request body")
def empty_request_body(context):
    """Set context to have an empty request body"""
    context["empty_body"] = True


@given("I have a request with null document field")
def null_document_field(context):
    """Set context to have a null document field"""
    context["null_document"] = True


@given("I have a document field as a string")
def document_as_string(context):
    """Set context to have document field as a string"""
    context["document_as_string"] = "this-is-a-string-not-object"


@given("I have null candidate documents field")
def null_candidates_field(context):
    """Set context to have null candidate documents field"""
    context["null_candidates"] = True


@when(
    'I send a POST request to "/" with a missing primary document and candidate documents'
)
def send_post_missing_primary(client, context):
    """Send POST request with missing primary document"""
    payload = {"candidate-documents": context["candidate_documents"]}
    context["response"] = client.post("/", json=payload)


@when('I send a POST request to "/" with the primary document and candidate documents')
def send_post_primary_and_candidates(client, context):
    """Send POST request with primary document and candidates"""
    payload = {
        "document": context["primary_document"],
        "candidate-documents": context["candidate_documents"],
    }
    context["response"] = client.post("/", json=payload)


@when('I send a POST request to "/" with the malformed payload')
def send_post_malformed_payload(client, context):
    """Send POST request with malformed JSON payload"""
    # Send raw malformed JSON string
    context["response"] = client.post(
        "/",
        data=context["malformed_payload"],
        headers={"Content-Type": "application/json"},
    )


@when(
    'I send a POST request to "/" with the primary document and incorrectly formatted candidates'
)
def send_post_invalid_candidates_format(client, context):
    """Send POST request with candidates in wrong format"""
    payload = {
        "document": context["primary_document"],
        "candidate-documents": context[
            "candidate_documents"
        ],  # This is a single object, not array
    }
    context["response"] = client.post("/", json=payload)


@when('I send a POST request to "/" with an unsupported Content-Type header')
def send_post_unsupported_content_type(client, context):
    """Send POST request with unsupported content type"""
    context["response"] = client.post(
        "/", data=context["document_data"], headers={"Content-Type": "text/plain"}
    )


@when('I send a POST request to "/" with the invalid payload')
def send_post_invalid_payload(client, context):
    """Send POST request with invalid payload structure"""
    context["response"] = client.post("/", json=context["invalid_payload"])


@when('I send a POST request to "/" with the empty body')
def send_post_empty_body(client, context):
    """Send POST request with empty body"""
    context["response"] = client.post(
        "/", data="", headers={"Content-Type": "application/json"}
    )


@when('I send a GET request to "/"')
def send_get_request(client, context):
    """Send GET request to root endpoint"""
    context["response"] = client.get("/")


@when('I send a POST request to "/" with the request')
def send_post_with_request(client, context):
    """Send POST request with special request types"""
    if context.get("null_document"):
        payload = {
            "document": None,
            "candidate-documents": context["candidate_documents"],
        }
    elif context.get("document_as_string"):
        payload = {
            "document": context["document_as_string"],
            "candidate-documents": context["candidate_documents"],
        }
    else:
        payload = {
            "document": context["primary_document"],
            "candidate-documents": context["candidate_documents"],
        }
    context["response"] = client.post("/", json=payload)


@when('I send a POST request to "/" with the primary document and null candidates')
def send_post_null_candidates(client, context):
    """Send POST request with null candidate documents"""
    payload = {"document": context["primary_document"], "candidate-documents": None}
    context["response"] = client.post("/", json=payload)


@then("the response body should contain a clear error message")
def response_contains_clear_error(context):
    """Check that response contains a clear error message"""
    try:
        response_data = context["response"].json()
        # Check for error message in various possible fields
        error_fields = ["detail", "message", "error", "errors"]
        has_error_message = any(field in response_data for field in error_fields)
        assert (
            has_error_message
        ), f"Response should contain error message in one of {error_fields}, got: {response_data}"

        # Ensure error message is not empty
        for field in error_fields:
            if field in response_data:
                error_value = response_data[field]
                if isinstance(error_value, str):
                    assert (
                        len(error_value.strip()) > 0
                    ), f"Error message in '{field}' should not be empty"
                elif isinstance(error_value, list):
                    assert (
                        len(error_value) > 0
                    ), f"Error list in '{field}' should not be empty"
                break
    except json.JSONDecodeError:
        # If response is not JSON, check if it contains error text
        response_text = context["response"].text
        assert len(response_text) > 0, "Response should contain error text"


@then("the error message should indicate the missing primary document")
def error_indicates_missing_primary(context):
    """Check that error message indicates missing primary document"""
    response_data = context["response"].json()
    error_message = str(
        response_data.get(
            "detail", response_data.get("message", response_data.get("error", ""))
        )
    )
    error_keywords = ["primary", "document", "missing", "required"]

    # Check if error message contains relevant keywords
    message_lower = error_message.lower()
    found_keywords = [keyword for keyword in error_keywords if keyword in message_lower]
    assert (
        len(found_keywords) >= 2
    ), f"Error message should mention primary document being missing. Found keywords: {found_keywords}, Message: {error_message}"


@then("the error message should indicate the format issue")
def error_indicates_format_issue(context):
    """Check that error message indicates format issue"""
    response_data = context["response"].json()
    error_message = str(
        response_data.get(
            "detail", response_data.get("message", response_data.get("error", ""))
        )
    )
    format_keywords = ["format", "invalid", "structure", "schema"]

    message_lower = error_message.lower()
    found_keywords = [
        keyword for keyword in format_keywords if keyword in message_lower
    ]
    assert (
        len(found_keywords) >= 1
    ), f"Error message should mention format issue. Found keywords: {found_keywords}, Message: {error_message}"


@then("the error message should indicate the JSON parsing issue")
def error_indicates_json_parsing_issue(context):
    """Check that error message indicates JSON parsing issue"""
    response_data = context["response"].json()
    error_message = str(
        response_data.get(
            "detail", response_data.get("message", response_data.get("error", ""))
        )
    )
    json_keywords = ["json", "parsing", "malformed", "syntax"]

    message_lower = error_message.lower()
    found_keywords = [keyword for keyword in json_keywords if keyword in message_lower]
    assert (
        len(found_keywords) >= 1
    ), f"Error message should mention JSON parsing issue. Found keywords: {found_keywords}, Message: {error_message}"


@then("the error message should indicate that candidates must be an array")
def error_indicates_candidates_array_requirement(context):
    """Check that error message indicates candidates must be an array"""
    response_data = context["response"].json()
    error_message = str(
        response_data.get(
            "detail", response_data.get("message", response_data.get("error", ""))
        )
    )
    array_keywords = ["array", "list", "candidates", "must be"]

    message_lower = error_message.lower()
    found_keywords = [keyword for keyword in array_keywords if keyword in message_lower]
    assert (
        len(found_keywords) >= 2
    ), f"Error message should mention candidates must be array. Found keywords: {found_keywords}, Message: {error_message}"


@then("the error message should indicate the unsupported content type")
def error_indicates_unsupported_content_type(context):
    """Check that error message indicates unsupported content type"""
    response_data = context["response"].json()
    error_message = str(
        response_data.get(
            "detail", response_data.get("message", response_data.get("error", ""))
        )
    )
    content_type_keywords = ["content", "type", "unsupported", "media"]

    message_lower = error_message.lower()
    found_keywords = [
        keyword for keyword in content_type_keywords if keyword in message_lower
    ]
    assert (
        len(found_keywords) >= 2
    ), f"Error message should mention unsupported content type. Found keywords: {found_keywords}, Message: {error_message}"


@then("the error message should specify which required fields are missing")
def error_specifies_missing_fields(context):
    """Check that error message specifies which required fields are missing"""
    response_data = context["response"].json()
    error_message = str(
        response_data.get(
            "detail", response_data.get("message", response_data.get("error", ""))
        )
    )
    field_keywords = ["field", "required", "missing", "id", "kind"]

    message_lower = error_message.lower()
    found_keywords = [keyword for keyword in field_keywords if keyword in message_lower]
    assert (
        len(found_keywords) >= 2
    ), f"Error message should specify missing required fields. Found keywords: {found_keywords}, Message: {error_message}"


@then("the error message should specify which fields have invalid values")
def error_specifies_invalid_field_values(context):
    """Check that error message specifies which fields have invalid values"""
    response_data = context["response"].json()
    error_message = str(
        response_data.get(
            "detail", response_data.get("message", response_data.get("error", ""))
        )
    )
    validation_keywords = ["invalid", "value", "field", "validation"]

    message_lower = error_message.lower()
    found_keywords = [
        keyword for keyword in validation_keywords if keyword in message_lower
    ]
    assert (
        len(found_keywords) >= 2
    ), f"Error message should specify invalid field values. Found keywords: {found_keywords}, Message: {error_message}"


@then("the error message should be machine-readable")
def error_message_machine_readable(context):
    """Check that error message is machine-readable (structured JSON)"""
    try:
        response_data = context["response"].json()
        # Check that response is valid JSON with structured error information
        assert isinstance(response_data, dict), "Error response should be a JSON object"

        # Should have at least one standard error field
        standard_fields = ["detail", "message", "error", "errors", "type"]
        has_standard_field = any(field in response_data for field in standard_fields)
        assert (
            has_standard_field
        ), f"Error response should have at least one standard error field from {standard_fields}"

    except json.JSONDecodeError:
        pytest.fail("Error response should be valid JSON for machine readability")


@then("the error message should indicate method not allowed")
def error_indicates_method_not_allowed(context):
    """Check that error message indicates method not allowed"""
    response_data = context["response"].json()
    error_message = str(
        response_data.get(
            "detail", response_data.get("message", response_data.get("error", ""))
        )
    )
    method_keywords = ["method", "not", "allowed"]

    message_lower = error_message.lower()
    found_keywords = [
        keyword for keyword in method_keywords if keyword in message_lower
    ]
    assert (
        len(found_keywords) >= 2
    ), f"Error message should mention method not allowed. Found keywords: {found_keywords}, Message: {error_message}"
