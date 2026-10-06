from typing import Any


def get_usage(
    response: dict[str, Any],
) -> dict[str, Any]:
    """
    Return normalized Prism usage information.
    """

    usage = response.get(
        "prism_usage",
        {},
    )

    return {
        "prompt_tokens": int(
            usage.get(
                "prompt_tokens",
                0,
            )
        ),
        "completion_tokens": int(
            usage.get(
                "completion_tokens",
                0,
            )
        ),
        "total_tokens": int(
            usage.get(
                "total_tokens",
                0,
            )
        ),
        "cost": float(
            usage.get(
                "cost",
                0.0,
            )
        ),
    }


def get_cost(
    response: dict[str, Any],
) -> float:
    """
    Return normalized request cost.
    """

    usage = get_usage(response)

    return max(
        0.0,
        usage["cost"],
    )