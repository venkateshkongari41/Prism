from app.core.rate_limiter import RateLimiter


def test_rate_limit_allows_requests():

    limiter = RateLimiter(
        limit=3,
        window_seconds=60,
    )

    allowed, remaining = limiter.check(
        "application-a"
    )

    assert allowed is True
    assert remaining == 2


def test_rate_limit_decreases_remaining():

    limiter = RateLimiter(
        limit=3,
        window_seconds=60,
    )

    limiter.check("application-a")

    allowed, remaining = limiter.check(
        "application-a"
    )

    assert allowed is True
    assert remaining == 1


def test_rate_limit_blocks_after_limit():

    limiter = RateLimiter(
        limit=2,
        window_seconds=60,
    )

    allowed, _ = limiter.check(
        "application-a"
    )

    assert allowed is True

    allowed, _ = limiter.check(
        "application-a"
    )

    assert allowed is True

    allowed, remaining = limiter.check(
        "application-a"
    )

    assert allowed is False
    assert remaining == 0


def test_rate_limit_is_per_application():

    limiter = RateLimiter(
        limit=1,
        window_seconds=60,
    )

    allowed_a, _ = limiter.check(
        "application-a"
    )

    allowed_b, _ = limiter.check(
        "application-b"
    )

    assert allowed_a is True
    assert allowed_b is True


def test_rate_limit_blocks_only_same_application():

    limiter = RateLimiter(
        limit=1,
        window_seconds=60,
    )

    limiter.check(
        "application-a"
    )

    allowed_a, _ = limiter.check(
        "application-a"
    )

    allowed_b, _ = limiter.check(
        "application-b"
    )

    assert allowed_a is False
    assert allowed_b is True