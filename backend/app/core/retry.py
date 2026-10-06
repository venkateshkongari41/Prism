import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.providers.exceptions import (
    ProviderRateLimitError,
    ProviderTemporaryError,
    ProviderTimeoutError,
)

T = TypeVar("T")


RETRYABLE_ERRORS = (
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderTemporaryError,
)


async def execute_with_retry(
    operation: Callable[[], Awaitable[T]],
    max_attempts: int = 3,
    base_delay: float = 0.5,
) -> T:

    for attempt in range(1, max_attempts + 1):

        try:
            return await operation()

        except RETRYABLE_ERRORS:

            if attempt == max_attempts:
                raise

            delay = base_delay * (2 ** (attempt - 1))

            await asyncio.sleep(delay)

    raise RuntimeError("Retry operation failed")