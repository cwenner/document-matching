# Circuit Breaker Pattern Implementation

## Overview

The circuit breaker pattern is implemented to prevent cascading failures when external dependencies become unavailable. This protection mechanism automatically detects failures and temporarily blocks requests to failing services, allowing them time to recover.

## Architecture

### Circuit Breaker States

The circuit breaker operates in three states:

1. **CLOSED** (Normal Operation)
   - All requests pass through normally
   - Failures are counted
   - Transitions to OPEN after reaching failure threshold

2. **OPEN** (Service Degraded)
   - All requests are blocked immediately without calling the service
   - Prevents cascading failures and resource exhaustion
   - Transitions to HALF_OPEN after recovery timeout

3. **HALF_OPEN** (Testing Recovery)
   - Limited requests allowed to test service recovery
   - Transitions to CLOSED after consecutive successes
   - Transitions back to OPEN on any failure

```
┌─────────┐    Failure Threshold    ┌──────┐
│ CLOSED  │────────────────────────>│ OPEN │
└─────────┘                          └──────┘
     ^                                  │
     │                                  │ Recovery Timeout
     │  Success Threshold               │
     │                               ┌──v────────┐
     └───────────────────────────────┤ HALF_OPEN │
                                     └───────────┘
```

## Usage

### Basic Circuit Breaker

```python
from src.circuit_breaker import CircuitBreaker

# Create a circuit breaker
breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Wait 60s before retry
    success_threshold=2       # Need 2 successes to close
)

# Use the circuit breaker
try:
    result = breaker.call(external_api_call, arg1, arg2)
except CircuitBreakerError:
    # Circuit is open, service is degraded
    return fallback_response()
```

### Decorator Usage

```python
from src.circuit_breaker import circuit_breaker

@circuit_breaker(failure_threshold=3, recovery_timeout=30)
def call_external_service():
    return requests.get("https://api.example.com/data")

# Use the function normally
try:
    result = call_external_service()
except CircuitBreakerError:
    # Handle open circuit
    pass

# Access breaker state
status = call_external_service.circuit_breaker.get_status()
print(f"Circuit state: {status['state']}")
```

### Protected HTTP Requests

The `external_service_client` module provides convenience functions for HTTP requests with automatic circuit breaker protection:

```python
from src.external_service_client import protected_post, get_circuit_breaker_status

# Make a protected POST request
try:
    response = protected_post(
        "https://api.example.com/match",
        json={"document": "data"},
        timeout=30,
        failure_threshold=5,  # Optional: override default
        recovery_timeout=60   # Optional: override default
    )
except CircuitBreakerError:
    # Circuit is open for this service
    logger.error("Matching service is unavailable")
    return fallback_response()
except requests.RequestException as e:
    # Service call failed
    logger.error(f"Request failed: {e}")
    return error_response()

# Check circuit breaker status
status = get_circuit_breaker_status("https://api.example.com")
print(f"Service status: {status['state']}")
```

### Named Service Management

```python
from src.external_service_client import (
    get_circuit_breaker,
    reset_circuit_breaker,
    get_all_circuit_breaker_statuses
)

# Get circuit breaker for specific service
breaker = get_circuit_breaker(
    "external-api",
    failure_threshold=10,
    recovery_timeout=120
)

# Manually reset a circuit breaker
reset_circuit_breaker("external-api")

# Get all circuit breaker statuses
statuses = get_all_circuit_breaker_statuses()
for service, status in statuses.items():
    print(f"{service}: {status['state']} ({status['failure_count']} failures)")
```

## Configuration

### Default Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `failure_threshold` | 5 | Number of consecutive failures before opening circuit |
| `recovery_timeout` | 60 | Seconds to wait before attempting recovery |
| `success_threshold` | 2 | Consecutive successes needed to close circuit |

### Recommended Settings by Use Case

**High-availability services:**
```python
CircuitBreaker(
    failure_threshold=3,   # Open quickly
    recovery_timeout=30,   # Retry sooner
    success_threshold=3    # Need more confidence to close
)
```

**Batch processing:**
```python
CircuitBreaker(
    failure_threshold=10,  # More tolerant of failures
    recovery_timeout=300,  # Wait longer before retry
    success_threshold=2    # Standard recovery
)
```

**Critical real-time services:**
```python
CircuitBreaker(
    failure_threshold=2,   # Very sensitive to failures
    recovery_timeout=15,   # Quick recovery attempts
    success_threshold=5    # High confidence needed
)
```

## Monitoring

### Health Endpoint

The service exposes circuit breaker status via health endpoint:

```bash
curl http://localhost:8000/health/circuit-breakers
```

Response:
```json
{
  "circuit_breakers": {
    "https://api.example.com": {
      "state": "closed",
      "failure_count": 0,
      "success_count": 0,
      "last_failure_time": null,
      "failure_threshold": 5,
      "recovery_timeout": 60
    }
  }
}
```

### Programmatic Status Checking

```python
from src.external_service_client import get_circuit_breaker_status

status = get_circuit_breaker_status("my-service")
if status and status["state"] == "open":
    logger.warning(f"Service is down: {status['failure_count']} failures")
```

## Best Practices

### 1. Service Isolation

Use separate circuit breakers for different services:

```python
# Good: Separate breakers per service
protected_post("https://matching-api.com/match", service_name="matching-api")
protected_post("https://storage-api.com/save", service_name="storage-api")

# Bad: Single breaker for all services
# This would cause all services to be blocked if one fails
```

### 2. Appropriate Thresholds

- **Too low**: Premature circuit opening, unnecessary service degradation
- **Too high**: Slow failure detection, wasted resources
- **Just right**: Based on historical failure patterns and SLAs

### 3. Graceful Degradation

Always provide fallback behavior when circuit is open:

```python
try:
    result = protected_post(url, json=data)
except CircuitBreakerError:
    # Graceful degradation
    return {
        "status": "degraded",
        "message": "Service temporarily unavailable",
        "fallback": True
    }
```

### 4. Logging and Alerting

Monitor circuit breaker state transitions:

```python
breaker = get_circuit_breaker("critical-service")
status = breaker.get_status()

if status["state"] == "open":
    logger.error(f"ALERT: Circuit open for critical-service")
    # Send alert to monitoring system
```

### 5. Testing Recovery

Manually test circuit breaker recovery:

```python
# Simulate service recovery
reset_circuit_breaker("test-service")

# Make test request
response = protected_get(
    "https://test-service.com/health",
    service_name="test-service"
)
```

## Testing

### Unit Tests

```python
from src.circuit_breaker import CircuitBreaker, CircuitBreakerError
import pytest

def test_circuit_opens_after_failures():
    breaker = CircuitBreaker(failure_threshold=3)

    def failing_func():
        raise RuntimeError("Service failed")

    # Cause failures
    for _ in range(3):
        with pytest.raises(RuntimeError):
            breaker.call(failing_func)

    # Circuit should be open
    with pytest.raises(CircuitBreakerError):
        breaker.call(failing_func)
```

### Integration Tests

```python
from src.external_service_client import protected_post

def test_circuit_breaker_with_real_service():
    # Make requests until circuit opens
    for _ in range(10):
        try:
            protected_post(
                "https://failing-service.com/api",
                service_name="test-integration"
            )
        except (CircuitBreakerError, requests.RequestException):
            pass

    # Verify circuit is open
    status = get_circuit_breaker_status("test-integration")
    assert status["state"] == "open"
```

## Troubleshooting

### Circuit Stuck Open

**Symptom**: Circuit remains open even after service recovers

**Solutions**:
1. Check recovery timeout - may be too long
2. Manually reset: `reset_circuit_breaker("service-name")`
3. Verify service is actually healthy
4. Check logs for continuous failures during HALF_OPEN state

### False Positives

**Symptom**: Circuit opens too frequently for healthy service

**Solutions**:
1. Increase `failure_threshold`
2. Review what counts as a failure - may need to filter exception types
3. Check for network issues or timeouts that are too aggressive

### Circuit Not Opening

**Symptom**: Service continues to be called despite failures

**Solutions**:
1. Verify circuit breaker is properly configured
2. Check exception types match `expected_exceptions`
3. Ensure using protected functions, not raw requests
4. Verify threshold is appropriate for failure rate

## Examples

### Example 1: External API Integration

```python
from src.external_service_client import protected_post, CircuitBreakerError

def match_documents(document, candidates):
    """Match documents using external API with circuit breaker protection."""
    try:
        response = protected_post(
            "https://matching-api.example.com/match",
            service_name="document-matching",
            json={
                "document": document,
                "candidates": candidates
            },
            timeout=30,
            failure_threshold=5,
            recovery_timeout=60
        )
        return response.json()

    except CircuitBreakerError:
        logger.warning("Matching service circuit is open, using fallback")
        # Fallback to simple matching logic
        return fallback_match(document, candidates)

    except requests.RequestException as e:
        logger.error(f"Matching service request failed: {e}")
        raise
```

### Example 2: Custom Circuit Breaker for Database

```python
from src.circuit_breaker import circuit_breaker
import psycopg2

@circuit_breaker(
    failure_threshold=3,
    recovery_timeout=120,
    expected_exceptions=(psycopg2.OperationalError,)
)
def query_database(query, params):
    """Execute database query with circuit breaker protection."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor.fetchall()
```

## References

- [Circuit Breaker Pattern - Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Release It! - Michael Nygard](https://pragprog.com/titles/mnee2/release-it-second-edition/)
- [Hystrix Documentation](https://github.com/Netflix/Hystrix/wiki)
