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


class AudioValidationError(KrishiMitraError):
    """Raised when uploaded audio violates format, size, or duration constraints."""

    def __init__(self, message: str = "Audio validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUDIO_VALIDATION_FAILED",
            status_code=400,
            retryable=False,
            details=details,
        )


class AudioNormalizationError(KrishiMitraError):
    """Raised when audio conversion or normalization fails."""

    def __init__(self, message: str = "Audio normalization failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUDIO_NORMALIZATION_FAILED",
            status_code=422,
            retryable=False,
            details=details,
        )


class ASRModelError(KrishiMitraError):
    """Base exception for ASR transcription errors."""

    def __init__(
        self,
        message: str,
        code: str = "ASR_ERROR",
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


class ASRTimeoutError(ASRModelError):
    """Raised when ASR transcription times out."""

    def __init__(self, message: str = "ASR transcription timed out", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ASR_TIMEOUT",
            status_code=504,
            retryable=True,
            details=details,
        )


class ASRUnavailableError(ASRModelError):
    """Raised when ASR model or service is unreachable."""

    def __init__(self, message: str = "ASR service unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ASR_UNAVAILABLE",
            status_code=503,
            retryable=True,
            details=details,
        )


class TTSModelError(KrishiMitraError):
    """Base exception for TTS speech synthesis errors."""

    def __init__(
        self,
        message: str,
        code: str = "TTS_ERROR",
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


class TTSTimeoutError(TTSModelError):
    """Raised when TTS synthesis times out."""

    def __init__(self, message: str = "TTS synthesis timed out", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="TTS_TIMEOUT",
            status_code=504,
            retryable=True,
            details=details,
        )


class TTSUnavailableError(TTSModelError):
    """Raised when TTS service or checkpoint is unreachable."""

    def __init__(self, message: str = "TTS service unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="TTS_UNAVAILABLE",
            status_code=503,
            retryable=True,
            details=details,
        )


class InvalidStateTransitionError(KrishiMitraError):
    """Raised when an illegal dialogue state transition is attempted."""

    def __init__(self, from_state: str, to_state: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Invalid dialogue transition from '{from_state}' to '{to_state}'",
            code="INVALID_STATE_TRANSITION",
            status_code=400,
            retryable=False,
            details=details or {"from_state": from_state, "to_state": to_state},
        )


class OptimisticLockError(KrishiMitraError):
    """Raised when concurrent updates conflict on a conversation version."""

    def __init__(self, message: str = "Conversation was modified concurrently. Please retry.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONCURRENCY_CONFLICT",
            status_code=409,
            retryable=True,
            details=details,
        )


class ConversationExpiredError(KrishiMitraError):
    """Raised when an operation is attempted on an expired or completed conversation."""

    def __init__(self, message: str = "Conversation has expired or is already completed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONVERSATION_EXPIRED",
            status_code=410,
            retryable=False,
            details=details,
        )


# Convenient domain aliases for BOLA and resource lookups
ConversationOwnershipError = AuthorizationError
NotFoundError = ResourceNotFoundError
