from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    primary: str
    fallbacks: tuple[str, ...]


ROUTES: dict[str, Route] = {
    "fast": Route(
        primary="openrouter",
        fallbacks=("mock",),
    ),
    "smart": Route(
        primary="mock",
        fallbacks=("openrouter",),
    ),
}