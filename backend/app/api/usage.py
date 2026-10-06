from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_api_key
from app.usage.usage_service import get_usage, get_usage_summary

router = APIRouter(
    prefix="/v1/usage",
    tags=["usage"],
)


@router.get("")
async def usage(
    identity=Depends(require_api_key),
    limit: int = Query(100, ge=1, le=500),
    hours: int | None = Query(None, ge=1),
):
    return {
        "application": identity["application_name"],
        "items": get_usage(
            application_name=identity["application_name"],
            limit=limit,
            hours=hours,
        ),
    }


@router.get("/summary")
async def usage_summary(
    identity=Depends(require_api_key),
    hours: int | None = Query(None, ge=1),
):
    return {
        "application": identity["application_name"],
        "summary": get_usage_summary(
            application_name=identity["application_name"],
            hours=hours,
        ),
    }
