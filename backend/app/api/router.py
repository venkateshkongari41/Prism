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


@dataclass
class StreamResult:
    stream: AsyncIterator[str]
    provider: str
    fallback_used: bool


RETRYABLE_ERRORS = (
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderTemporaryError,
)

NON_FALLBACK_ERRORS = (
    ProviderAuthenticationError,
    ProviderBadRequestError,
)


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

            provider = provider_registry.get(provider_name)

            try:
                response = await execute_with_retry(
                    lambda: provider.chat(
                        model=model,
                        messages=messages,
                        stream=stream,
                    )
                )

                return RoutingResult(
                    response=response,
                    provider=provider_name,
                    fallback_used=index > 0,
                )

            except NON_FALLBACK_ERRORS:
                raise

            except RETRYABLE_ERRORS:
                if index == len(providers) - 1:
                    raise

                continue

        raise RuntimeError("No provider available")

    async def _stream_provider(
        self,
        provider_name: str,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[str]:

        provider = provider_registry.get(provider_name)

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

        for index, provider_name in enumerate(providers):

            provider = provider_registry.get(provider_name)

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
                # We need to get the first chunk before returning
                # StreamResult so that the API knows which provider
                # is actually serving the request.
                stream_iterator = generate()

                try:
                    first_chunk = await stream_iterator.__anext__()
                except StopAsyncIteration:
                    return StreamResult(
                        stream=self._empty_stream(),
                        provider=provider_name,
                        fallback_used=index > 0,
                    )

                async def combined_stream():
                    yield first_chunk

                    async for chunk in stream_iterator:
                        yield chunk

                return StreamResult(
                    stream=combined_stream(),
                    provider=provider_name,
                    fallback_used=index > 0,
                )

            except NON_FALLBACK_ERRORS:
                raise

            except RETRYABLE_ERRORS:

                # No chunk reached the client because we haven't
                # returned StreamResult yet.
                if stream_started:
                    raise

                if index == len(providers) - 1:
                    raise

                continue

        raise RuntimeError("No provider available")

    async def _empty_stream(self):
        return
        yield


routing_engine = RoutingEngine()