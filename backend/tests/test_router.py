import pytest

from app.core.router import RoutingEngine
from app.core.routing_config import ROUTES, Route
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderTemporaryError,
)
from app.providers.provider import LLMProvider


class FailingProvider(LLMProvider):

    async def chat(
        self,
        model,
        messages,
        stream=False,
    ):
        raise ProviderTemporaryError(
            "provider unavailable"
        )


class AuthenticationFailingProvider(LLMProvider):

    async def chat(
        self,
        model,
        messages,
        stream=False,
    ):
        raise ProviderAuthenticationError(
            "invalid API key"
        )


class SuccessfulProvider(LLMProvider):

    async def chat(
        self,
        model,
        messages,
        stream=False,
    ):
        return {
            "id": "test-response",
            "model": model,
            "choices": [],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 5,
                "total_tokens": 10,
            },
        }


class StreamFailingProvider(LLMProvider):

    async def chat(
        self,
        model,
        messages,
        stream=False,
    ):
        raise ProviderTemporaryError(
            "provider unavailable"
        )

    async def stream_chat(
        self,
        model,
        messages,
    ):
        raise ProviderTemporaryError(
            "stream failed before first chunk"
        )

        yield


class SuccessfulStreamProvider(LLMProvider):

    async def chat(
        self,
        model,
        messages,
        stream=False,
    ):
        return {
            "id": "test-response",
            "model": model,
            "choices": [],
        }

    async def stream_chat(
        self,
        model,
        messages,
    ):
        yield "data: fallback response\n\n"
        yield "data: [DONE]\n\n"


class PartialStreamFailingProvider(LLMProvider):

    async def chat(
        self,
        model,
        messages,
        stream=False,
    ):
        raise ProviderTemporaryError(
            "provider unavailable"
        )

    async def stream_chat(
        self,
        model,
        messages,
    ):
        yield "data: first chunk\n\n"

        raise ProviderTemporaryError(
            "provider failed after streaming started"
        )


@pytest.mark.asyncio
async def test_fallback_is_used_when_primary_fails():

    from app.providers.registry import provider_registry

    provider_registry.register(
        "test-primary",
        FailingProvider(),
    )

    provider_registry.register(
        "test-fallback",
        SuccessfulProvider(),
    )

    original_route = ROUTES.get("test")

    ROUTES["test"] = Route(
        primary="test-primary",
        fallbacks=("test-fallback",),
    )

    engine = RoutingEngine()

    result = await engine.execute(
        alias="test",
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "Hello",
            }
        ],
    )

    assert result.provider == "test-fallback"
    assert result.fallback_used is True
    assert result.response["id"] == "test-response"

    if original_route is None:
        del ROUTES["test"]
    else:
        ROUTES["test"] = original_route


@pytest.mark.asyncio
async def test_authentication_error_does_not_fallback():

    from app.providers.registry import provider_registry

    provider_registry.register(
        "auth-primary",
        AuthenticationFailingProvider(),
    )

    provider_registry.register(
        "auth-fallback",
        SuccessfulProvider(),
    )

    original_route = ROUTES.get("auth-test")

    ROUTES["auth-test"] = Route(
        primary="auth-primary",
        fallbacks=("auth-fallback",),
    )

    engine = RoutingEngine()

    with pytest.raises(ProviderAuthenticationError):

        await engine.execute(
            alias="auth-test",
            model="test-model",
            messages=[
                {
                    "role": "user",
                    "content": "Hello",
                }
            ],
        )

    if original_route is None:
        del ROUTES["auth-test"]
    else:
        ROUTES["auth-test"] = original_route


@pytest.mark.asyncio
async def test_stream_fallback_before_first_chunk():

    from app.providers.registry import provider_registry

    provider_registry.register(
        "stream-primary",
        StreamFailingProvider(),
    )

    provider_registry.register(
        "stream-fallback",
        SuccessfulStreamProvider(),
    )

    original_route = ROUTES.get("stream-test")

    ROUTES["stream-test"] = Route(
        primary="stream-primary",
        fallbacks=("stream-fallback",),
    )

    engine = RoutingEngine()

    # stream() now returns a StreamResult.
    result = await engine.stream(
        alias="stream-test",
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "Hello",
            }
        ],
    )

    chunks = []

    async for chunk in result.stream:
        chunks.append(chunk)

    assert result.provider == "stream-fallback"
    assert result.fallback_used is True

    assert chunks == [
        "data: fallback response\n\n",
        "data: [DONE]\n\n",
    ]

    if original_route is None:
        del ROUTES["stream-test"]
    else:
        ROUTES["stream-test"] = original_route


@pytest.mark.asyncio
async def test_stream_does_not_fallback_after_first_chunk():

    from app.providers.registry import provider_registry

    provider_registry.register(
        "partial-primary",
        PartialStreamFailingProvider(),
    )

    provider_registry.register(
        "partial-fallback",
        SuccessfulStreamProvider(),
    )

    original_route = ROUTES.get("partial-test")

    ROUTES["partial-test"] = Route(
        primary="partial-primary",
        fallbacks=("partial-fallback",),
    )

    engine = RoutingEngine()

    result = await engine.stream(
        alias="partial-test",
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "Hello",
            }
        ],
    )

    chunks = []

    with pytest.raises(ProviderTemporaryError):

        async for chunk in result.stream:
            chunks.append(chunk)

    assert result.provider == "partial-primary"
    assert result.fallback_used is False

    assert chunks == [
        "data: first chunk\n\n",
    ]

    if original_route is None:
        del ROUTES["partial-test"]
    else:
        ROUTES["partial-test"] = original_route