from pytest_bdd import scenario, given, when, then, parsers

# --- Feature: API Readiness and Health Checks ---


# Background
@given(parsers.parse('the matching service is expected to be running at "{base_url}"'))
def matching_service_base_url(context, base_url):
    context.base_url = base_url


@scenario(
    "../../features/api/readiness_health.feature",
    "Readiness probe indicates service is ready",
)
def test_readiness_probe():
    pass


@scenario(
    "../../features/api/readiness_health.feature",
    "Liveness probe indicates service is healthy",
)
def test_liveness_probe():
    pass


# --- Common When Step ---
@when(parsers.parse('I send a GET request to "{path}"'))
def send_get_request(context, mock_http_client, path):
    full_url = context.base_url + path

    # Get the pre-configured mock_response object from the mock_http_client fixture
    response_mock = mock_http_client.get.return_value
    response_mock.status_code = 200  # Ensure status code is 200 for these scenarios

    if path == "/health/readiness":
        response_mock.json.return_value = {"status": "READY"}
    elif path == "/health/liveness":
        response_mock.json.return_value = {"status": "HEALTHY"}
    else:
        # Default or raise error if path not expected for this test file
        response_mock.json.return_value = {}

    context.response = mock_http_client.get(full_url)
    mock_http_client.get.assert_called_with(full_url)


@then(parsers.parse("the response status code should be {status_code:d}"))
def response_status_code(context, status_code):
    assert context.response.status_code == status_code


@then(
    parsers.parse(
        'the JSON response should contain a field "{field_name}" with value "{field_value}"'
    )
)
def json_response_contains_field_value(context, field_name, field_value):
    response_json = context.response.json()
    assert (
        field_name in response_json
    ), f"Field '{field_name}' not in response {response_json}"
    assert (
        str(response_json[field_name]) == field_value
    ), f"Field '{field_name}' value mismatch: expected '{field_value}', got '{response_json[field_name]}'"
