"""
Unit tests for rate limiting functionality.
"""

import os

import pytest
from fastapi.testclient import TestClient

import app


@pytest.fixture
def client():
    """Test client for the FastAPI app"""
    return TestClient(app.app)


def create_test_document():
    """Create a minimal test document."""
    return {
        "version": "v3",
        "id": "TEST-001",
        "kind": "invoice",
        "site": "test-site",
        "stage": "input",
        "headers": [
            {"name": "supplierId", "value": "SUP-001"},
            {"name": "invoiceNumber", "value": "INV-001"},
        ],
        "items": [],
    }


def test_rate_limiting_disabled_by_default(client):
    """Test that requests work when rate limiting is disabled."""
    payload = {
        "document": create_test_document(),
        "candidate-documents": [],
    }

    # Should be able to make many requests without hitting rate limit
    for _ in range(10):
        response = client.post("/", json=payload)
        assert response.status_code != 429


def test_health_endpoints_always_accessible(client):
    """Test that health check endpoints are always accessible."""
    # Health endpoints should always work regardless of rate limiting
    for _ in range(10):
        response = client.get("/health")
        assert response.status_code == 200

        response = client.get("/health/readiness")
        assert response.status_code == 200

        response = client.get("/health/liveness")
        assert response.status_code == 200
