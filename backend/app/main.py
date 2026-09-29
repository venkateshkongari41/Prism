from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "prism-gateway",
        "environment": settings.environment,
    }


app.include_router(chat_router)