"""TTS subsystem exports and provider factory."""

from app.config import get_settings
from app.core.tts.indic_tts import IndicTTSAdapter
from app.core.tts.interface import SpeechSynthesizer
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.sanitizer import sanitize_tts_text
from app.core.tts.schemas import TTSResult
from app.core.tts.storage import EphemeralAudioStore, get_ephemeral_audio_store


def get_speech_synthesizer() -> SpeechSynthesizer:
    """Return configured SpeechSynthesizer instance based on application settings."""
    settings = get_settings()
    if settings.TTS_PROVIDER == "mock":
        return MockSpeechSynthesizer()
    return IndicTTSAdapter()


__all__ = [
    "SpeechSynthesizer",
    "TTSResult",
    "IndicTTSAdapter",
    "MockSpeechSynthesizer",
    "EphemeralAudioStore",
    "get_ephemeral_audio_store",
    "get_speech_synthesizer",
    "sanitize_tts_text",
]
