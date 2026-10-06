import asyncio
import json

import pytest

from app.core.router import (
    NON_FALLBACK_ERRORS,
    RETRYABLE_ERRORS,
    RoutingEngine,
)
from app.core.routing_config import ROUTES, Route
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderTemporaryError,
)
from app.providers.provider import LLMProvider
from app.providers.registry import provider_registry


class SuccessfulProvider(LLMProvider):
    def __init__(self, name: str):
        self.name = name
        self.calls = 0

    async def chat(
        self,
        model: str,
        messages: list[dict],
        stream: bool = False,
    ):
        self.calls += 1

        return {
            "id": f"{self.name}-completion",
            "object": "chat.completion",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"response from {self.name}",
                    },
                    "finish_reason": "stop",
                }
            ],
        }

    async def stream_chat(
        self,
        model: str,
        messages: list[dict],
    ):
        self.calls += 1

        chunk = {
            "id": f"{self.name}-stream",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": f"response from {self.name}",
                    },
                    "finish_reason": None,
                }
            ],
        }

        yield (
            f"data: {json.dumps(chunk)}\n\n"
        )

        yield "data: [DONE]\n\n"


class TemporaryFailureProvider(LLMProvider):
    def __init__(self):
        self.calls = 0

    async def chat(
        self,
        model: str,
        messages: list[dict],
        stream: bool = False,
    ):
        self.calls += 1

        raise ProviderTemporaryError(
            "simulated temporary failure"
        )

    async def stream_chat(
        self,
        model: str,
        messages: list[dict],
    ):
        self.calls += 1

        if False:
            yield ""

        raise ProviderTemporaryError(
            "simulated stream failure"
        )


class AuthenticationFailureProvider(LLMProvider):
    async def chat(
        self,
        model: str,
        messages: list[dict],
        stream: bool = False,
    ):
        raise ProviderAuthenticationError(
            "simulated authentication failure"
        )

    async def stream_chat(
        self,
        model: str,
        messages: list[dict],
    ):
        raise ProviderAuthenticationError(
            "simulated authentication failure"
        )

        if False:
            yield ""


@pytest.mark.asyncio
async def test_non_streaming_provider_failover(monkeypatch):
    primary = TemporaryFailureProvider()
    fallback = SuccessfulProvider("fallback")

    monkeypatch.setitem(
        ROUTES,
        "test-failover",
        Route(
            primary="primary-test",
            fallbacks=("fallback-test",),
        ),
    )

    monkeypatch.setattr(
        provider_registry,
        "_providers",
        {
            "primary-test": primary,
            "fallback-test": fallback,
        },
    )

    # Disable retry backoff for this deterministic unit test.
    async def call_once(operation):
        return await operation()

    monkeypatch.setattr(
        "app.core.router.execute_with_retry",
        call_once,
    )

    result = await RoutingEngine().execute(
        alias="test-failover",
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "hello",
            }
        ],
    )

    assert result.provider == "fallback-test"
    assert result.fallback_used is True

    assert (
        result.response["choices"][0]["message"]["content"]
        == "response from fallback"
    )

    assert primary.calls == 1
    assert fallback.calls == 1


@pytest.mark.asyncio
async def test_authentication_error_does_not_failover(
    monkeypatch,
):
    primary = AuthenticationFailureProvider()
    fallback = SuccessfulProvider("fallback")

    monkeypatch.setitem(
        ROUTES,
        "test-auth",
        Route(
            primary="primary-auth",
            fallbacks=("fallback-auth",),
        ),
    )

    monkeypatch.setattr(
        provider_registry,
        "_providers",
        {
            "primary-auth": primary,
            "fallback-auth": fallback,
        },
    )

    async def call_once(operation):
        return await operation()

    monkeypatch.setattr(
        "app.core.router.execute_with_retry",
        call_once,
    )

    with pytest.raises(
        ProviderAuthenticationError
    ):
        await RoutingEngine().execute(
            alias="test-auth",
            model="test-model",
            messages=[
                {
                    "role": "user",
                    "content": "hello",
                }
            ],
        )

    assert fallback.calls == 0


@pytest.mark.asyncio
async def test_streaming_failover_before_first_chunk(
    monkeypatch,
):
    primary = TemporaryFailureProvider()
    fallback = SuccessfulProvider(
        "stream-fallback"
    )

    monkeypatch.setitem(
        ROUTES,
        "test-stream-failover",
        Route(
            primary="stream-primary",
            fallbacks=("stream-fallback",),
        ),
    )

    monkeypatch.setattr(
        provider_registry,
        "_providers",
        {
            "stream-primary": primary,
            "stream-fallback": fallback,
        },
    )

    result = await RoutingEngine().stream(
        alias="test-stream-failover",
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "hello",
            }
        ],
    )

    chunks = [
        chunk
        async for chunk in result.stream
    ]

    assert result.provider == "stream-fallback"
    assert result.fallback_used is True

    assert chunks[-1] == (
        "data: [DONE]\n\n"
    )

    assert "stream-fallback" in chunks[0]


@pytest.mark.asyncio
async def test_streaming_does_not_failover_after_first_chunk(
    monkeypatch,
):
    class PartialFailureProvider(LLMProvider):
        async def chat(
            self,
            model: str,
            messages: list[dict],
            stream: bool = False,
        ):
            raise ProviderTemporaryError(
                "not used"
            )

        async def stream_chat(
            self,
            model: str,
            messages: list[dict],
        ):
            yield "data: first-chunk\n\n"

            raise ProviderTemporaryError(
                "stream failed after first chunk"
            )

    primary = PartialFailureProvider()
    fallback = SuccessfulProvider(
        "should-not-run"
    )

    monkeypatch.setitem(
        ROUTES,
        "test-stream-partial",
        Route(
            primary="partial-primary",
            fallbacks=("partial-fallback",),
        ),
    )

    monkeypatch.setattr(
        provider_registry,
        "_providers",
        {
            "partial-primary": primary,
            "partial-fallback": fallback,
        },
    )

    result = await RoutingEngine().stream(
        alias="test-stream-partial",
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "hello",
            }
        ],
    )

    iterator = result.stream.__aiter__()

    first_chunk = await iterator.__anext__()

    assert first_chunk == (
        "data: first-chunk\n\n"
    )

    with pytest.raises(
        ProviderTemporaryError
    ):
        await iterator.__anext__()

    assert result.provider == (
        "partial-primary"
    )

    assert result.fallback_used is False

    assert fallback.calls == 0


def test_retryable_error_categories_are_configured():
    assert (
        ProviderTemporaryError
        in RETRYABLE_ERRORS
    )

    assert (
        ProviderAuthenticationError
        in NON_FALLBACK_ERRORS
    )