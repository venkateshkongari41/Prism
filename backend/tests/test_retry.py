import pytest

from app.core.retry import execute_with_retry
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderBadRequestError,
    ProviderRateLimitError,
    ProviderTemporaryError,
    ProviderTimeoutError,
)


@pytest.mark.asyncio
async def test_success_without_retry():

    calls = 0

    async def operation():
        nonlocal calls
        calls += 1

        return "success"

    result = await execute_with_retry(operation)

    assert result == "success"
    assert calls == 1
    

@pytest.mark.asyncio
async def test_timeout_is_retried():

    calls = 0

    async def operation():
        nonlocal calls
        calls += 1

        if calls < 3:
            raise ProviderTimeoutError("timeout")

        return "success"

    result = await execute_with_retry(
        operation,
        base_delay=0,
    )

    assert result == "success"
    assert calls == 3
    
    
@pytest.mark.asyncio
async def test_rate_limit_is_retried():

    calls = 0

    async def operation():
        nonlocal calls
        calls += 1

        if calls == 1:
            raise ProviderRateLimitError("rate limited")

        return "success"

    result = await execute_with_retry(
        operation,
        base_delay=0,
    )

    assert result == "success"
    assert calls == 2
    
    
@pytest.mark.asyncio
async def test_temporary_error_is_retried():

    calls = 0

    async def operation():
        nonlocal calls
        calls += 1

        if calls < 3:
            raise ProviderTemporaryError("server error")

        return "success"

    result = await execute_with_retry(
        operation,
        base_delay=0,
    )

    assert result == "success"
    assert calls == 3
    
    
@pytest.mark.asyncio
async def test_authentication_error_is_not_retried():

    calls = 0

    async def operation():
        nonlocal calls
        calls += 1

        raise ProviderAuthenticationError(
            "invalid API key"
        )

    with pytest.raises(ProviderAuthenticationError):
        await execute_with_retry(
            operation,
            base_delay=0,
        )

    assert calls == 1
    
    
@pytest.mark.asyncio
async def test_bad_request_is_not_retried():

    calls = 0

    async def operation():
        nonlocal calls
        calls += 1

        raise ProviderBadRequestError(
            "invalid request"
        )

    with pytest.raises(ProviderBadRequestError):
        await execute_with_retry(
            operation,
            base_delay=0,
        )

    assert calls == 1
    
    
@pytest.mark.asyncio
async def test_retry_stops_after_max_attempts():

    calls = 0

    async def operation():
        nonlocal calls
        calls += 1

        raise ProviderTemporaryError(
            "provider unavailable"
        )

    with pytest.raises(ProviderTemporaryError):
        await execute_with_retry(
            operation,
            max_attempts=3,
            base_delay=0,
        )

    assert calls == 3