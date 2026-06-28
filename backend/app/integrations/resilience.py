from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar


T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    pass


@dataclass
class RateLimiter:
    calls_per_minute: int
    monotonic: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    _last_call_at: float | None = None

    def wait(self) -> None:
        if self.calls_per_minute <= 0:
            return
        min_interval = 60 / self.calls_per_minute
        now = self.monotonic()
        if self._last_call_at is not None:
            elapsed = now - self._last_call_at
            if elapsed < min_interval:
                self.sleep(min_interval - elapsed)
        self._last_call_at = self.monotonic()


@dataclass
class CircuitBreaker:
    failure_threshold: int
    cooldown_seconds: int
    provider_name: str = "provider"
    monotonic: Callable[[], float] = time.monotonic
    failure_count: int = 0
    opened_at: float | None = None

    def before_call(self) -> None:
        if self.opened_at is None:
            return

        if self.monotonic() - self.opened_at < self.cooldown_seconds:
            raise CircuitOpenError(f"{self.provider_name} circuit breaker is open")

        self.opened_at = None
        self.failure_count = 0

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = self.monotonic()

    @property
    def state(self) -> str:
        return "open" if self.opened_at is not None else "closed"


def with_retries(
    operation: Callable[[], T],
    *,
    max_retries: int,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    last_error: Exception | None = None
    for attempt in range(max(1, max_retries)):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt >= max_retries - 1:
                break
            sleep(0.25 * (2**attempt))
    if last_error is None:
        raise RuntimeError("retry operation failed without an exception")
    raise last_error


class ResilientLoadProvider:
    def __init__(
        self,
        provider,
        *,
        rate_limiter: RateLimiter,
        circuit_breaker: CircuitBreaker,
        provider_name: str,
        max_retries: int,
    ):
        self.provider = provider
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker
        self.provider_name = provider_name
        self.max_retries = max_retries

    def authenticate(self) -> None:
        return self._call(self.provider.authenticate)

    def search_loads(self, filters=None):
        return self._call(lambda: self.provider.search_loads(filters))

    def close(self) -> None:
        self.provider.close()

    def health(self) -> dict[str, int | str]:
        return {
            "provider": self.provider_name,
            "circuit_state": self.circuit_breaker.state,
            "consecutive_failures": self.circuit_breaker.failure_count,
        }

    def _call(self, operation):
        self.circuit_breaker.before_call()
        self.rate_limiter.wait()
        try:
            result = with_retries(operation, max_retries=self.max_retries)
        except Exception:
            self.circuit_breaker.record_failure()
            raise
        self.circuit_breaker.record_success()
        return result
