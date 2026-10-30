"""Mock ASR provider for testing and offline environments."""

import time
from pathlib import Path
from typing import Dict, Optional

from app.core.asr.interface import SpeechRecognizer
from app.core.asr.schemas import ASRResult
from app.core.audio.validator import parse_wav_header


class MockSpeechRecognizer(SpeechRecognizer):
    """Mock implementation returning preconfigured or synthetic transcripts."""

    def __init__(
        self,
        default_transcript: str = "ನನಗೆ ಎರಡು ಎಕರೆ ಜಮೀನಿದೆ, ಧಾರವಾಡ ಜಿಲ್ಲೆ",
        transcript_map: Optional[Dict[str, str]] = None,
        confidence: Optional[float] = 0.95,
        healthy: bool = True,
        simulate_latency_seconds: float = 0.0,
    ):
        self.default_transcript = default_transcript
        self.transcript_map = transcript_map or {}
        self.confidence = confidence
        self.healthy = healthy
        self.simulate_latency_seconds = simulate_latency_seconds

    async def transcribe(self, audio_path: Path, *, language: str = "kn") -> ASRResult:
        start_time = time.perf_counter()

        # Extract duration from audio file if WAV
        duration_ms = 2000
        if audio_path.exists():
            try:
                data = audio_path.read_bytes()
                _ch, _sr, dur = parse_wav_header(data)
                if dur is not None:
                    duration_ms = int(dur * 1000)
            except Exception:
                pass

        filename = audio_path.name
        transcript = self.transcript_map.get(filename, self.default_transcript)
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return ASRResult(
            text=transcript,
            language=language,
            duration_ms=duration_ms,
            confidence=self.confidence,
            provider="mock",
            model_version="mock-kn-v1",
            warnings=[],
            diagnostic_metadata={"latency_ms": latency_ms, "mock": True},
        )

    async def check_health(self) -> bool:
        return self.healthy
