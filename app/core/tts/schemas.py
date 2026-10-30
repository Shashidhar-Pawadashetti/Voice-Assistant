"""TTS schema definitions and synthesis result models."""

from typing import Any, Dict
from pydantic import BaseModel, Field


class TTSResult(BaseModel):
    """Result of speech synthesis."""

    audio_bytes: bytes = Field(repr=False, description="Synthesized PCM WAV or playback-compatible audio bytes")
    content_type: str = Field(default="audio/wav", description="MIME content type")
    duration_ms: int = Field(ge=0, description="Estimated audio duration in milliseconds")
    sample_rate: int = Field(default=22050, description="Audio sample rate in Hz")
    provider: str = Field(description="TTS provider identifier (e.g. indic_tts)")
    model_version: str = Field(description="TTS model/checkpoint version string")
    voice_gender: str = Field(default="female", description="Voice gender (female/male)")
    diagnostic_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Non-PII diagnostic metadata (latency_ms, character_count, etc.)",
    )
