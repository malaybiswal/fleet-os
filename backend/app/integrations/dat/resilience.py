from __future__ import annotations

from app.config import settings
from app.integrations.resilience import (
    CircuitBreaker,
    CircuitOpenError,
    RateLimiter,
    ResilientLoadProvider,
    with_retries as _with_retries,
)


def with_retries(operation, *, max_retries=None, sleep=None):
    kwargs = {"max_retries": max_retries or settings.DAT_MAX_RETRIES}
    if sleep is not None:
        kwargs["sleep"] = sleep
    return _with_retries(operation, **kwargs)


class ResilientDatProvider(ResilientLoadProvider):
    def __init__(
        self,
        provider,
        *,
        rate_limiter: RateLimiter | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        super().__init__(
            provider,
            rate_limiter=rate_limiter or RateLimiter(settings.DAT_RATE_LIMIT_PER_MINUTE),
            circuit_breaker=circuit_breaker
            or CircuitBreaker(
                failure_threshold=settings.DAT_CIRCUIT_BREAKER_THRESHOLD,
                cooldown_seconds=settings.DAT_CIRCUIT_BREAKER_COOLDOWN_SECONDS,
                provider_name="DAT",
            ),
            provider_name="DAT",
            max_retries=settings.DAT_MAX_RETRIES,
        )
