import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class RateLimitState:
    window_start: float
    request_count: int


class RateLimiter:

    def __init__(
        self,
        limit: int = 10,
        window_seconds: int = 60,
    ):
        self.limit = limit
        self.window_seconds = window_seconds

        self._states: dict[
            str,
            RateLimitState,
        ] = {}

        self._lock = Lock()

    def check(
        self,
        key: str,
        limit: int | None = None,
        window_seconds: int | None = None,
    ) -> tuple[bool, int]:

        effective_limit = (
            limit
            if limit is not None
            else self.limit
        )

        effective_window = (
            window_seconds
            if window_seconds is not None
            else self.window_seconds
        )

        now = time.monotonic()

        with self._lock:

            state = self._states.get(key)

            if state is None:
                self._states[key] = RateLimitState(
                    window_start=now,
                    request_count=1,
                )

                return (
                    True,
                    effective_limit - 1,
                )

            elapsed = (
                now - state.window_start
            )

            if elapsed >= effective_window:
                state.window_start = now
                state.request_count = 1

                return (
                    True,
                    effective_limit - 1,
                )

            if state.request_count >= effective_limit:
                return False, 0

            state.request_count += 1

            remaining = (
                effective_limit
                - state.request_count
            )

            return True, remaining


rate_limiter = RateLimiter()