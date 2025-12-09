"""Tests for external service client with circuit breaker."""

from unittest.mock import Mock, patch

import pytest
import requests

from src.circuit_breaker import CircuitBreakerError, CircuitState
from src.external_service_client import (
    get_all_circuit_breaker_statuses,
    get_circuit_breaker,
    get_circuit_breaker_status,
    protected_delete,
    protected_get,
    protected_post,
    protected_put,
    protected_request,
    reset_circuit_breaker,
)


class TestCircuitBreakerManagement:
    """Test circuit breaker management functions."""

    def test_get_circuit_breaker_creates_new_breaker(self):
        """Getting a breaker for a new service should create it."""
        breaker = get_circuit_breaker("test-service-1")
        assert breaker is not None
        assert breaker.state == CircuitState.CLOSED

    def test_get_circuit_breaker_reuses_existing(self):
        """Getting a breaker for existing service should return same instance."""
        breaker1 = get_circuit_breaker("test-service-2")
        breaker2 = get_circuit_breaker("test-service-2")
        assert breaker1 is breaker2

    def test_get_circuit_breaker_with_custom_params(self):
        """Circuit breaker should be created with custom parameters."""
        breaker = get_circuit_breaker(
            "test-service-3", failure_threshold=10, recovery_timeout=120
        )
        assert breaker.failure_threshold == 10
        assert breaker.recovery_timeout == 120

    def test_reset_circuit_breaker_existing_service(self):
        """Resetting existing service should return True."""
        breaker = get_circuit_breaker("test-service-4")
        result = reset_circuit_breaker("test-service-4")
        assert result is True

    def test_reset_circuit_breaker_nonexistent_service(self):
        """Resetting non-existent service should return False."""
        result = reset_circuit_breaker("nonexistent-service")
        assert result is False

    def test_get_circuit_breaker_status_existing(self):
        """Getting status of existing breaker should return dict."""
        breaker = get_circuit_breaker("test-service-5")
        status = get_circuit_breaker_status("test-service-5")
        assert status is not None
        assert "state" in status
        assert status["state"] == CircuitState.CLOSED.value

    def test_get_circuit_breaker_status_nonexistent(self):
        """Getting status of non-existent service should return None."""
        status = get_circuit_breaker_status("nonexistent-service-2")
        assert status is None

    def test_get_all_circuit_breaker_statuses(self):
        """Getting all statuses should return dict of all breakers."""
        get_circuit_breaker("service-a")
        get_circuit_breaker("service-b")

        statuses = get_all_circuit_breaker_statuses()
        assert isinstance(statuses, dict)
        assert "service-a" in statuses
        assert "service-b" in statuses


class TestProtectedRequest:
    """Test protected_request function."""

    @patch("src.external_service_client.requests.request")
    def test_successful_request(self, mock_request):
        """Successful request should return response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = protected_request(
            "GET", "https://api.example.com/test", service_name="test-api"
        )

        assert response.status_code == 200
        mock_request.assert_called_once()

    @patch("src.external_service_client.requests.request")
    def test_failed_requests_open_circuit(self, mock_request):
        """Multiple failed requests should open circuit."""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # Make requests until circuit opens
        for i in range(5):
            with pytest.raises(requests.exceptions.ConnectionError):
                protected_request(
                    "GET",
                    "https://api.example.com/test",
                    service_name="failing-api",
                    failure_threshold=5,
                )

        # Next request should be blocked by circuit breaker
        with pytest.raises(CircuitBreakerError):
            protected_request(
                "GET",
                "https://api.example.com/test",
                service_name="failing-api",
                failure_threshold=5,
            )

        # Verify circuit is open
        status = get_circuit_breaker_status("failing-api")
        assert status["state"] == CircuitState.OPEN.value

    @patch("src.external_service_client.requests.request")
    def test_service_name_derived_from_url(self, mock_request):
        """Service name should be derived from URL if not provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        protected_request("GET", "https://api.example.com/endpoint")

        # Check that a breaker was created with derived name
        statuses = get_all_circuit_breaker_statuses()
        assert "https://api.example.com" in statuses

    @patch("src.external_service_client.requests.request")
    def test_request_with_additional_kwargs(self, mock_request):
        """Request should pass through additional kwargs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        protected_request(
            "POST",
            "https://api.example.com/data",
            service_name="test-api-2",
            json={"key": "value"},
            headers={"Authorization": "Bearer token"},
            timeout=30,
        )

        # Verify kwargs were passed
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"] == {"key": "value"}
        assert call_kwargs["headers"] == {"Authorization": "Bearer token"}
        assert call_kwargs["timeout"] == 30


class TestProtectedHTTPMethods:
    """Test convenience methods for HTTP verbs."""

    @patch("src.external_service_client.requests.request")
    def test_protected_get(self, mock_request):
        """protected_get should make GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = protected_get("https://api.example.com/resource", service_name="get-api")

        assert response.status_code == 200
        mock_request.assert_called_once()
        assert mock_request.call_args[0][0] == "GET"

    @patch("src.external_service_client.requests.request")
    def test_protected_post(self, mock_request):
        """protected_post should make POST request."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response

        response = protected_post(
            "https://api.example.com/resource",
            service_name="post-api",
            json={"data": "value"},
        )

        assert response.status_code == 201
        mock_request.assert_called_once()
        assert mock_request.call_args[0][0] == "POST"

    @patch("src.external_service_client.requests.request")
    def test_protected_put(self, mock_request):
        """protected_put should make PUT request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = protected_put(
            "https://api.example.com/resource/1",
            service_name="put-api",
            json={"data": "updated"},
        )

        assert response.status_code == 200
        mock_request.assert_called_once()
        assert mock_request.call_args[0][0] == "PUT"

    @patch("src.external_service_client.requests.request")
    def test_protected_delete(self, mock_request):
        """protected_delete should make DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        response = protected_delete(
            "https://api.example.com/resource/1", service_name="delete-api"
        )

        assert response.status_code == 204
        mock_request.assert_called_once()
        assert mock_request.call_args[0][0] == "DELETE"


class TestCircuitBreakerIntegration:
    """Test integration scenarios with circuit breaker."""

    @patch("src.external_service_client.requests.request")
    def test_circuit_breaker_prevents_cascading_failures(self, mock_request):
        """Circuit breaker should prevent cascading failures."""
        # Simulate service degradation
        mock_request.side_effect = requests.exceptions.Timeout("Service timeout")

        service_name = "degraded-service"
        call_count = 0

        # Make requests until circuit opens
        for _ in range(5):
            try:
                protected_request(
                    "GET",
                    "https://degraded.example.com/api",
                    service_name=service_name,
                    failure_threshold=5,
                )
            except requests.exceptions.Timeout:
                call_count += 1

        # Circuit should be open, preventing further actual requests
        for _ in range(10):
            with pytest.raises(CircuitBreakerError):
                protected_request(
                    "GET",
                    "https://degraded.example.com/api",
                    service_name=service_name,
                    failure_threshold=5,
                )

        # Verify that no additional requests were made after circuit opened
        assert mock_request.call_count == 5

    @patch("src.external_service_client.requests.request")
    def test_manual_reset_allows_immediate_retry(self, mock_request):
        """Manual reset should allow immediate retry without waiting."""
        # Open the circuit
        mock_request.side_effect = requests.exceptions.ConnectionError("Failed")

        service_name = "manual-reset-service"

        for _ in range(5):
            with pytest.raises(requests.exceptions.ConnectionError):
                protected_request(
                    "GET",
                    "https://api.example.com/test",
                    service_name=service_name,
                    failure_threshold=5,
                )

        # Verify circuit is open
        status = get_circuit_breaker_status(service_name)
        assert status["state"] == CircuitState.OPEN.value

        # Manual reset
        reset_circuit_breaker(service_name)

        # Service is back up
        mock_request.side_effect = None
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Should be able to make request immediately
        response = protected_request(
            "GET", "https://api.example.com/test", service_name=service_name
        )
        assert response.status_code == 200

        # Circuit should be closed
        status = get_circuit_breaker_status(service_name)
        assert status["state"] == CircuitState.CLOSED.value
