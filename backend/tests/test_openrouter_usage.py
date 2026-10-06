from app.providers.openrouter import OpenRouterProvider


def test_openrouter_usage_normalization():
    provider = OpenRouterProvider()

    result = {
        "id": "test-response",
        "usage": {
            "prompt_tokens": 18,
            "completion_tokens": 420,
            "total_tokens": 438,
            "cost": 0,
        },
    }

    usage = result.get("usage")

    normalized = {
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

    assert normalized["prompt_tokens"] == 18
    assert normalized["completion_tokens"] == 420
    assert normalized["total_tokens"] == 438
    assert normalized["cost"] == 0
