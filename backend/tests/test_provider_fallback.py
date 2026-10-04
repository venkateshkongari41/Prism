import pytest

from app.core.router import RoutingEngine
from app.providers.exceptions import (
    ProviderTemporaryError,
)
from app.providers.provider import LLMProvider
from app.providers.registry import provider_registry


class FailingProvider(LLMProvider):

    async def chat(
        self,
        model,
        messages,
        stream=False,
    ):
        raise ProviderTemporaryError(
            "Simulated provider failure"
        )

    async def stream_chat(
        self,
        model,
        messages,
    ):
        raise ProviderTemporaryError(
            "Simulated provider failure"
        )
        yield


class SuccessfulProvider(LLMProvider):

    async def chat(
        self,
        model,
        messages,
        stream=False,
    ):
        return {
            "id": "test-response",
            "object": "chat.completion",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "fallback success",
                    }
                }
            ],
        }

    async def stream_chat(
        self,
        model,
        messages,
    ):
        yield "data: fallback success\n\n"


@pytest.mark.asyncio
async def test_provider_fallback():

    original_first = provider_registry._providers.get(
        "openrouter"
    )
    original_second = provider_registry._providers.get(
        "huggingface"
    )

    try:

        provider_registry.register(
            "openrouter",
            FailingProvider(),
        )

        provider_registry.register(
            "huggingface",
            SuccessfulProvider(),
        )

        engine = RoutingEngine()

        result = await engine.execute(
            alias="fast",
            model="test-model",
            messages=[
                {
                    "role": "user",
                    "content": "hello",
                }
            ],
        )

        assert result.provider == "huggingface"
        assert result.fallback_used is True

    finally:

        provider_registry.register(
            "openrouter",
            original_first,
        )

        provider_registry.register(
            "huggingface",
            original_second,
        )


@pytest.mark.asyncio
async def test_provider_fallback_to_mock():

    original_first = provider_registry._providers.get(
        "openrouter"
    )
    original_second = provider_registry._providers.get(
        "huggingface"
    )

    try:

        provider_registry.register(
            "openrouter",
            FailingProvider(),
        )

        provider_registry.register(
            "huggingface",
            FailingProvider(),
        )

        engine = RoutingEngine()

        result = await engine.execute(
            alias="fast",
            model="test-model",
            messages=[
                {
                    "role": "user",
                    "content": "hello",
                }
            ],
        )

        assert result.provider == "mock"
        assert result.fallback_used is True

    finally:

        provider_registry.register(
            "openrouter",
            original_first,
        )

        provider_registry.register(
            "huggingface",
            original_second,
        )