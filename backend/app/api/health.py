from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(
    tags=["health"],
)


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "prism-gateway",
        "environment": settings.environment,
    }


@router.get("/ready")
async def readiness():
    return {
        "status": "ready",
    }