"""Voice turn schemas and response envelopes."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.extraction import ExtractedEntity, Intent


class VoiceTurnResponse(BaseModel):
    """Result of end-to-end voice processing turn."""

    transcript: str = Field(description="Transcribed Kannada utterance")
    language: str = Field(default="kn", description="Detected or configured language code")
    intent: Intent = Field(description="Extracted primary agricultural intent")
    entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted agricultural entities")
    unresolved_phrases: List[str] = Field(default_factory=list, description="Unresolved phrases requiring clarification")
    correction_target: Optional[str] = Field(default=None, description="Corrected slot name if turn was a correction")
    response_text: str = Field(description="Grounded Kannada text response for farmer")
    audio_id: Optional[str] = Field(default=None, description="Ephemeral audio ID for TTS response playback")
    audio_url: Optional[str] = Field(default=None, description="Playback URL for TTS audio (valid for 10 minutes)")
    speech_available: bool = Field(default=False, description="Whether TTS audio is ready and available for playback")
    asr_duration_ms: int = Field(ge=0, description="Audio input duration in milliseconds")
    tts_duration_ms: Optional[int] = Field(default=None, description="Generated speech duration in milliseconds")
    turn_latency_ms: int = Field(ge=0, description="Total turn end-to-end processing latency in milliseconds")
    diagnostic_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Non-PII pipeline diagnostics (models, providers, status)",
    )
