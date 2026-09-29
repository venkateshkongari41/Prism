from app.core.exceptions import ModelAliasNotFoundError
from app.core.model_aliases import MODEL_ALIASES, ModelAlias


class ModelResolver:

    def resolve(self, alias: str) -> ModelAlias:
        try:
            return MODEL_ALIASES[alias]
        except KeyError:
            raise ModelAliasNotFoundError(
                f"Unknown model alias: {alias}"
            )


model_resolver = ModelResolver()