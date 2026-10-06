import asyncio
import json

from app.api.chat import _extract_stream_usage
from app.providers.mock import (
    MOCK_COMPLETION_TOKENS,
    MOCK_COST,
    MOCK_PROMPT_TOKENS,
    MOCK_TOTAL_TOKENS,
    MockProvider,
)


def test_extract_stream_usage_standard_event():
    chunk = (
        "data: "
        + json.dumps(
            {
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 7,
                    "total_tokens": 18,
                    "cost": 0.0025,
                }
            }
        )
        + "\n\n"
    )

    assert _extract_stream_usage(chunk) == {
        "prompt_tokens": 11,
        "completion_tokens": 7,
        "total_tokens": 18,
        "cost": 0.0025,
    }


def test_extract_stream_usage_prism_event():
    chunk = (
        "data: "
        + json.dumps(
            {
                "prism_usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "total_tokens": 20,
                    "cost": 0.001,
                }
            }
        )
        + "\n\n"
    )

    assert _extract_stream_usage(chunk) == {
        "prompt_tokens": 10,
        "completion_tokens": 10,
        "total_tokens": 20,
        "cost": 0.001,
    }


def test_extract_stream_usage_done_is_none():
    assert _extract_stream_usage(
        "data: [DONE]\n\n"
    ) is None


def test_mock_stream_emits_usage_before_done():

    async def collect():
        provider = MockProvider()

        return [
            chunk
            async for chunk in provider.stream_chat(
                model="mock-smart",
                messages=[
                    {
                        "role": "user",
                        "content": "Hello",
                    }
                ],
            )
        ]

    chunks = asyncio.run(collect())

    assert chunks[-1] == "data: [DONE]\n\n"

    usage = _extract_stream_usage(
        chunks[-2]
    )

    assert usage == {
        "prompt_tokens": MOCK_PROMPT_TOKENS,
        "completion_tokens": MOCK_COMPLETION_TOKENS,
        "total_tokens": MOCK_TOTAL_TOKENS,
        "cost": MOCK_COST,
    }


def test_mock_nonstream_has_prism_usage():

    async def run():
        return await MockProvider().chat(
            model="mock-smart",
            messages=[
                {
                    "role": "user",
                    "content": "Hello",
                }
            ],
        )

    response = asyncio.run(run())

    assert response["prism_usage"] == {
        "prompt_tokens": MOCK_PROMPT_TOKENS,
        "completion_tokens": MOCK_COMPLETION_TOKENS,
        "total_tokens": MOCK_TOTAL_TOKENS,
        "cost": MOCK_COST,
    }