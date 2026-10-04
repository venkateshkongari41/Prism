import logging
import time

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import Request


logger = logging.getLogger("prism")


class LoggingMiddleware(
    BaseHTTPMiddleware
):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        start_time = time.perf_counter()

        response = await call_next(
            request
        )

        latency_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        request_id = getattr(
            request.state,
            "request_id",
            None,
        )

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round(
                    latency_ms,
                    2,
                ),
            },
        )

        return response