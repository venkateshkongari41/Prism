"""
Deterministic provider-failover verification.

This script does not call external providers.
It invokes the same RoutingEngine used by Prism
with temporary test providers and prints a compact
verification summary suitable for the final report.
"""

import asyncio
import json

from app.core.router import RoutingEngine
from app.core.routing_config import ROUTES, Route
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
            "simulated primary outage"
        )

    async def stream_chat(
        self,
        model,
        messages,
    ):
        raise ProviderTemporaryError(
            "simulated primary outage"
        )

        if False:
            yield ""


class DemoFallbackProvider(LLMProvider):

    async def chat(
        self,
        model,
        messages,
        stream=False,
    ):
        return {
            "id": "demo-fallback",
            "object": "chat.completion",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "fallback-success",
                    },
                    "finish_reason": "stop",
                }
            ],
        }

    async def stream_chat(
        self,
        model,
        messages,
    ):
        chunk = {
            "id": "demo-fallback-stream",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": "fallback-success",
                    },
                    "finish_reason": None,
                }
            ],
        }

        yield (
            f"data: {json.dumps(chunk)}\n\n"
        )

        yield "data: [DONE]\n\n"


async def main():

    original_providers = dict(
        provider_registry._providers
    )

    original_route = ROUTES.get(
        "verification-failover"
    )

    try:

        provider_registry._providers = {
            "verification-primary": (
                FailingProvider()
            ),
            "verification-fallback": (
                DemoFallbackProvider()
            ),
        }

        ROUTES[
            "verification-failover"
        ] = Route(
            primary="verification-primary",
            fallbacks=(
                "verification-fallback",
            ),
        )

        engine = RoutingEngine()

        async def call_once(operation):
            return await operation()

        import app.core.router as router_module

        original_retry = (
            router_module.execute_with_retry
        )

        router_module.execute_with_retry = (
            call_once
        )

        try:

            result = await engine.execute(
                alias="verification-failover",
                model="test-model",
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "trigger failover"
                        ),
                    }
                ],
            )

        finally:

            router_module.execute_with_retry = (
                original_retry
            )

        print(
            "Prism provider failover verification"
        )

        print(
            "-----------------------------------"
        )

        print(
            f"provider_used      : "
            f"{result.provider}"
        )

        print(
            f"fallback_used      : "
            f"{result.fallback_used}"
        )

        print(
            "response            : "
            + result.response[
                "choices"
            ][0]["message"]["content"]
        )

        print(
            "result              : PASS"
        )

    finally:

        provider_registry._providers = (
            original_providers
        )

        if original_route is None:

            ROUTES.pop(
                "verification-failover",
                None,
            )

        else:

            ROUTES[
                "verification-failover"
            ] = original_route


if __name__ == "__main__":
    asyncio.run(main())