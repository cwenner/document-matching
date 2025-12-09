"""
External service client with circuit breaker protection.

This module provides helper functions for making external service calls
with automatic circuit breaker protection to prevent cascading failures.
"""

import logging
from typing import Any, Dict, Optional

import requests

from src.circuit_breaker import CircuitBreaker, CircuitBreakerError, circuit_breaker

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("external_service_client")


# Global circuit breaker instances for different services
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    success_threshold: int = 2,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a named service.

    Args:
        service_name: Unique identifier for the service
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        success_threshold: Consecutive successes needed to close from half-open

    Returns:
        CircuitBreaker instance for the service
    """
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            expected_exceptions=(
                requests.exceptions.RequestException,
                ConnectionError,
                TimeoutError,
            ),
        )
        logger.info(f"Created circuit breaker for service: {service_name}")

    return _circuit_breakers[service_name]


def reset_circuit_breaker(service_name: str) -> bool:
    """
    Manually reset a circuit breaker for a service.

    Args:
        service_name: Name of the service

    Returns:
        True if breaker was reset, False if service not found
    """
    if service_name in _circuit_breakers:
        _circuit_breakers[service_name].reset()
        logger.info(f"Reset circuit breaker for service: {service_name}")
        return True
    return False


def get_circuit_breaker_status(service_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a circuit breaker.

    Args:
        service_name: Name of the service

    Returns:
        Dictionary with breaker status, or None if service not found
    """
    if service_name in _circuit_breakers:
        return _circuit_breakers[service_name].get_status()
    return None


def get_all_circuit_breaker_statuses() -> Dict[str, Dict[str, Any]]:
    """
    Get status of all circuit breakers.

    Returns:
        Dictionary mapping service names to their breaker statuses
    """
    return {name: breaker.get_status() for name, breaker in _circuit_breakers.items()}


def protected_request(
    method: str,
    url: str,
    service_name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    **kwargs: Any,
) -> requests.Response:
    """
    Make an HTTP request with circuit breaker protection.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        service_name: Name for the circuit breaker (default: derived from URL)
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        **kwargs: Additional arguments passed to requests.request()

    Returns:
        Response object from requests

    Raises:
        CircuitBreakerError: If circuit breaker is open
        requests.RequestException: For HTTP errors

    Example:
        response = protected_request(
            "POST",
            "https://api.example.com/match",
            json={"data": "value"},
            timeout=30
        )
    """
    # Derive service name from URL if not provided
    if service_name is None:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        service_name = f"{parsed.scheme}://{parsed.netloc}"

    # Get or create circuit breaker for this service
    breaker = get_circuit_breaker(
        service_name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
    )

    # Make request with circuit breaker protection
    try:
        response = breaker.call(requests.request, method, url, **kwargs)
        logger.debug(
            f"Protected request to {url} completed: {response.status_code}"
        )
        return response
    except CircuitBreakerError:
        logger.error(
            f"Circuit breaker is OPEN for service {service_name}. Request to {url} blocked."
        )
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to {url} failed: {e}")
        raise


def protected_get(url: str, **kwargs: Any) -> requests.Response:
    """
    Make a GET request with circuit breaker protection.

    Args:
        url: URL to request
        **kwargs: Additional arguments passed to protected_request()

    Returns:
        Response object
    """
    return protected_request("GET", url, **kwargs)


def protected_post(url: str, **kwargs: Any) -> requests.Response:
    """
    Make a POST request with circuit breaker protection.

    Args:
        url: URL to request
        **kwargs: Additional arguments passed to protected_request()

    Returns:
        Response object
    """
    return protected_request("POST", url, **kwargs)


def protected_put(url: str, **kwargs: Any) -> requests.Response:
    """
    Make a PUT request with circuit breaker protection.

    Args:
        url: URL to request
        **kwargs: Additional arguments passed to protected_request()

    Returns:
        Response object
    """
    return protected_request("PUT", url, **kwargs)


def protected_delete(url: str, **kwargs: Any) -> requests.Response:
    """
    Make a DELETE request with circuit breaker protection.

    Args:
        url: URL to request
        **kwargs: Additional arguments passed to protected_request()

    Returns:
        Response object
    """
    return protected_request("DELETE", url, **kwargs)
