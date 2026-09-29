from typing import Any

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


class OpenRouterProvider(LLMProvider):

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:

        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
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
                    f"{settings.openrouter_base_url}/chat/completions",
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
                f"OpenRouter server error: {response.status_code}"
            )

        response.raise_for_status()

        return response.json()