from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class LLMProvider(ABC):

    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        pass

    async def stream_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[str]:
        raise NotImplementedError(
            "Streaming is not implemented for this provider"
        )
        yield ""