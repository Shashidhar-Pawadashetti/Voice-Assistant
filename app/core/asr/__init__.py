"""ASR subsystem exports and provider factory."""

from app.config import get_settings
from app.core.asr.indic_conformer import IndicConformerAdapter
from app.core.asr.interface import SpeechRecognizer
from app.core.asr.mock import MockSpeechRecognizer
from app.core.asr.schemas import ASRResult


def get_speech_recognizer() -> SpeechRecognizer:
    """Return configured SpeechRecognizer instance based on application settings."""
    settings = get_settings()
    if settings.ASR_PROVIDER == "mock":
        return MockSpeechRecognizer()
    return IndicConformerAdapter()


__all__ = [
    "SpeechRecognizer",
    "ASRResult",
    "IndicConformerAdapter",
    "MockSpeechRecognizer",
    "get_speech_recognizer",
]
