import sys
import os
from fastapi.testclient import TestClient


# Adjust import dir for tests
module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)


from app import app, WHITELISTED_SITES

# --- Test Client ---
client = TestClient(app)


# --- Sample Data ---

WHITELISTED_DOC = {
    "id": "whitelisted-doc-1",
    "kind": "invoice",
    "site": next(iter(WHITELISTED_SITES)),
    "stage": "input",
    "items": [{"fields": [{"name": "text", "value": "Item 1"}]}],
}

CANDIDATE_DOCS = [
    {
        "id": "candidate-doc-1",
        "kind": "purchase-order",
        "site": next(iter(WHITELISTED_SITES)),
        "stage": "historical",
        "items": [{"fields": [{"name": "description", "value": "Item 1 PO"}]}],
    }
]

# --- Tests ---


def test_post_whitelisted_site_pipeline():
    """
    Test real prediction POST / for a whitelisted site.
    """
    payload = {"document": WHITELISTED_DOC, "candidate_documents": CANDIDATE_DOCS}
    response = client.post("/", json=payload)

    # Expecting 200 OK even for no-match
    assert response.status_code == 200

    report = response.json()
    assert report["version"] == "v3"  # Check adaptation
    assert report["kind"] == "match-report"
    assert report["site"] == WHITELISTED_DOC["site"]
    assert "labels" in report  # Should have labels like "match" or "no-match"
    assert isinstance(report["labels"], list)
    assert "documents" in report
    assert isinstance(report["documents"], list)
    assert len(report["documents"]) >= 1  # At least the input document
    # @TODO more in depth prediction
    assert report["documents"][0]["id"] == WHITELISTED_DOC["id"]
