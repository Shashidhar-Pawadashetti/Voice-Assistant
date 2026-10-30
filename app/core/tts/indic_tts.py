"""AI4Bharat Indic-TTS adapter with Kannada support."""

import base64
import logging
import time
from typing import Optional

import httpx

from app.config import get_settings
from app.core.exceptions import TTSModelError, TTSTimeoutError, TTSUnavailableError
from app.core.tts.interface import SpeechSynthesizer
from app.core.tts.sanitizer import sanitize_tts_text
from app.core.tts.schemas import TTSResult


logger = logging.getLogger(__name__)


class IndicTTSAdapter(SpeechSynthesizer):
    """Adapter for AI4Bharat Indic-TTS Kannada speech synthesis service."""

    def __init__(
        self,
        service_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        model_version: Optional[str] = None,
    ):
        settings = get_settings()
        self.service_url = (service_url or settings.TTS_SERVICE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.TTS_TIMEOUT_SECONDS
        self.model_version = model_version or settings.TTS_MODEL_VERSION

    async def synthesize(
        self,
        text: str,
        *,
        language: str = "kn",
        voice_gender: str = "female",
    ) -> TTSResult:
        """Synthesize Kannada text using the Indic-TTS service."""
        sanitized = sanitize_tts_text(text)
        if not sanitized:
            raise TTSModelError("Cannot synthesize empty text")

        start_time = time.perf_counter()
        url = f"{self.service_url}/synthesize"
        payload = {
            "text": sanitized,
            "language": language,
            "gender": voice_gender,
        }
        timeout = httpx.Timeout(self.timeout_seconds, connect=5.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            if response.status_code != 200:
                logger.error("TTS service error: status=%d latency_ms=%d", response.status_code, latency_ms)
                raise TTSModelError(
                    f"Indic-TTS returned status {response.status_code}",
                    details={"status_code": response.status_code, "latency_ms": latency_ms},
                )

            content_type = response.headers.get("content-type", "")

            # If response is direct binary audio
            if "audio/" in content_type or response.content.startswith(b"RIFF"):
                audio_bytes = response.content
                sample_rate = 22050
                duration_ms = max(500, int(len(audio_bytes) / (sample_rate * 2) * 1000))
            else:
                # JSON with base64 payload
                body = response.json()
                raw_audio_b64 = body.get("audio") or body.get("audio_content", "")
                if not raw_audio_b64:
                    raise TTSModelError("TTS response missing audio payload")
                audio_bytes = base64.b64decode(raw_audio_b64)
                sample_rate = body.get("sample_rate", 22050)
                duration_ms = body.get("duration_ms", max(500, int(len(audio_bytes) / (sample_rate * 2) * 1000)))

            logger.info(
                "TTS synthesis completed successfully: provider=indic_tts latency_ms=%d size_bytes=%d",
                latency_ms,
                len(audio_bytes),
            )

            return TTSResult(
                audio_bytes=audio_bytes,
                content_type="audio/wav",
                duration_ms=duration_ms,
                sample_rate=sample_rate,
                provider="indic_tts",
                model_version=self.model_version,
                voice_gender=voice_gender,
                diagnostic_metadata={
                    "latency_ms": latency_ms,
                    "service_url": self.service_url,
                    "chars": len(sanitized),
                },
            )

        except httpx.TimeoutException as exc:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error("TTS request timed out after %d ms", latency_ms)
            raise TTSTimeoutError(
                f"Indic-TTS synthesis timed out after {self.timeout_seconds}s",
                details={"timeout_seconds": self.timeout_seconds, "latency_ms": latency_ms},
            ) from exc

        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error("TTS service unavailable at %s: %s", self.service_url, type(exc).__name__)
            raise TTSUnavailableError(
                f"Indic-TTS service is unavailable at {self.service_url}",
                details={"service_url": self.service_url, "error": str(exc)},
            ) from exc

        except TTSModelError:
            raise

        except Exception as exc:
            logger.error("Unexpected TTS failure: %s", str(exc))
            raise TTSModelError(
                f"Unexpected TTS error: {str(exc)}",
                details={"error": str(exc)},
            ) from exc

    async def check_health(self) -> bool:
        """Check if Indic-TTS service endpoint is reachable."""
        url = f"{self.service_url}/health"
        timeout = httpx.Timeout(3.0, connect=2.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
