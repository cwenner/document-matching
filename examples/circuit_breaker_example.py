"""
Example usage of circuit breaker pattern for external service calls.

This file demonstrates how to integrate the circuit breaker pattern
into your application to protect against cascading failures.
"""

import logging
import time

import requests

from src.circuit_breaker import CircuitBreakerError, circuit_breaker
from src.external_service_client import (
    get_all_circuit_breaker_statuses,
    get_circuit_breaker_status,
    protected_post,
    reset_circuit_breaker,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example 1: Using the decorator
@circuit_breaker(failure_threshold=3, recovery_timeout=30)
def fetch_user_data(user_id: str) -> dict:
    """
    Fetch user data from external API with circuit breaker protection.
    """
    response = requests.get(f"https://api.example.com/users/{user_id}", timeout=5)
    response.raise_for_status()
    return response.json()


# Example 2: Using protected_post for making API calls
def match_documents(document: dict, candidates: list) -> dict:
    """
    Match documents using external API with circuit breaker protection.

    If the circuit is open, returns a fallback response instead of failing.
    """
    try:
        response = protected_post(
            "https://matching-api.example.com/match",
            service_name="document-matching",
            json={"document": document, "candidates": candidates},
            timeout=30,
            failure_threshold=5,
            recovery_timeout=60,
        )
        return response.json()

    except CircuitBreakerError:
        logger.warning("Matching service circuit is open, using fallback")
        # Return a fallback response
        return {
            "status": "degraded",
            "message": "Matching service temporarily unavailable",
            "fallback": True,
        }

    except requests.RequestException as e:
        logger.error(f"Matching service request failed: {e}")
        raise


# Example 3: Monitoring circuit breaker health
def check_service_health():
    """
    Check the health of all circuit breakers and report status.
    """
    statuses = get_all_circuit_breaker_statuses()

    if not statuses:
        logger.info("No circuit breakers currently active")
        return

    for service_name, status in statuses.items():
        state = status["state"]
        failures = status["failure_count"]
        threshold = status["failure_threshold"]

        if state == "open":
            logger.warning(
                f"⚠️  {service_name}: Circuit OPEN ({failures}/{threshold} failures)"
            )
        elif state == "half_open":
            logger.info(
                f"🔄 {service_name}: Circuit HALF_OPEN (testing recovery)"
            )
        else:
            logger.info(f"✅ {service_name}: Circuit CLOSED (healthy)")


# Example 4: Manual circuit breaker reset
def admin_reset_circuit(service_name: str) -> bool:
    """
    Manually reset a circuit breaker (admin operation).

    Use this when you know a service has recovered and want to
    immediately allow traffic again without waiting for the timeout.
    """
    if reset_circuit_breaker(service_name):
        logger.info(f"Successfully reset circuit breaker for {service_name}")
        return True
    else:
        logger.error(f"Circuit breaker not found for {service_name}")
        return False


# Example 5: Graceful degradation with retry logic
def robust_api_call(url: str, data: dict, max_retries: int = 3) -> dict:
    """
    Make an API call with circuit breaker, retries, and graceful degradation.
    """
    for attempt in range(max_retries):
        try:
            response = protected_post(
                url,
                json=data,
                timeout=10,
                failure_threshold=5,
                recovery_timeout=60,
            )
            return response.json()

        except CircuitBreakerError:
            logger.warning(
                f"Circuit breaker is open for {url}, returning cached result"
            )
            # Return cached or fallback data
            return {"status": "cached", "data": None}

        except requests.Timeout:
            logger.warning(f"Request timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2**attempt
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise


# Example 6: Using circuit breaker in a class
class ExternalServiceClient:
    """
    Client for external service with built-in circuit breaker protection.
    """

    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url
        self.service_name = service_name

    def get_data(self, endpoint: str) -> dict:
        """Fetch data from external service."""
        url = f"{self.base_url}/{endpoint}"

        try:
            response = protected_post(
                url,
                service_name=self.service_name,
                failure_threshold=5,
                recovery_timeout=60,
            )
            return response.json()

        except CircuitBreakerError:
            logger.warning(f"{self.service_name} circuit is open")
            return self._get_fallback_data(endpoint)

    def _get_fallback_data(self, endpoint: str) -> dict:
        """Return fallback data when service is unavailable."""
        return {
            "status": "fallback",
            "message": f"{self.service_name} temporarily unavailable",
            "endpoint": endpoint,
        }

    def check_health(self) -> dict:
        """Check the health of this service's circuit breaker."""
        status = get_circuit_breaker_status(self.service_name)
        if status:
            return {
                "service": self.service_name,
                "state": status["state"],
                "failures": status["failure_count"],
                "healthy": status["state"] == "closed",
            }
        return {"service": self.service_name, "state": "unknown", "healthy": False}


def main():
    """
    Demonstrate circuit breaker usage.
    """
    logger.info("=== Circuit Breaker Examples ===\n")

    # Example 1: Using decorator
    logger.info("Example 1: Decorator-based circuit breaker")
    try:
        user_data = fetch_user_data("123")
        logger.info(f"User data: {user_data}")
    except CircuitBreakerError:
        logger.warning("Circuit is open for user service")
    except Exception as e:
        logger.error(f"Error fetching user data: {e}")

    # Example 2: Protected API call
    logger.info("\nExample 2: Protected API call with fallback")
    result = match_documents(
        {"id": "doc1", "content": "test"}, [{"id": "doc2", "content": "test2"}]
    )
    logger.info(f"Match result: {result}")

    # Example 3: Health monitoring
    logger.info("\nExample 3: Circuit breaker health check")
    check_service_health()

    # Example 4: Using client class
    logger.info("\nExample 4: Service client with circuit breaker")
    client = ExternalServiceClient(
        "https://api.example.com", "external-api"
    )
    health = client.check_health()
    logger.info(f"Service health: {health}")


if __name__ == "__main__":
    main()
