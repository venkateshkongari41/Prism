from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.auth.service import (
    create_api_key,
    list_api_keys,
    revoke_api_key,
)

from app.usage.usage_service import (
    get_usage as get_usage_records,
    get_usage_summary,
    get_usage_by_application,
)

from app.auth.database import get_connection
from app.core.config import settings


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


class CreateApiKeyRequest(BaseModel):
    name: str
    application_name: str


class UpdateRateLimitRequest(BaseModel):
    rate_limit: int = Field(
        gt=0,
        description="Maximum number of requests allowed",
    )

    rate_window_seconds: int = Field(
        gt=0,
        description="Rate-limit window in seconds",
    )


def validate_admin_key(
    admin_key: str | None,
) -> None:

    if not settings.prism_admin_key:
        raise HTTPException(
            status_code=500,
            detail="Admin key is not configured",
        )

    if admin_key != settings.prism_admin_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin key",
        )


@router.post("/keys")
async def create_key(
    request: CreateApiKeyRequest,
    x_prism_admin_key: str | None = Header(
        default=None
    ),
):

    validate_admin_key(
        x_prism_admin_key
    )

    api_key = create_api_key(
        name=request.name,
        application_name=(
            request.application_name
        ),
    )

    return {
        "name": request.name,
        "application_name": (
            request.application_name
        ),
        "api_key": api_key,
        "message": (
            "Store this API key securely. "
            "It will not be returned again."
        ),
    }


@router.get("/keys")
async def get_keys(
    x_prism_admin_key: str | None = Header(
        default=None
    ),
):

    validate_admin_key(
        x_prism_admin_key
    )

    return {
        "keys": list_api_keys()
    }


@router.delete("/keys/{key_id}")
async def revoke_key(
    key_id: int,
    x_prism_admin_key: str | None = Header(
        default=None
    ),
):

    validate_admin_key(
        x_prism_admin_key
    )

    revoked = revoke_api_key(
        key_id
    )

    if not revoked:
        raise HTTPException(
            status_code=404,
            detail="API key not found",
        )

    return {
        "id": key_id,
        "is_active": False,
        "message": "API key revoked",
    }


@router.patch(
    "/keys/{key_id}/rate-limit"
)
async def update_rate_limit(
    key_id: int,
    request: UpdateRateLimitRequest,
    x_prism_admin_key: str | None = Header(
        default=None
    ),
):

    validate_admin_key(
        x_prism_admin_key
    )

    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT
                id,
                name,
                application_name,
                rate_limit,
                rate_window_seconds
            FROM api_keys
            WHERE id = ?
            """,
            (key_id,),
        ).fetchone()

        if row is None:

            raise HTTPException(
                status_code=404,
                detail="API key not found",
            )

        connection.execute(
            """
            UPDATE api_keys
            SET
                rate_limit = ?,
                rate_window_seconds = ?
            WHERE id = ?
            """,
            (
                request.rate_limit,
                request.rate_window_seconds,
                key_id,
            ),
        )

        connection.commit()

        return {
            "id": key_id,
            "application_name": row[
                "application_name"
            ],
            "rate_limit": request.rate_limit,
            "rate_window_seconds": (
                request.rate_window_seconds
            ),
            "message": (
                "Rate limit updated successfully"
            ),
        }

    finally:
        connection.close()


@router.get("/usage")
async def get_usage(
    application_name: str | None = None,
    limit: int = 100,
    hours: int | None = None,
    x_prism_admin_key: str | None = Header(
        default=None
    ),
):

    validate_admin_key(
        x_prism_admin_key
    )

    if limit <= 0:
        raise HTTPException(
            status_code=400,
            detail="Limit must be greater than 0",
        )

    if limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="Limit cannot exceed 1000",
        )

    if hours is not None and hours <= 0:
        raise HTTPException(
            status_code=400,
            detail="Hours must be greater than 0",
        )

    if hours is not None:

        # Get the filtered records through
        # the usage service.
        records = get_usage_records(
            application_name=application_name,
            limit=limit,
        )

        # The existing get_usage() service does
        # not yet support an hours parameter.
        # Time filtering for this endpoint will
        # be added in the next step.
        #
        # For now, return the normal usage records.
        return {
            "usage": records,
            "hours": hours,
        }

    return {
        "usage": get_usage_records(
            application_name=application_name,
            limit=limit,
        )
    }


@router.get("/usage/summary")
async def usage_summary(
    application_name: str | None = None,
    hours: int | None = None,
    x_prism_admin_key: str | None = Header(
        default=None
    ),
):

    validate_admin_key(
        x_prism_admin_key
    )

    if hours is not None and hours <= 0:
        raise HTTPException(
            status_code=400,
            detail="Hours must be greater than 0",
        )

    summary = get_usage_summary(
        application_name=application_name,
        hours=hours,
    )

    return {
        "application_name": application_name,
        "hours": hours,
        "summary": summary,
    }


@router.get("/usage/applications")
async def get_application_usage(
    hours: int | None = None,
    x_prism_admin_key: str | None = Header(
        default=None
    ),
):

    validate_admin_key(
        x_prism_admin_key
    )

    if hours is not None and hours <= 0:
        raise HTTPException(
            status_code=400,
            detail="Hours must be greater than 0",
        )

    return {
        "hours": hours,
        "applications": (
            get_usage_by_application(
                hours=hours
            )
        ),
    }