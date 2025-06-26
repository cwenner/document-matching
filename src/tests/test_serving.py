import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import patch


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
    assert "Missing or invalid 'document'" in response.json()["detail"]


def test_post_invalid_candidates():
    """Test POST / with 'candidate-documents' not being a list."""
    payload = {"document": DUMMY_DOC, "candidate-documents": "not-a-list"}
    response = client.post("/", json=payload)
    assert response.status_code == 400
    assert "Invalid 'candidate-documents' format" in response.json()["detail"]


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
