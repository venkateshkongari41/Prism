from typing import Any, AsyncIterator

import httpx

from app.core.config import settings
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderRateLimitError,
    ProviderTemporaryError,
    ProviderTimeoutError,
)
from app.providers.provider import LLMProvider


class HuggingFaceProvider(LLMProvider):

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:

        if not settings.huggingface_api_key:
            raise ProviderAuthenticationError(
                "Hugging Face API key is not configured"
            )

        headers = {
            "Authorization": (
                f"Bearer "
                f"{settings.huggingface_api_key}"
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
                        f"{settings.huggingface_base_url}"
                        "/chat/completions"
                    ),
                    headers=headers,
                    json=payload,
                )

        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "Hugging Face request timed out"
            ) from exc

        except httpx.RequestError as exc:
            raise ProviderTemporaryError(
                f"Hugging Face request failed: {exc}"
            ) from exc

        if response.status_code in (401, 403):
            raise ProviderAuthenticationError(
                "Hugging Face authentication failed"
            )

        if response.status_code == 400:
            raise ProviderBadRequestError(
                "Hugging Face rejected the request"
            )

        if response.status_code == 429:
            raise ProviderRateLimitError(
                "Hugging Face rate limit exceeded"
            )

        if response.status_code >= 500:
            raise ProviderTemporaryError(
                (
                    "Hugging Face server error: "
                    f"{response.status_code}"
                )
            )

        response.raise_for_status()

        result = response.json()

        usage = result.get("usage")

        if usage:
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
        else:
            result["prism_usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0,
            }

        return result

    async def stream_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[str]:

        if not settings.huggingface_api_key:
            raise ProviderAuthenticationError(
                "Hugging Face API key is not configured"
            )

        headers = {
            "Authorization": (
                f"Bearer "
                f"{settings.huggingface_api_key}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        timeout = httpx.Timeout(
            connect=10.0,
            read=None,
            write=10.0,
            pool=10.0,
        )

        try:
            async with httpx.AsyncClient(
                timeout=timeout
            ) as client:

                async with client.stream(
                    "POST",
                    (
                        f"{settings.huggingface_base_url}"
                        "/chat/completions"
                    ),
                    headers=headers,
                    json=payload,
                ) as response:

                    if response.status_code in (
                        401,
                        403,
                    ):
                        raise ProviderAuthenticationError(
                            "Hugging Face authentication failed"
                        )

                    if response.status_code == 400:
                        raise ProviderBadRequestError(
                            "Hugging Face rejected the request"
                        )

                    if response.status_code == 429:
                        raise ProviderRateLimitError(
                            "Hugging Face rate limit exceeded"
                        )

                    if response.status_code >= 500:
                        raise ProviderTemporaryError(
                            (
                                "Hugging Face server error: "
                                f"{response.status_code}"
                            )
                        )

                    response.raise_for_status()

                    async for line in (
                        response.aiter_lines()
                    ):
                        if not line:
                            continue

                        if line.startswith("data:"):
                            yield f"{line}\n\n"

        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "Hugging Face streaming request timed out"
            ) from exc

        except httpx.RequestError as exc:
            raise ProviderTemporaryError(
                (
                    "Hugging Face streaming "
                    f"request failed: {exc}"
                )
            ) from exc