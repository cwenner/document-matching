import pytest


@pytest.fixture
def context():
    """Scenario context for sharing state between steps."""

    class Context:
        def __init__(self):
            # Initialize test state attributes
            self.response = None
            self.request_kwargs = {}
            self.client = None  # For general purpose client
            # Add more as needed

    ctx = Context()
    yield ctx
    # Optional teardown: ctx.cleanup()


@pytest.fixture
def mock_http_client(mocker):
    """Create a mock HTTP client (e.g., for requests library)."""
    client = mocker.MagicMock()
    # Default successful response
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_response.text = ""
    client.get.return_value = mock_response
    client.post.return_value = mock_response
    client.put.return_value = mock_response
    client.delete.return_value = mock_response
    return client
