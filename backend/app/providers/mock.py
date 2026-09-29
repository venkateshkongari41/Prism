from typing import Any

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