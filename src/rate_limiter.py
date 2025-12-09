import logging
import os
from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rate_limiter")


def get_client_identifier(request: Request) -> str:
    """
    Extract client identifier for rate limiting.
    First tries x-om-trace-id header, falls back to remote address.
    """
    trace_id = request.headers.get("x-om-trace-id")
    if trace_id:
        return trace_id
    return get_remote_address(request)


# Configuration from environment variables
RATE_LIMIT_REQUESTS = os.environ.get("RATE_LIMIT_REQUESTS", "100")
RATE_LIMIT_PERIOD = os.environ.get("RATE_LIMIT_PERIOD", "minute")
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"

# Construct rate limit string (e.g., "100/minute")
RATE_LIMIT_STRING = f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_PERIOD}"

logger.info(
    f"Rate limiting {'enabled' if RATE_LIMIT_ENABLED else 'disabled'}: {RATE_LIMIT_STRING}"
)

# Create limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[RATE_LIMIT_STRING] if RATE_LIMIT_ENABLED else [],
    enabled=RATE_LIMIT_ENABLED,
)


def get_limiter() -> Limiter:
    """Get the configured limiter instance."""
    return limiter


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    Returns 429 Too Many Requests with Retry-After header.
    """
    retry_after = (
        exc.detail.split("Retry after ")[1].split(" second")[0]
        if "Retry after" in exc.detail
        else "60"
    )

    logger.warning(
        f"Rate limit exceeded for client: {get_client_identifier(request)}. "
        f"Retry after {retry_after} seconds"
    )

    response = Response(
        content=f"Rate limit exceeded. Retry after {retry_after} seconds",
        status_code=429,
        headers={"Retry-After": str(retry_after)},
    )
    return response
