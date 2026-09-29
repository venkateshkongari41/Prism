class PrismError(Exception):
    """Base exception for Prism application errors."""


class ModelAliasNotFoundError(PrismError):
    """Raised when a requested model alias does not exist."""