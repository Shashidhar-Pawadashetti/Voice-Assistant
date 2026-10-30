"""Domain exceptions for Krishi Mitra AI subsystem."""

from typing import Any, Dict, Optional


class KrishiMitraError(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}


class DatabaseConnectionError(KrishiMitraError):
    """Raised when database connection or ping fails."""

    def __init__(self, message: str = "Database connection unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_UNAVAILABLE",
            status_code=503,
            retryable=True,
            details=details,
        )


class LLMModelError(KrishiMitraError):
    """Base exception for LLM operations."""

    def __init__(
        self,
        message: str,
        code: str = "LLM_ERROR",
        status_code: int = 502,
        retryable: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            retryable=retryable,
            details=details,
        )


class LLMTimeoutError(LLMModelError):
    """Raised when LLM generation or structured extraction times out."""

    def __init__(self, message: str = "LLM extraction request timed out", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="LLM_TIMEOUT",
            status_code=504,
            retryable=True,
            details=details,
        )


class LLMUnavailableError(LLMModelError):
    """Raised when Ollama server or configured model is unreachable."""

    def __init__(self, message: str = "LLM service unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="LLM_UNAVAILABLE",
            status_code=503,
            retryable=True,
            details=details,
        )


class LLMSchemaValidationError(LLMModelError):
    """Raised when LLM output violates Pydantic extraction schema after bounded retries."""

    def __init__(self, message: str = "LLM structured extraction schema validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="LLM_SCHEMA_VALIDATION_FAILED",
            status_code=422,
            retryable=False,
            details=details,
        )


class ResourceNotFoundError(KrishiMitraError):
    """Raised when an authorized resource is not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            retryable=False,
            details=details,
        )


class AuthorizationError(KrishiMitraError):
    """Raised when resource ownership check fails (BOLA protection)."""

    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            retryable=False,
            details=details,
        )


class AuthenticationError(KrishiMitraError):
    """Raised when user credentials or token is invalid."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            retryable=False,
            details=details,
        )


class IdempotencyConflictError(KrishiMitraError):
    """Raised when an idempotency key is reused with a different payload."""

    def __init__(self, message: str = "Idempotency key reused with different payload", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="IDEMPOTENCY_KEY_REUSED",
            status_code=409,
            retryable=False,
            details=details,
        )
