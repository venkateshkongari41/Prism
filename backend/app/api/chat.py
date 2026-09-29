from fastapi import APIRouter, HTTPException

from app.core.exceptions import ModelAliasNotFoundError
from app.core.model_resolver import model_resolver
from app.providers.registry import provider_registry
from app.schemas.chat import ChatCompletionRequest

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):

    try:
        alias = model_resolver.resolve(request.model)

    except ModelAliasNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    provider = provider_registry.get(alias.provider)

    response = await provider.chat(
        model=alias.model,
        messages=[
            message.model_dump()
            for message in request.messages
        ],
        stream=request.stream,
    )

    return response