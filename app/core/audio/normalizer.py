"""Audio normalization to 16 kHz mono PCM WAV using FFmpeg."""

import asyncio
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.core.audio.validator import parse_wav_header
from app.core.exceptions import AudioNormalizationError, AudioValidationError


logger = logging.getLogger(__name__)


def get_ffmpeg_path() -> str:
    """Resolve FFmpeg executable from config, system PATH, or imageio_ffmpeg."""
    settings = get_settings()

    if settings.FFMPEG_BINARY_PATH and os.path.isfile(settings.FFMPEG_BINARY_PATH):
        return settings.FFMPEG_BINARY_PATH

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise AudioNormalizationError(
            "FFmpeg executable not found. Install FFmpeg or configure FFMPEG_BINARY_PATH.",
            details={"error": str(exc)},
        ) from exc


def probe_audio_duration(wav_path: Path) -> Optional[float]:
    """Read duration from WAV file header without spawning external processes."""
    try:
        data = wav_path.read_bytes()
        _channels, _sample_rate, duration = parse_wav_header(data)
        return duration
    except Exception as exc:
        logger.debug("Failed to read WAV duration: %s", exc)
        return None


async def normalize_to_wav_16k(
    input_path: Path,
    output_path: Path,
    *,
    timeout_seconds: float = 15.0,
    max_duration_seconds: float = 60.0,
) -> Path:
    """Normalize input audio to 16 kHz mono 16-bit PCM WAV.

    Arguments are passed directly as an array to prevent shell injection.

    Raises:
        AudioNormalizationError: If FFmpeg fails, times out, or output is invalid.
        AudioValidationError: If decoded audio duration exceeds max_duration_seconds.
    """
    ffmpeg_bin = get_ffmpeg_path()

    args = [
        ffmpeg_bin,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]

    try:
        def _run_ffmpeg() -> subprocess.CompletedProcess[bytes]:
            return subprocess.run(
                args,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )

        try:
            completed: subprocess.CompletedProcess[bytes] = await asyncio.to_thread(_run_ffmpeg)
        except subprocess.TimeoutExpired as exc:
            raise AudioNormalizationError(
                f"Audio normalization timed out after {timeout_seconds}s",
                details={"timeout_seconds": timeout_seconds},
            ) from exc

        if completed.returncode != 0:
            err_msg = completed.stderr.decode("utf-8", errors="replace").strip()
            raise AudioNormalizationError(
                f"FFmpeg failed with exit code {completed.returncode}: {err_msg}",
                details={"returncode": completed.returncode, "stderr": err_msg},
            )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise AudioNormalizationError("Normalized audio output file is missing or zero bytes")

        # Validate normalized audio duration
        duration = probe_audio_duration(output_path)
        if duration is not None and duration > max_duration_seconds:
            raise AudioValidationError(
                f"Audio duration ({duration:.1f}s) exceeds maximum allowed {max_duration_seconds} seconds.",
                details={"duration_seconds": duration, "max_seconds": max_duration_seconds},
            )

        return output_path

    except (AudioNormalizationError, AudioValidationError):
        raise
    except Exception as exc:
        raise AudioNormalizationError(
            f"Unexpected error during audio normalization: {str(exc)}",
            details={"error": str(exc)},
        ) from exc
