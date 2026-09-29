from app.providers.mock import MockProvider
from app.providers.openrouter import OpenRouterProvider
from app.providers.provider import LLMProvider


class ProviderRegistry:

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}

    def register(
        self,
        name: str,
        provider: LLMProvider,
    ) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> LLMProvider:
        try:
            return self._providers[name]
        except KeyError:
            raise ValueError(
                f"Unknown provider: {name}"
            )


provider_registry = ProviderRegistry()

provider_registry.register(
    "mock",
    MockProvider(),
)

provider_registry.register(
    "openrouter",
    OpenRouterProvider(),
)