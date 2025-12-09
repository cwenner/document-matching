"""Tests for circuit breaker implementation."""

import time
from unittest.mock import Mock

import pytest

from src.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    circuit_breaker,
)


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state."""
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_successful_calls_keep_circuit_closed(self):
        """Successful calls should keep circuit in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3)
        mock_func = Mock(return_value="success")

        for _ in range(5):
            result = breaker.call(mock_func)
            assert result == "success"
            assert breaker.state == CircuitState.CLOSED

        assert mock_func.call_count == 5

    def test_failures_open_circuit(self):
        """Circuit should open after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3)
        mock_func = Mock(side_effect=RuntimeError("Service unavailable"))

        # First 3 failures should open the circuit
        for i in range(3):
            with pytest.raises(RuntimeError):
                breaker.call(mock_func)
            if i < 2:
                assert breaker.state == CircuitState.CLOSED
            else:
                assert breaker.state == CircuitState.OPEN

        # Circuit is now open, further calls should be blocked
        with pytest.raises(CircuitBreakerError):
            breaker.call(mock_func)

        # Function should not be called when circuit is open
        assert mock_func.call_count == 3

    def test_circuit_transitions_to_half_open_after_timeout(self):
        """Circuit should transition to HALF_OPEN after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        mock_func = Mock(side_effect=RuntimeError("Service unavailable"))

        # Open the circuit
        for _ in range(2):
            with pytest.raises(RuntimeError):
                breaker.call(mock_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN (but will fail)
        mock_func.side_effect = RuntimeError("Still failing")
        with pytest.raises(RuntimeError):
            breaker.call(mock_func)

        # Should be back to OPEN after failure in HALF_OPEN
        assert breaker.state == CircuitState.OPEN

    def test_successful_recovery_closes_circuit(self):
        """Successful calls in HALF_OPEN should close circuit."""
        breaker = CircuitBreaker(
            failure_threshold=2, recovery_timeout=1, success_threshold=2
        )
        mock_func = Mock(side_effect=RuntimeError("Service unavailable"))

        # Open the circuit
        for _ in range(2):
            with pytest.raises(RuntimeError):
                breaker.call(mock_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next calls succeed
        mock_func.side_effect = None
        mock_func.return_value = "success"

        result1 = breaker.call(mock_func)
        assert result1 == "success"
        assert breaker.state == CircuitState.HALF_OPEN

        result2 = breaker.call(mock_func)
        assert result2 == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_manual_reset(self):
        """Manual reset should close circuit regardless of state."""
        breaker = CircuitBreaker(failure_threshold=2)
        mock_func = Mock(side_effect=RuntimeError("Service unavailable"))

        # Open the circuit
        for _ in range(2):
            with pytest.raises(RuntimeError):
                breaker.call(mock_func)

        assert breaker.state == CircuitState.OPEN

        # Manual reset
        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

        # Should be able to call again
        mock_func.side_effect = None
        mock_func.return_value = "success"
        result = breaker.call(mock_func)
        assert result == "success"

    def test_get_status(self):
        """get_status should return current breaker state."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        status = breaker.get_status()

        assert status["state"] == CircuitState.CLOSED.value
        assert status["failure_count"] == 0
        assert status["failure_threshold"] == 3
        assert status["recovery_timeout"] == 60

    def test_expected_exceptions_filter(self):
        """Only expected exceptions should trigger circuit breaker."""
        breaker = CircuitBreaker(
            failure_threshold=2, expected_exceptions=(RuntimeError,)
        )

        # ValueError should not trigger circuit breaker
        mock_func = Mock(side_effect=ValueError("Not monitored"))
        with pytest.raises(ValueError):
            breaker.call(mock_func)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0  # Not counted as failure

        # RuntimeError should trigger circuit breaker
        mock_func.side_effect = RuntimeError("Monitored error")
        with pytest.raises(RuntimeError):
            breaker.call(mock_func)

        with pytest.raises(RuntimeError):
            breaker.call(mock_func)

        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerDecorator:
    """Test circuit_breaker decorator."""

    def test_decorator_wraps_function(self):
        """Decorator should properly wrap function."""

        @circuit_breaker(failure_threshold=2)
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"
        assert hasattr(test_func, "circuit_breaker")

    def test_decorator_opens_circuit_on_failures(self):
        """Decorator should open circuit after failures."""
        call_count = 0

        @circuit_breaker(failure_threshold=2)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Failed")

        # First 2 calls should fail and open circuit
        for _ in range(2):
            with pytest.raises(RuntimeError):
                failing_func()

        # Circuit should be open now
        with pytest.raises(CircuitBreakerError):
            failing_func()

        assert call_count == 2
        assert failing_func.circuit_breaker.state == CircuitState.OPEN

    def test_decorator_with_arguments(self):
        """Decorator should work with function arguments."""

        @circuit_breaker(failure_threshold=3)
        def add_func(a, b):
            return a + b

        result = add_func(2, 3)
        assert result == 5

    def test_decorator_breaker_accessible(self):
        """Circuit breaker instance should be accessible from decorated function."""

        @circuit_breaker(failure_threshold=2, recovery_timeout=30)
        def test_func():
            return "success"

        breaker = test_func.circuit_breaker
        assert isinstance(breaker, CircuitBreaker)
        assert breaker.failure_threshold == 2
        assert breaker.recovery_timeout == 30

        # Should be able to check status
        status = breaker.get_status()
        assert status["state"] == CircuitState.CLOSED.value

        # Should be able to reset
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_failure_threshold(self):
        """Circuit breaker with zero threshold opens immediately on first failure."""
        breaker = CircuitBreaker(failure_threshold=0)
        mock_func = Mock(side_effect=RuntimeError("Failed"))

        # With threshold=0, circuit opens on first failure (>= 0)
        with pytest.raises(RuntimeError):
            breaker.call(mock_func)

        # State should be OPEN because failure_count (1) >= threshold (0)
        assert breaker.state == CircuitState.OPEN

    def test_very_short_recovery_timeout(self):
        """Very short recovery timeout should work correctly."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        mock_func = Mock(side_effect=RuntimeError("Failed"))

        # Open circuit
        with pytest.raises(RuntimeError):
            breaker.call(mock_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for very short timeout
        time.sleep(0.2)

        # Should transition to HALF_OPEN
        mock_func.return_value = "success"
        mock_func.side_effect = None
        result = breaker.call(mock_func)

        assert result == "success"

    def test_success_resets_failure_count_in_closed_state(self):
        """Success should reset failure count when in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3)
        mock_func = Mock()

        # Cause some failures
        mock_func.side_effect = RuntimeError("Failed")
        with pytest.raises(RuntimeError):
            breaker.call(mock_func)

        assert breaker.failure_count == 1

        # Now succeed
        mock_func.side_effect = None
        mock_func.return_value = "success"
        breaker.call(mock_func)

        # Failure count should be reset
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED
