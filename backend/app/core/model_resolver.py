from app.core.exceptions import ModelAliasNotFoundError
from app.core.model_aliases import (
    MODEL_ALIASES,
    ModelAlias,
)


AUTO_ALIAS = "auto"

# Simple, explainable difficulty indicators.
COMPLEXITY_KEYWORDS = {
    "analyze",
    "analyse",
    "architecture",
    "architect",
    "debug",
    "debugging",
    "compare",
    "comparison",
    "design",
    "explain",
    "implement",
    "optimization",
    "optimize",
    "reason",
    "reasoning",
    "refactor",
    "tradeoff",
    "trade-off",
}


class ModelResolver:

    def resolve(
        self,
        alias: str,
        messages: list[dict] | None = None,
    ) -> ModelAlias:

        if alias == AUTO_ALIAS:

            if not messages:
                return MODEL_ALIASES["fast"]

            if self._is_complex_request(
                messages
            ):
                return MODEL_ALIASES["smart"]

            return MODEL_ALIASES["fast"]

        try:
            return MODEL_ALIASES[alias]

        except KeyError:
            raise ModelAliasNotFoundError(
                f"Unknown model alias: {alias}"
            )

    def resolve_alias(
        self,
        alias: str,
        messages: list[dict] | None = None,
    ) -> str:

        if alias != AUTO_ALIAS:
            # Validate the alias.
            self.resolve(alias, messages)

            return alias

        if not messages:
            return "fast"

        if self._is_complex_request(
            messages
        ):
            return "smart"

        return "fast"

    def _is_complex_request(
        self,
        messages: list[dict],
    ) -> bool:

        user_text = " ".join(
            str(message.get("content", ""))
            for message in messages
            if message.get("role") == "user"
        ).lower()

        words = user_text.split()

        # Long prompts are more likely to require
        # the smart model.
        if len(words) >= 120:
            return True

        # Explicit complexity indicators.
        for keyword in COMPLEXITY_KEYWORDS:

            if keyword in user_text:
                return True

        # Multiple questions / instructions generally
        # indicate a more complex request.
        if user_text.count("?") >= 2:
            return True

        return False


model_resolver = ModelResolver()