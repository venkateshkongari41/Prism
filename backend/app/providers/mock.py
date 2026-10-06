import asyncio
import json
from typing import Any, AsyncIterator

from app.providers.provider import LLMProvider


MOCK_PROMPT_TOKENS = 10
MOCK_COMPLETION_TOKENS = 10
MOCK_TOTAL_TOKENS = 20
MOCK_COST = 0.001


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
                        "content": (
                            f"Mock response for: {last_message}"
                        ),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": MOCK_PROMPT_TOKENS,
                "completion_tokens": MOCK_COMPLETION_TOKENS,
                "total_tokens": MOCK_TOTAL_TOKENS,
            },
            "prism_usage": {
                "prompt_tokens": MOCK_PROMPT_TOKENS,
                "completion_tokens": MOCK_COMPLETION_TOKENS,
                "total_tokens": MOCK_TOTAL_TOKENS,
                "cost": MOCK_COST,
            },
        }

    async def stream_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[str]:

        last_message = messages[-1]["content"]

        words = (
            f"Mock response for: {last_message}"
        ).split(" ")

        # ---------------------------------------------------------
        # Normal content chunks
        # ---------------------------------------------------------

        for index, word in enumerate(words):

            chunk = {
                "id": "mock-stream-001",
                "object": "chat.completion.chunk",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": (
                                word
                                if index == 0
                                else f" {word}"
                            ),
                        },
                        "finish_reason": None,
                    }
                ],
            }

            yield (
                f"data: {json.dumps(chunk)}\n\n"
            )

            await asyncio.sleep(0.05)

        # ---------------------------------------------------------
        # Final usage chunk
        #
        # Keep choices[0].delta.content present because existing
        # streaming tests expect every pre-DONE chunk to have a
        # standard OpenAI-style choices array.
        #
        # The content is empty so it does not change the generated
        # response.
        # ---------------------------------------------------------

        usage_chunk = {
            "id": "mock-stream-001",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": "",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": MOCK_PROMPT_TOKENS,
                "completion_tokens": MOCK_COMPLETION_TOKENS,
                "total_tokens": MOCK_TOTAL_TOKENS,
            },
            "prism_usage": {
                "prompt_tokens": MOCK_PROMPT_TOKENS,
                "completion_tokens": MOCK_COMPLETION_TOKENS,
                "total_tokens": MOCK_TOTAL_TOKENS,
                "cost": MOCK_COST,
            },
        }

        yield (
            f"data: {json.dumps(usage_chunk)}\n\n"
        )

        # ---------------------------------------------------------
        # Stream termination
        # ---------------------------------------------------------

        yield "data: [DONE]\n\n"