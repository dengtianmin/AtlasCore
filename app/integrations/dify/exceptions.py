from __future__ import annotations

from typing import Any


class DifyIntegrationError(Exception):
    """Base error for Dify integration layer."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        raw: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.raw = raw or {}
        super().__init__(message)


class DifyClientError(DifyIntegrationError):
    """Base error for request/response failures against Dify."""


class DifyUnavailableError(DifyClientError):
    """Raised when Dify integration is not configured or temporarily unavailable."""


class DifyConfigurationError(DifyUnavailableError):
    """Raised when required Dify configuration is missing."""


class DifyAuthError(DifyClientError):
    """Raised when Dify rejects authentication or authorization."""


class DifyBadRequestError(DifyClientError):
    """Raised when Dify rejects request parameters."""


class DifyTimeoutError(DifyUnavailableError):
    """Raised when a Dify request times out."""


class DifyServiceUnavailableError(DifyUnavailableError):
    """Raised when Dify is temporarily unavailable."""


class DifyQuotaExceededError(DifyClientError):
    """Raised when Dify quota/rate limits are exceeded."""


class DifyWorkflowExecutionError(DifyClientError):
    """Raised when a Dify workflow finishes with failure."""


class DifyWorkflowNotFoundError(DifyClientError):
    """Raised when a workflow or workflow run is not found."""


class DifyFileUploadError(DifyClientError):
    """Raised when file upload fails."""


class DifyFileTooLargeError(DifyFileUploadError):
    """Raised when Dify rejects an oversized file."""


class DifyUnsupportedFileTypeError(DifyFileUploadError):
    """Raised when Dify rejects the file type."""


class DifyProviderInitError(DifyClientError):
    """Raised when a provider backing the Dify app is not initialized."""


class DifyAppUnavailableError(DifyClientError):
    """Raised when the Dify app is unavailable."""


class DifyRequestError(DifyClientError):
    """Backward-compatible alias for generic Dify request failures."""
