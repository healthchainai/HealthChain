"""Retry helpers for transient network failures in FHIR/OAuth2 clients.

Healthcare endpoints (EHR FHIR servers, OAuth2 token services) frequently
return transient errors under load — connection resets, timeouts, and
``429``/``5xx`` responses. These helpers provide a small, dependency-free
exponential-backoff retry primitive shared by the sync and async clients.
"""

import asyncio
import logging
import time
from typing import Awaitable, Callable, Iterable, Tuple, Type, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

# HTTP status codes that are safe to retry — transient server-side conditions.
RETRYABLE_STATUS_CODES: Tuple[int, ...] = (408, 429, 500, 502, 503, 504)

# Exceptions that indicate a transient transport-level failure.
RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
)


class RetryPolicy:
    """Configuration for exponential-backoff retries.

    Args:
        max_attempts: Total number of attempts (including the first).
        backoff_base: Initial delay in seconds before the first retry.
        backoff_factor: Multiplier applied to the delay after each attempt.
        max_backoff: Upper bound on any single backoff delay, in seconds.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_base: float = 0.5,
        backoff_factor: float = 2.0,
        max_backoff: float = 8.0,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff

    def delay_for(self, attempt: int) -> float:
        """Return the backoff delay (seconds) before the given 1-indexed attempt."""
        raw = self.backoff_base * (self.backoff_factor ** (attempt - 1))
        return min(raw, self.max_backoff)


def _is_retryable_response(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    return isinstance(exc, RETRYABLE_EXCEPTIONS)


def retry_call(
    fn: Callable[[], T],
    policy: RetryPolicy,
    *,
    retryable: Iterable[Type[BaseException]] = None,
) -> T:
    """Invoke ``fn`` with synchronous exponential-backoff retries.

    Re-raises the last exception once attempts are exhausted.
    """
    last_exc: BaseException = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return fn()
        except BaseException as exc:  # noqa: BLE001 - re-raised below
            transient = _is_retryable_response(exc) or (
                retryable is not None and isinstance(exc, tuple(retryable))
            )
            if not transient or attempt == policy.max_attempts:
                raise
            delay = policy.delay_for(attempt)
            logger.warning(
                "Transient failure (attempt %d/%d), retrying in %.2fs: %s",
                attempt,
                policy.max_attempts,
                delay,
                exc,
            )
            last_exc = exc
            time.sleep(delay)
    raise last_exc  # pragma: no cover - loop always returns or raises


async def async_retry_call(
    fn: Callable[[], Awaitable[T]],
    policy: RetryPolicy,
    *,
    retryable: Iterable[Type[BaseException]] = None,
) -> T:
    """Invoke awaitable ``fn`` with asynchronous exponential-backoff retries."""
    last_exc: BaseException = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await fn()
        except BaseException as exc:  # noqa: BLE001 - re-raised below
            transient = _is_retryable_response(exc) or (
                retryable is not None and isinstance(exc, tuple(retryable))
            )
            if not transient or attempt == policy.max_attempts:
                raise
            delay = policy.delay_for(attempt)
            logger.warning(
                "Transient failure (attempt %d/%d), retrying in %.2fs: %s",
                attempt,
                policy.max_attempts,
                delay,
                exc,
            )
            last_exc = exc
            await asyncio.sleep(delay)
    raise last_exc  # pragma: no cover - loop always returns or raises
