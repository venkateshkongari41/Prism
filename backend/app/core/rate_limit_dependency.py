from fastapi import HTTPException

from app.core.rate_limiter import rate_limiter


async def check_rate_limit(
    identity: dict,
) -> int:

    application_name = identity[
        "application_name"
    ]

    limit = identity[
        "rate_limit"
    ]

    window_seconds = identity[
        "rate_window_seconds"
    ]

    allowed, remaining = (
        rate_limiter.check(
            key=application_name,
            limit=limit,
            window_seconds=window_seconds,
        )
    )

    if not allowed:

        raise HTTPException(
            status_code=429,
            detail=(
                "Rate limit exceeded. "
                "Please try again later."
            ),
            headers={
                "Retry-After": str(
                    window_seconds
                )
            },
        )

    return remaining