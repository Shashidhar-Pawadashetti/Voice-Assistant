"""ASR provider abstract interface."""

from pathlib import Path
from typing import Protocol
from app.core.asr.schemas import ASRResult


class SpeechRecognizer(Protocol):
    """Protocol defining the contract for speech recognition engines."""

    async def transcribe(self, audio_path: Path, *, language: str = "kn") -> ASRResult:
        """Transcribe a normalized audio file to text.

        Args:
            audio_path: Path to normalized 16 kHz mono PCM WAV file.
            language: Target ISO-639-1 language code (default 'kn' for Kannada).

        Returns:
            ASRResult containing the transcript, language, and diagnostic metadata.

        Raises:
            ASRTimeoutError: If transcription takes longer than configured timeout.
            ASRUnavailableError: If ASR service is unreachable.
            ASRModelError: If model encounters an internal inference error.
        """
        ...

    async def check_health(self) -> bool:
        """Verify provider availability and model readiness."""
        ...
