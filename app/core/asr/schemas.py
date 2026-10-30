"""ASR schema definitions and transcription result models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ASRResult(BaseModel):
    """Normalized transcription result from an ASR provider."""

    text: str = Field(description="Transcription text in native script")
    language: str = Field(default="kn", description="Language code (e.g. kn for Kannada)")
    duration_ms: int = Field(ge=0, description="Audio duration in milliseconds")
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Calibrated confidence score if provided by the model; None otherwise",
    )
    provider: str = Field(description="ASR provider identifier (e.g. indic_conformer)")
    model_version: str = Field(description="Model/checkpoint version string")
    warnings: List[str] = Field(default_factory=list, description="Quality warnings (silence, clipping, etc.)")
    diagnostic_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Non-PII diagnostic metadata (latency_ms, sample_rate, etc.)",
    )
