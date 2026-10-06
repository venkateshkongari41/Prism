import httpx
from typing import Any, AsyncIterator

from app.core.config import settings
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderRateLimitError,
    ProviderTemporaryError,
    ProviderTimeoutError,
)
from app.providers.provider import LLMProvider


class OpenRouterProvider(LLMProvider):

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:

        headers = {
            "Authorization": (
                f"Bearer {settings.openrouter_api_key}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        try:
            async with httpx.AsyncClient(
                timeout=60.0
            ) as client:

                response = await client.post(
                    (
                        f"{settings.openrouter_base_url}"
                        "/chat/completions"
                    ),
                    headers=headers,
                    json=payload,
                )

        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "OpenRouter request timed out"
            ) from exc

        except httpx.RequestError as exc:
            raise ProviderTemporaryError(
                f"OpenRouter request failed: {exc}"
            ) from exc

        if response.status_code == 401:
            raise ProviderAuthenticationError(
                "OpenRouter authentication failed"
            )

        if response.status_code == 400:
            raise ProviderBadRequestError(
                "OpenRouter rejected the request"
            )

        if response.status_code == 429:
            raise ProviderRateLimitError(
                "OpenRouter rate limit exceeded"
            )

        if response.status_code >= 500:
            raise ProviderTemporaryError(
                (
                    "OpenRouter server error: "
                    f"{response.status_code}"
                )
            )

        response.raise_for_status()

        result = response.json()

        usage = result.get("usage") or {}

        result["prism_usage"] = {
            "prompt_tokens": usage.get(
                "prompt_tokens",
                0,
            ),
            "completion_tokens": usage.get(
                "completion_tokens",
                0,
            ),
            "total_tokens": usage.get(
                "total_tokens",
                0,
            ),
            "cost": usage.get(
                "cost",
                0,
            ),
        }

        return result

    async def stream_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[str]:

        headers = {
            "Authorization": (
                f"Bearer {settings.openrouter_api_key}"
            ),
            "Content-Type": "application/json",
        }

        # Request final usage metadata from OpenRouter.
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "usage": {
                "include": True,
            },
        }

        timeout = httpx.Timeout(
            connect=10.0,
            read=None,
            write=10.0,
            pool=10.0,
        )

        done_seen = False

        try:
            async with httpx.AsyncClient(
                timeout=timeout
            ) as client:

                async with client.stream(
                    "POST",
                    (
                        f"{settings.openrouter_base_url}"
                        "/chat/completions"
                    ),
                    headers=headers,
                    json=payload,
                ) as response:

                    if response.status_code == 401:
                        raise ProviderAuthenticationError(
                            "OpenRouter authentication failed"
                        )

                    if response.status_code == 400:
                        raise ProviderBadRequestError(
                            "OpenRouter rejected the request"
                        )

                    if response.status_code == 429:
                        raise ProviderRateLimitError(
                            "OpenRouter rate limit exceeded"
                        )

                    if response.status_code >= 500:
                        raise ProviderTemporaryError(
                            (
                                "OpenRouter server error: "
                                f"{response.status_code}"
                            )
                        )

                    response.raise_for_status()

                    async for line in response.aiter_lines():

                        if not line:
                            continue

                        if not line.startswith("data:"):
                            continue

                        payload_text = line[5:].strip()

                        if payload_text == "[DONE]":
                            done_seen = True

                        # Forward each SSE event immediately.
                        yield f"{line}\n\n"

            # Defensively enforce Prism's terminal stream contract.
            if not done_seen:
                yield "data: [DONE]\n\n"

        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "OpenRouter streaming request timed out"
            ) from exc

        except httpx.RequestError as exc:
            raise ProviderTemporaryError(
                (
                    "OpenRouter streaming request failed: "
                    f"{exc}"
                )
            ) from exc