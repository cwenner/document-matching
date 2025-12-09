import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


DUMMY_DOC = {
    "id": "123",
    "kind": "invoice",
    "site": "non-whitelisted-site",
    "stage": "input",
    "items": [],
}


def test_readiness_endpoint():
    """Test the GET /health endpoint for readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "Ready to match" in response.text


def test_post_missing_document():
    """Test POST / with missing 'document' field."""
    payload = {"candidate-documents": []}
    response = client.post("/", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "document" in detail and ("required" in detail or "missing" in detail)


def test_post_invalid_candidates():
    """Test POST / with 'candidate-documents' not being a list."""
    payload = {"document": DUMMY_DOC, "candidate-documents": "not-a-list"}
    response = client.post("/", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "candidate" in detail and ("list" in detail or "array" in detail)


def test_post_non_whitelisted_site_dummy_no_match():
    """Test POST / for a non-whitelisted site, expecting dummy 'no-match'."""
    payload = {"document": DUMMY_DOC, "candidate-documents": []}
    with patch("builtins.hash", return_value=0):
        response = client.post("/", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert report["version"] == "v3"
    assert report["kind"] == "match-report"
    assert report["site"] == DUMMY_DOC["site"]
    assert report["labels"] == ["no-match"]
    assert len(report["documents"]) == 1
    assert report["documents"][0]["id"] == DUMMY_DOC["id"]
    assert report["documents"][0]["kind"] == DUMMY_DOC["kind"]


def test_post_non_whitelisted_site_dummy_match():
    """Test POST / for a non-whitelisted site, expecting dummy 'match'."""
    payload = {"document": DUMMY_DOC, "candidate-documents": []}
    with patch("builtins.hash", return_value=1):
        response = client.post("/", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert report["version"] == "v3"
    assert report["kind"] == "match-report"
    assert report["site"] == DUMMY_DOC["site"]
    assert report["labels"] == ["match"]
    assert len(report["documents"]) == 2  # Dummy match has 2 docs
    assert report["documents"][0]["id"] == DUMMY_DOC["id"]
    assert report["documents"][0]["kind"] == DUMMY_DOC["kind"]


def test_request_id_generated_when_not_provided():
    """Test that X-Request-ID is generated when not provided in request."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    # Verify it's a valid UUID
    request_id = response.headers["X-Request-ID"]
    try:
        uuid.UUID(request_id)
    except ValueError:
        assert False, f"Generated request ID is not a valid UUID: {request_id}"


def test_request_id_preserved_when_provided():
    """Test that X-Request-ID is preserved when provided in request."""
    test_request_id = "test-request-id-12345"
    response = client.get("/health", headers={"X-Request-ID": test_request_id})
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == test_request_id


def test_request_id_in_health_readiness_endpoint():
    """Test that X-Request-ID is returned from /health/readiness endpoint."""
    test_request_id = "readiness-test-id"
    response = client.get(
        "/health/readiness", headers={"X-Request-ID": test_request_id}
    )
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == test_request_id


def test_request_id_in_health_liveness_endpoint():
    """Test that X-Request-ID is returned from /health/liveness endpoint."""
    test_request_id = "liveness-test-id"
    response = client.get(
        "/health/liveness", headers={"X-Request-ID": test_request_id}
    )
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == test_request_id


def test_request_id_in_post_request():
    """Test that X-Request-ID is returned from POST / endpoint."""
    test_request_id = "post-test-id"
    payload = {"document": DUMMY_DOC, "candidate-documents": []}
    with patch("builtins.hash", return_value=0):
        response = client.post(
            "/", json=payload, headers={"X-Request-ID": test_request_id}
        )
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == test_request_id


def test_request_id_in_error_response():
    """Test that X-Request-ID is returned in error responses."""
    test_request_id = "error-test-id"
    payload = {"candidate-documents": []}  # Missing document field
    response = client.post("/", json=payload, headers={"X-Request-ID": test_request_id})
    assert response.status_code == 400
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == test_request_id


def test_request_id_in_validation_error():
    """Test that X-Request-ID is returned in validation error responses."""
    test_request_id = "validation-error-test-id"
    payload = {"document": DUMMY_DOC, "candidate-documents": "not-a-list"}
    response = client.post("/", json=payload, headers={"X-Request-ID": test_request_id})
    assert response.status_code == 400
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == test_request_id
