from dataclasses import dataclass


@dataclass(frozen=True)
class Route:

    primary: str

    fallbacks: tuple[str, ...]


ROUTES: dict[str, Route] = {

    "fast": Route(
        primary="openrouter",
        fallbacks=(
            "huggingface",
            "mock",
        ),
    ),

    "smart": Route(
        primary="huggingface",
        fallbacks=(
            "openrouter",
            "mock",
        ),
    ),
}