class DifyIntegrationError(Exception):
    """Base error for Dify integration layer."""


class DifyUnavailableError(DifyIntegrationError):
    """Raised when Dify integration is not configured or temporarily unavailable."""


class DifyConfigurationError(DifyUnavailableError):
    """Raised when required Dify configuration is missing."""


class DifyTimeoutError(DifyUnavailableError):
    """Raised when a Dify request times out."""


class DifyRequestError(DifyIntegrationError):
    """Raised when Dify returns an invalid or failed response."""
