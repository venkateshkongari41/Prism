from app.core.cost import get_cost, get_usage


def test_get_usage():

    response = {
        "prism_usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "cost": 0.0025,
        }
    }

    usage = get_usage(response)

    assert usage["prompt_tokens"] == 100
    assert usage["completion_tokens"] == 50
    assert usage["total_tokens"] == 150
    assert usage["cost"] == 0.0025


def test_get_cost():

    response = {
        "prism_usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "cost": 0.0025,
        }
    }

    assert get_cost(response) == 0.0025


def test_missing_usage_defaults_to_zero():

    response = {}

    usage = get_usage(response)

    assert usage["prompt_tokens"] == 0
    assert usage["completion_tokens"] == 0
    assert usage["total_tokens"] == 0
    assert usage["cost"] == 0.0

    assert get_cost(response) == 0.0


def test_negative_cost_is_clamped():

    response = {
        "prism_usage": {
            "cost": -1,
        }
    }

    assert get_cost(response) == 0.0