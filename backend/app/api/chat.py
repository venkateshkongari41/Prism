from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.auth.dependencies import require_api_key
from app.cache import semantic_cache
from app.core.config import settings
from app.core.exceptions import ModelAliasNotFoundError
from app.core.model_resolver import model_resolver
from app.core.rate_limit_dependency import check_rate_limit
from app.core.router import routing_engine
from app.schemas.chat import ChatCompletionRequest


router = APIRouter()


@router.post(
    "/v1/chat/completions",
)
async def chat_completions(
    request: ChatCompletionRequest,
    identity: dict = Depends(
        require_api_key
    ),
):
    """
    OpenAI-compatible chat completion endpoint.

    Responsibilities:
    - Authenticate the virtual API key.
    - Enforce rate limiting.
    - Resolve model aliases, including `auto`.
    - Perform tenant-isolated semantic cache lookup.
    - Route requests through the provider routing engine.
    - Return provider/cache/fallback/cost headers.
    """

    remaining = await check_rate_limit(
        identity
    )

    try:
        # ---------------------------------------------------------
        # Convert request messages into plain dictionaries
        # ---------------------------------------------------------

        messages = [
            message.model_dump()
            for message in request.messages
        ]

        # ---------------------------------------------------------
        # Resolve the requested model.
        #
        # For:
        #   fast  -> fast
        #   smart -> smart
        #   auto  -> fast/smart based on the prompt
        # ---------------------------------------------------------

        resolved_alias = model_resolver.resolve_alias(
            request.model,
            messages,
        )

        alias = model_resolver.resolve(
            resolved_alias,
            messages,
        )

        # ---------------------------------------------------------
        # Tenant/application identifier
        #
        # The semantic cache must never be shared across tenants.
        # `id` is the API-key/application database identifier.
        # ---------------------------------------------------------

        application_id = identity["id"]

        # ---------------------------------------------------------
        # Streaming path
        #
        # We intentionally bypass the semantic cache for streaming
        # because the current cache stores completed JSON responses.
        # ---------------------------------------------------------

        if request.stream:

            stream_result = await routing_engine.stream(
                alias=resolved_alias,
                model=alias.model,
                messages=messages,
            )

            return StreamingResponse(
                stream_result.stream,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "X-Prism-Provider": (
                        stream_result.provider
                    ),
                    "X-Prism-Cache": "BYPASS",
                    "X-Prism-Fallback": str(
                        stream_result.fallback_used
                    ).lower(),
                    "X-Prism-Cost-USD": "0",
                    "X-Prism-Application": (
                        identity[
                            "application_name"
                        ]
                    ),
                    "X-Prism-Resolved-Model": (
                        resolved_alias
                    ),
                    "X-RateLimit-Remaining": str(
                        remaining
                    ),
                },
            )

        # ---------------------------------------------------------
        # Semantic cache lookup
        #
        # Cache scope:
        #   application_id + model + semantic similarity
        #
        # This prevents:
        #   Tenant A's cached response
        #   from being returned to Tenant B.
        # ---------------------------------------------------------

        if settings.semantic_cache_enabled:

            cache_result = await semantic_cache.get(
                application_id=application_id,
                model=alias.model,
                messages=messages,
            )

            if cache_result is not None:

                return JSONResponse(
                    content=cache_result["response"],
                    headers={
                        "X-Prism-Provider": "cache",
                        "X-Prism-Cache": (
                            cache_result[
                                "cache_type"
                            ].upper()
                        ),
                        "X-Prism-Fallback": "false",
                        "X-Prism-Cost-USD": "0",
                        "X-Prism-Application": (
                            identity[
                                "application_name"
                            ]
                        ),
                        "X-Prism-Resolved-Model": (
                            resolved_alias
                        ),
                        "X-RateLimit-Remaining": str(
                            remaining
                        ),
                    },
                )

        # ---------------------------------------------------------
        # Provider execution
        # ---------------------------------------------------------

        result = await routing_engine.execute(
            alias=resolved_alias,
            model=alias.model,
            messages=messages,
            stream=False,
        )

        # ---------------------------------------------------------
        # Provider usage / cost
        #
        # Providers normalize usage into `prism_usage`.
        # ---------------------------------------------------------

        usage = result.response.get(
            "prism_usage",
            {},
        )

        cost = usage.get(
            "cost",
            0,
        )

        # ---------------------------------------------------------
        # Store successful provider response in semantic cache.
        #
        # Only non-streaming successful responses are cached.
        # ---------------------------------------------------------

        if settings.semantic_cache_enabled:

            await semantic_cache.set(
                application_id=application_id,
                model=alias.model,
                messages=messages,
                response=result.response,
            )

        # ---------------------------------------------------------
        # Normal provider response
        # ---------------------------------------------------------

        return JSONResponse(
            content=result.response,
            headers={
                "X-Prism-Provider": (
                    result.provider
                ),
                "X-Prism-Cache": "MISS",
                "X-Prism-Fallback": str(
                    result.fallback_used
                ).lower(),
                "X-Prism-Cost-USD": (
                    f"{float(cost):.10f}"
                ),
                "X-Prism-Application": (
                    identity[
                        "application_name"
                    ]
                ),
                "X-Prism-Resolved-Model": (
                    resolved_alias
                ),
                "X-RateLimit-Remaining": str(
                    remaining
                ),
            },
        )

    except ModelAliasNotFoundError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc