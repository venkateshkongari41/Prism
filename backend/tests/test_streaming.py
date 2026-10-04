import json
import pytest

from app.providers.mock import MockProvider


@pytest.mark.asyncio
async def test_mock_provider_streaming():

    provider = MockProvider()

    chunks = []

    async for chunk in provider.stream_chat(
        model="mock-fast",
        messages=[
            {
                "role": "user",
                "content": "Hello Prism",
            }
        ],
    ):
        chunks.append(chunk)

    assert len(chunks) > 1
    assert chunks[-1] == "data: [DONE]\n\n"

    content = ""

    for chunk in chunks[:-1]:
        assert chunk.startswith("data: ")
        assert chunk.endswith("\n\n")

        payload = json.loads(
            chunk.removeprefix("data: ").strip()
        )

        assert payload["object"] == "chat.completion.chunk"

        content += payload["choices"][0]["delta"]["content"]

    assert content == "Mock response for: Hello Prism"