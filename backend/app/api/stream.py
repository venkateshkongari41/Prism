from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.providers.openrouter import OpenRouterProvider
from app.schemas.chat import ChatCompletionRequest

router = APIRouter()


@router.post("/v1/test/stream")
async def test_stream(request: ChatCompletionRequest):

    provider = OpenRouterProvider()

    generator = provider.stream_chat(
        model="openrouter/free",
        messages=[
            message.model_dump()
            for message in request.messages
        ],
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )