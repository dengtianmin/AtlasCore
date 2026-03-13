class DifyIntegrationError(Exception):
    """Base error for Dify integration layer."""


class DifyUnavailableError(DifyIntegrationError):
    """Raised when Dify integration is not configured or temporarily unavailable."""
