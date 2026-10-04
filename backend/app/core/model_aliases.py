from dataclasses import dataclass


@dataclass(frozen=True)
class ModelAlias:
    provider: str
    model: str


MODEL_ALIASES: dict[str, ModelAlias] = {
    "fast": ModelAlias(
        provider="openrouter",
        model="openrouter/free",
    ),
    "smart": ModelAlias(
        provider="huggingface",
        model="huggingface/free",
    ),
}