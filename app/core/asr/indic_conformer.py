"""AI4Bharat IndicConformer ASR adapter with Kannada support."""

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from app.config import get_settings
from app.core.asr.interface import SpeechRecognizer
from app.core.asr.schemas import ASRResult
from app.core.audio.validator import parse_wav_header
from app.core.exceptions import ASRModelError, ASRTimeoutError, ASRUnavailableError


logger = logging.getLogger(__name__)


class IndicConformerAdapter(SpeechRecognizer):
    """Adapter for AI4Bharat IndicConformer Kannada speech recognition service."""

    def __init__(
        self,
        service_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        model_version: Optional[str] = None,
    ):
        settings = get_settings()
        self.service_url = (service_url or settings.ASR_SERVICE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.ASR_TIMEOUT_SECONDS
        self.model_version = model_version or settings.ASR_MODEL_VERSION

    async def transcribe(self, audio_path: Path, *, language: str = "kn") -> ASRResult:
        """Send normalized audio to the IndicConformer service for Kannada transcription."""
        if not audio_path.exists():
            raise ASRModelError(f"Audio file not found: {audio_path.name}")

        start_time = time.perf_counter()

        # Extract duration from audio header if available
        duration_ms = 0
        try:
            data = audio_path.read_bytes()
            _ch, _sr, dur = parse_wav_header(data)
            if dur is not None:
                duration_ms = int(dur * 1000)
        except Exception:
            pass

        url = f"{self.service_url}/transcribe"
        timeout = httpx.Timeout(self.timeout_seconds, connect=5.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                with open(audio_path, "rb") as f:
                    files = {"file": (audio_path.name, f, "audio/wav")}
                    data_payload = {"language": language}

                    response = await client.post(url, files=files, data=data_payload)

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            if response.status_code != 200:
                logger.error(
                    "ASR service error: status=%d latency_ms=%d",
                    response.status_code,
                    latency_ms,
                )
                raise ASRModelError(
                    f"IndicConformer ASR returned status {response.status_code}",
                    details={"status_code": response.status_code, "latency_ms": latency_ms},
                )

            body = response.json()
            transcript = body.get("transcript") or body.get("text", "")
            detected_lang = body.get("language", language)
            resp_dur = body.get("duration_ms")
            if resp_dur is not None and isinstance(resp_dur, (int, float)):
                duration_ms = int(resp_dur)

            # Never fabricate confidence; only accept documented numeric float
            raw_confidence = body.get("confidence")
            confidence = float(raw_confidence) if isinstance(raw_confidence, (int, float)) else None
            warnings = body.get("warnings", [])

            logger.info(
                "ASR transcription completed successfully: provider=indic_conformer latency_ms=%d duration_ms=%d",
                latency_ms,
                duration_ms,
            )

            return ASRResult(
                text=transcript.strip(),
                language=detected_lang,
                duration_ms=duration_ms,
                confidence=confidence,
                provider="indic_conformer",
                model_version=self.model_version,
                warnings=warnings,
                diagnostic_metadata={
                    "latency_ms": latency_ms,
                    "service_url": self.service_url,
                },
            )

        except httpx.TimeoutException as exc:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error("ASR request timed out after %d ms", latency_ms)
            raise ASRTimeoutError(
                f"IndicConformer transcription timed out after {self.timeout_seconds}s",
                details={"timeout_seconds": self.timeout_seconds, "latency_ms": latency_ms},
            ) from exc

        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error("ASR service unavailable at %s: %s", self.service_url, type(exc).__name__)
            raise ASRUnavailableError(
                f"IndicConformer ASR service is unavailable at {self.service_url}",
                details={"service_url": self.service_url, "error": str(exc)},
            ) from exc

        except ASRModelError:
            raise

        except Exception as exc:
            logger.error("Unexpected ASR failure: %s", str(exc))
            raise ASRModelError(
                f"Unexpected ASR error: {str(exc)}",
                details={"error": str(exc)},
            ) from exc

    async def check_health(self) -> bool:
        """Check if IndicConformer service endpoint is reachable and responsive."""
        url = f"{self.service_url}/health"
        timeout = httpx.Timeout(3.0, connect=2.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
