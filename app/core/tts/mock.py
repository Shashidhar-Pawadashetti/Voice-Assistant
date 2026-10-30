"""Mock TTS provider generating valid synthetic WAV audio for testing."""

import io
import math
import struct
import time
import wave
from app.core.tts.interface import SpeechSynthesizer
from app.core.tts.schemas import TTSResult
from app.core.tts.sanitizer import sanitize_tts_text


def generate_synthetic_wav_bytes(
    duration_seconds: float = 0.5,
    sample_rate: int = 16000,
    frequency: float = 440.0,
) -> bytes:
    """Generate valid PCM 16-bit mono WAV bytes for testing."""
    num_samples = int(duration_seconds * sample_rate)
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Generate smooth sine wave
        samples = []
        for i in range(num_samples):
            # Soft envelope to avoid clicks
            envelope = min(i / 1000.0, (num_samples - i) / 1000.0, 1.0)
            sample_val = int(32767.0 * 0.3 * envelope * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            samples.append(struct.pack("<h", sample_val))

        wav_file.writeframes(b"".join(samples))

    return buffer.getvalue()


class MockSpeechSynthesizer(SpeechSynthesizer):
    """Mock implementation returning playable synthetic audio bytes."""

    def __init__(
        self,
        sample_rate: int = 16000,
        healthy: bool = True,
        simulate_error: bool = False,
    ):
        self.sample_rate = sample_rate
        self.healthy = healthy
        self.simulate_error = simulate_error

    async def synthesize(
        self,
        text: str,
        *,
        language: str = "kn",
        voice_gender: str = "female",
    ) -> TTSResult:
        if self.simulate_error:
            from app.core.exceptions import TTSModelError

            raise TTSModelError("Simulated mock TTS inference failure")

        start_time = time.perf_counter()
        sanitized = sanitize_tts_text(text)

        # Approximate duration based on character length (10 chars ~ 0.5s, min 0.5s, max 5s)
        estimated_duration_sec = max(0.5, min(len(sanitized) * 0.06, 5.0))
        audio_bytes = generate_synthetic_wav_bytes(
            duration_seconds=estimated_duration_sec,
            sample_rate=self.sample_rate,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return TTSResult(
            audio_bytes=audio_bytes,
            content_type="audio/wav",
            duration_ms=int(estimated_duration_sec * 1000),
            sample_rate=self.sample_rate,
            provider="mock",
            model_version="mock-tts-kn-v1",
            voice_gender=voice_gender,
            diagnostic_metadata={
                "latency_ms": latency_ms,
                "character_count": len(sanitized),
                "mock": True,
            },
        )

    async def check_health(self) -> bool:
        return self.healthy
