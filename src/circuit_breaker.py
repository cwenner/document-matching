"""
Circuit breaker pattern implementation for external service calls.

This module provides a circuit breaker to prevent cascading failures when
external dependencies become unavailable.
"""

import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Type

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.

    The circuit breaker monitors failures and transitions between states:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Too many failures, calls are blocked immediately
    - HALF_OPEN: Testing recovery, limited calls allowed

    Args:
        failure_threshold: Number of failures before opening circuit (default: 5)
        recovery_timeout: Seconds to wait before attempting recovery (default: 60)
        success_threshold: Consecutive successes needed to close from half-open (default: 2)
        expected_exceptions: Tuple of exception types to count as failures
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return False
        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception raised by func
        """
        # Check if we should transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    f"Circuit breaker transitioning to HALF_OPEN after {self.recovery_timeout}s timeout"
                )
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN. Service calls are blocked. "
                    f"Failures: {self._failure_count}/{self.failure_threshold}"
                )

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Success handling
            self._on_success()
            return result

        except Exception as e:
            # Check if this is an expected exception type
            if isinstance(e, self.expected_exceptions):
                # Failure handling for expected exceptions
                self._on_failure()
            raise e

    def _on_success(self) -> None:
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            logger.info(
                f"Circuit breaker success in HALF_OPEN state: "
                f"{self._success_count}/{self.success_threshold}"
            )

            if self._success_count >= self.success_threshold:
                logger.info(
                    "Circuit breaker transitioning to CLOSED after successful recovery"
                )
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self._last_failure_time = None
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success in CLOSED state
            self._failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        logger.warning(
            f"Circuit breaker recorded failure: "
            f"{self._failure_count}/{self.failure_threshold} in state {self._state.value}"
        )

        if self._state == CircuitState.HALF_OPEN:
            # Single failure in HALF_OPEN immediately reopens circuit
            logger.warning(
                "Circuit breaker transitioning to OPEN after failure in HALF_OPEN state"
            )
            self._state = CircuitState.OPEN
            self._success_count = 0
        elif (
            self._state == CircuitState.CLOSED
            and self._failure_count >= self.failure_threshold
        ):
            # Too many failures in CLOSED state, open the circuit
            logger.error(
                f"Circuit breaker transitioning to OPEN after {self._failure_count} failures"
            )
            self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        logger.info("Circuit breaker manually reset to CLOSED state")
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None

    def get_status(self) -> Dict[str, Any]:
        """
        Get current circuit breaker status.

        Returns:
            Dictionary with state, failure_count, and last_failure_time
        """
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    success_threshold: int = 2,
    expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator to apply circuit breaker pattern to a function.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        success_threshold: Consecutive successes needed to close from half-open
        expected_exceptions: Tuple of exception types to count as failures

    Example:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        def call_external_api():
            return requests.get("https://api.example.com")
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        success_threshold=success_threshold,
        expected_exceptions=expected_exceptions,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)

        # Attach breaker instance to wrapper for access to state/reset
        wrapper.circuit_breaker = breaker  # type: ignore
        return wrapper

    return decorator
