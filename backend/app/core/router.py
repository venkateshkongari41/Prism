import json
from dataclasses import dataclass
from typing import Any, AsyncIterator

from app.core.retry import execute_with_retry
from app.core.routing_config import ROUTES
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderRateLimitError,
    ProviderTemporaryError,
    ProviderTimeoutError,
)
from app.providers.registry import provider_registry


@dataclass
class RoutingResult:
    response: dict[str, Any]
    provider: str
    fallback_used: bool
    usage: dict[str, Any] | None = None
    model: str | None = None


@dataclass
class StreamResult:
    stream: AsyncIterator[str]
    provider: str
    fallback_used: bool
    model: str | None = None


RETRYABLE_ERRORS = (
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderTemporaryError,
)

NON_FALLBACK_ERRORS = (
    ProviderAuthenticationError,
    ProviderBadRequestError,
)


def _reported_provider(
    response: dict[str, Any],
    fallback: str,
) -> str:
    provider = response.get("provider")
    if isinstance(provider, str) and provider.strip():
        return provider
    return fallback


def _reported_model(
    response: dict[str, Any],
    fallback: str,
) -> str:
    model = response.get("model")
    if isinstance(model, str) and model.strip():
        return model
    return fallback


def _reported_stream_metadata(
    chunk: str,
    fallback_provider: str,
    fallback_model: str,
) -> tuple[str, str]:
    for line in chunk.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue

        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue

        try:
            event = json.loads(payload)
        except (TypeError, ValueError):
            continue

        if isinstance(event, dict):
            return (
                _reported_provider(event, fallback_provider),
                _reported_model(event, fallback_model),
            )

    return fallback_provider, fallback_model


class RoutingEngine:

    async def execute(
        self,
        alias: str,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
    ) -> RoutingResult:

        route = ROUTES[alias]

        providers = [
            route.primary,
            *route.fallbacks,
        ]

        for index, provider_name in enumerate(providers):

            provider = provider_registry.get(
                provider_name
            )

            try:
                response = await execute_with_retry(
                    lambda: provider.chat(
                        model=model,
                        messages=messages,
                        stream=stream,
                    )
                )

                usage = response.get(
                    "prism_usage"
                )

                return RoutingResult(
                    response=response,
                    provider=_reported_provider(
                        response,
                        provider_name,
                    ),
                    fallback_used=index > 0,
                    usage=usage,
                    model=_reported_model(
                        response,
                        model,
                    ),
                )

            except NON_FALLBACK_ERRORS:
                raise

            except RETRYABLE_ERRORS:

                if index == len(providers) - 1:
                    raise

                continue

        raise RuntimeError(
            "No provider available"
        )

    async def _stream_provider(
        self,
        provider_name: str,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[str]:

        provider = provider_registry.get(
            provider_name
        )

        async for chunk in provider.stream_chat(
            model=model,
            messages=messages,
        ):
            yield chunk

    async def stream(
        self,
        alias: str,
        model: str,
        messages: list[dict[str, Any]],
    ) -> StreamResult:

        route = ROUTES[alias]

        providers = [
            route.primary,
            *route.fallbacks,
        ]

        for index, provider_name in enumerate(
            providers
        ):

            provider = provider_registry.get(
                provider_name
            )

            stream_started = False

            async def generate():
                nonlocal stream_started

                try:
                    async for chunk in provider.stream_chat(
                        model=model,
                        messages=messages,
                    ):
                        stream_started = True
                        yield chunk

                except NON_FALLBACK_ERRORS:
                    raise

                except RETRYABLE_ERRORS:
                    raise

            try:
                stream_iterator = generate()

                try:
                    first_chunk = (
                        await stream_iterator.__anext__()
                    )

                except StopAsyncIteration:

                    return StreamResult(
                        stream=self._empty_stream(),
                        provider=provider_name,
                        fallback_used=index > 0,
                        model=model,
                    )

                async def combined_stream():
                    yield first_chunk

                    async for chunk in stream_iterator:
                        yield chunk

                reported_provider, reported_model = (
                    _reported_stream_metadata(
                        first_chunk,
                        provider_name,
                        model,
                    )
                )

                return StreamResult(
                    stream=combined_stream(),
                    provider=reported_provider,
                    fallback_used=index > 0,
                    model=reported_model,
                )

            except NON_FALLBACK_ERRORS:
                raise

            except RETRYABLE_ERRORS:

                if stream_started:
                    raise

                if index == len(providers) - 1:
                    raise

                continue

        raise RuntimeError(
            "No provider available"
        )

    async def _empty_stream(self):
        return
        yield


routing_engine = RoutingEngine()