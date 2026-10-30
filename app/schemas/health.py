"""Pydantic schemas for health and readiness checks."""

from datetime import datetime, timezone
from typing import Dict, Optional
from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    """Process liveness response model."""

    status: str = Field(default="ok", description="Liveness status")
    version: str = Field(default="0.1.0", description="Application version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DependencyHealth(BaseModel):
    """Individual dependency health status."""

    status: str = Field(description="UP or DOWN")
    latency_ms: Optional[float] = Field(default=None, description="Probe latency in milliseconds")
    error: Optional[str] = Field(default=None, description="Sanitized error description if down")


class ReadinessResponse(BaseModel):
    """Readiness response model verifying essential external dependencies."""

    status: str = Field(description="ok or degraded")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dependencies: Dict[str, DependencyHealth] = Field(description="Health statuses of external services")
