from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.auth.database import initialize_database
from app.core.config import settings
from app.core.error_handlers import (
    model_alias_not_found_handler,
    provider_authentication_handler,
    provider_bad_request_handler,
    provider_rate_limit_handler,
    provider_temporary_handler,
    provider_timeout_handler,
    validation_error_handler,
)
from app.core.exceptions import ModelAliasNotFoundError
from app.middleware.logging import LoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderRateLimitError,
    ProviderTemporaryError,
    ProviderTimeoutError,
)


initialize_database()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Prism is an LLM gateway that provides a unified "
        "API for model routing, authentication, rate limiting, "
        "usage analytics, streaming, retries, and provider "
        "fallback handling."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)


app.include_router(
    admin_router
)

app.include_router(
    chat_router
)

app.include_router(
    health_router
)


app.add_middleware(
    RequestIDMiddleware
)

app.add_middleware(
    LoggingMiddleware
)


app.add_exception_handler(
    ProviderTimeoutError,
    provider_timeout_handler,
)

app.add_exception_handler(
    ProviderRateLimitError,
    provider_rate_limit_handler,
)

app.add_exception_handler(
    ProviderTemporaryError,
    provider_temporary_handler,
)

app.add_exception_handler(
    ProviderAuthenticationError,
    provider_authentication_handler,
)

app.add_exception_handler(
    ProviderBadRequestError,
    provider_bad_request_handler,
)

app.add_exception_handler(
    ModelAliasNotFoundError,
    model_alias_not_found_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_error_handler,
)