class ProviderError(Exception):
    """Base provider error."""


class ProviderTimeoutError(ProviderError):
    """Provider request timed out."""


class ProviderRateLimitError(ProviderError):
    """Provider rate limit was exceeded."""


class ProviderTemporaryError(ProviderError):
    """Provider returned a temporary/server-side failure."""


class ProviderAuthenticationError(ProviderError):
    """Provider authentication failed."""


class ProviderBadRequestError(ProviderError):
    """Provider rejected the request."""
    
class ModelAliasNotFoundError(Exception):
    """Requested model alias was not found."""
    
class BudgetExceededError(Exception):
    """Monthly budget has been exhausted."""