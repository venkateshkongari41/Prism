from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderRateLimitError,
    ProviderTemporaryError,
    ProviderTimeoutError,
)

from app.core.exceptions import (
    ModelAliasNotFoundError,
)

from app.core.exceptions import (
    ModelAliasNotFoundError,
)


def _error_response(
    request: Request,
    error_type: str,
    message: str,
    status_code: int,
):
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": error_type,
                "message": message,
                "request_id": request_id,
            }
        },
        headers={
            "X-Request-ID": request_id
        }
        if request_id
        else {},
    )


async def provider_timeout_handler(
    request: Request,
    exc: ProviderTimeoutError,
):
    return _error_response(
        request,
        "provider_timeout",
        str(exc),
        504,
    )


async def provider_rate_limit_handler(
    request: Request,
    exc: ProviderRateLimitError,
):
    return _error_response(
        request,
        "provider_rate_limit",
        str(exc),
        429,
    )


async def provider_temporary_handler(
    request: Request,
    exc: ProviderTemporaryError,
):
    return _error_response(
        request,
        "provider_temporary_error",
        str(exc),
        502,
    )


async def provider_authentication_handler(
    request: Request,
    exc: ProviderAuthenticationError,
):
    return _error_response(
        request,
        "provider_authentication_error",
        str(exc),
        502,
    )


async def provider_bad_request_handler(
    request: Request,
    exc: ProviderBadRequestError,
):
    return _error_response(
        request,
        "provider_bad_request",
        str(exc),
        400,
    )
    
    
async def model_alias_not_found_handler(
    request: Request,
    exc: ModelAliasNotFoundError,
):
    return _error_response(
        request,
        "model_not_found",
        str(exc),
        400,
    )
    
async def model_alias_not_found_handler(
    request: Request,
    exc: ModelAliasNotFoundError,
):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "type": "model_alias_not_found",
                "message": str(exc),
            }
        },
    )
    

async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "message": "Invalid request",
                "details": exc.errors(),
            }
        },
    )