import asyncio
import json
from typing import Any, AsyncIterator

from app.providers.provider import LLMProvider


class MockProvider(LLMProvider):

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:

        last_message = messages[-1]["content"]

        return {
            "id": "mock-completion-001",
            "object": "chat.completion",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Mock response for: {last_message}",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "total_tokens": 20,
            },
        }

    async def stream_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[str]:

        last_message = messages[-1]["content"]

        words = f"Mock response for: {last_message}".split(" ")

        for index, word in enumerate(words):

            chunk = {
                "id": "mock-stream-001",
                "object": "chat.completion.chunk",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": word if index == 0 else f" {word}"
                        },
                        "finish_reason": None,
                    }
                ],
            }

            yield f"data: {json.dumps(chunk)}\n\n"

            await asyncio.sleep(0.1)

        yield "data: [DONE]\n\n"