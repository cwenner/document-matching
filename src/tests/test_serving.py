import sys
import os
from fastapi.testclient import TestClient


# Adjust import dir for tests
module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)


# --- Setup ---
# Test client
from app import app
client = TestClient(app)


# --- Sample Data ---
# Use ids that will deterministically trigger match/no-match in dummy logic
# Which? Hard-coded for now
DUMMY_DOC_NO_MATCH = {
    "id": "id-even-hash-for-no-match", # May need updating
    "kind": "invoice",
    "site": "non-whitelisted-site",
    "stage": "input",
    "items": []
}

DUMMY_DOC_MATCH = {
    "id": "id-odd-hash-for-match", # May need updating
    "kind": "invoice",
    "site": "non-whitelisted-site",
    "stage": "input",
    "items": []
}

# --- Tests ---

def test_readiness_endpoint():
    """Test the GET / endpoint for readiness."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Ready to match" in response.text


def test_post_missing_document():
    """Test POST / with missing 'document' field."""
    payload = {"candidate_documents": []}
    response = client.post("/", json=payload)
    assert response.status_code == 400
    assert "Missing or invalid 'document'" in response.json()["detail"]


def test_post_invalid_candidates():
    """Test POST / with 'candidate_documents' not being a list."""
    payload = {"document": DUMMY_DOC_NO_MATCH, "candidate_documents": "not-a-list"}
    response = client.post("/", json=payload)
    assert response.status_code == 400
    assert "Invalid 'candidate_documents' format" in response.json()["detail"]


def test_post_non_whitelisted_site_dummy_no_match():
    """Test POST / for a non-whitelisted site, expecting dummy 'no-match'."""
    payload = {"document": DUMMY_DOC_NO_MATCH, "candidate_documents": []}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert report["version"] == "v3"
    assert report["kind"] == "match-report"
    assert report["site"] == DUMMY_DOC_NO_MATCH["site"]
    assert report["labels"] == ["no-match"]
    assert len(report["documents"]) == 1
    assert report["documents"][0]["id"] == DUMMY_DOC_NO_MATCH["id"]
    assert report["documents"][0]["kind"] == DUMMY_DOC_NO_MATCH["kind"]


def test_post_non_whitelisted_site_dummy_match():
    """Test POST / for a non-whitelisted site, expecting dummy 'match'."""
    payload = {"document": DUMMY_DOC_MATCH, "candidate_documents": []}
    response = client.post("/", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert report["version"] == "v3"
    assert report["kind"] == "match-report"
    assert report["site"] == DUMMY_DOC_MATCH["site"]
    assert report["labels"] == ["match"]
    assert len(report["documents"]) == 2 # Dummy match has 2 docs
    assert report["documents"][0]["id"] == DUMMY_DOC_MATCH["id"]
    assert report["documents"][0]["kind"] == DUMMY_DOC_MATCH["kind"]
