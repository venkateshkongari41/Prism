from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.auth.service import get_api_key_identity


api_key_header = APIKeyHeader(
    name="Authorization",
    auto_error=False,
)


async def require_api_key(
    authorization: str | None = Depends(
        api_key_header
    ),
) -> dict:

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    scheme, separator, token = (
        authorization.partition(" ")
    )

    if (
        not separator
        or scheme.lower() != "bearer"
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header",
        )

    identity = get_api_key_identity(
        token
    )

    if identity is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key",
        )

    return identity