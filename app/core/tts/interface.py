"""TTS provider abstract interface."""

from typing import Protocol
from app.core.tts.schemas import TTSResult


class SpeechSynthesizer(Protocol):
    """Protocol defining the contract for text-to-speech synthesis engines."""

    async def synthesize(
        self,
        text: str,
        *,
        language: str = "kn",
        voice_gender: str = "female",
    ) -> TTSResult:
        """Synthesize text into speech audio bytes.

        Args:
            text: Input text (Kannada).
            language: ISO-639-1 language code (default 'kn').
            voice_gender: 'female' or 'male'.

        Returns:
            TTSResult with audio_bytes and playback metadata.

        Raises:
            TTSTimeoutError: If synthesis times out.
            TTSUnavailableError: If TTS service is unreachable.
            TTSModelError: If model encounters an internal error.
        """
        ...

    async def check_health(self) -> bool:
        """Verify TTS engine readiness."""
        ...
