"""Standard API error response envelope following 09_API_CONTRACT.md."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error object conforming to Krishi Mitra API contract."""

    code: str = Field(description="Stable application error code")
    message: str = Field(description="Human-readable safe error message")
    retryable: bool = Field(default=False, description="Whether the client may retry the operation")
    request_id: Optional[str] = Field(default=None, description="Unique correlation request ID")
    details: Dict[str, Any] = Field(default_factory=dict, description="Safe machine-readable context")


class APIErrorResponse(BaseModel):
    """Top-level error response envelope."""

    error: ErrorDetail
