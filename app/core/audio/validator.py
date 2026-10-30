"""Audio input validation: file size, duration, container format, and security."""

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.exceptions import AudioValidationError


SUPPORTED_FORMATS = {"wav", "ogg", "webm", "mp3", "m4a"}


@dataclass(frozen=True)
class AudioMetadata:
    """Validated audio metadata."""

    format: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    channels: Optional[int] = None
    sample_rate: Optional[int] = None


def detect_audio_format(header_bytes: bytes) -> Optional[str]:
    """Inspect magic bytes to determine actual audio container format."""
    if len(header_bytes) < 12:
        return None

    # WAV: "RIFF" .... "WAVE"
    if header_bytes[:4] == b"RIFF" and header_bytes[8:12] == b"WAVE":
        return "wav"

    # OGG: "OggS"
    if header_bytes[:4] == b"OggS":
        return "ogg"

    # WEBM / Matroska: standard EBML header 0x1A 0x45 0xDF 0xA3
    if header_bytes[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"

    # MP3 with ID3v2 tag: "ID3"
    if header_bytes[:3] == b"ID3":
        return "mp3"

    # MP3 sync frame: 0xFF followed by 0xFB, 0xF3, or 0xF2
    if header_bytes[0] == 0xFF and (header_bytes[1] & 0xFE) == 0xF2:
        return "mp3"

    # M4A / MP4 container: "ftyp" signature at offset 4
    if len(header_bytes) >= 8 and header_bytes[4:8] == b"ftyp":
        return "m4a"

    return None


def parse_wav_header(data: bytes) -> tuple[Optional[int], Optional[int], Optional[float]]:
    """Parse a PCM WAV header to extract channels, sample_rate, and duration."""
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return None, None, None

    try:
        offset = 12
        channels: Optional[int] = None
        sample_rate: Optional[int] = None
        byte_rate: Optional[int] = None
        data_size: Optional[int] = None

        while offset + 8 <= len(data):
            chunk_id = data[offset : offset + 4]
            chunk_size = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
            chunk_data_offset = offset + 8

            if chunk_id == b"fmt " and chunk_size >= 16:
                _audio_format, channels, sample_rate, byte_rate = struct.unpack(
                    "<HHII", data[chunk_data_offset : chunk_data_offset + 12]
                )
            elif chunk_id == b"data":
                data_size = chunk_size
                break

            # Move to next chunk (padded to even byte boundary)
            offset += 8 + chunk_size
            if chunk_size % 2 != 0:
                offset += 1

        if byte_rate and byte_rate > 0 and data_size is not None:
            duration = data_size / byte_rate
            return channels, sample_rate, duration

        return channels, sample_rate, None
    except Exception:
        return None, None, None


def validate_audio_file(
    content: bytes,
    *,
    max_bytes: int = 15728640,
    max_seconds: int = 60,
    min_bytes: int = 44,
    min_seconds: float = 0.2,
) -> AudioMetadata:
    """Validate audio bytes against format, size, duration, and safety constraints.

    Raises:
        AudioValidationError: If audio is corrupt, empty, unsupported, oversized, or too long.
    """
    size_bytes = len(content)

    if size_bytes < min_bytes:
        raise AudioValidationError(
            f"Audio file is too small or empty ({size_bytes} bytes). Minimum required is {min_bytes} bytes.",
            details={"size_bytes": size_bytes, "min_bytes": min_bytes},
        )

    if size_bytes > max_bytes:
        raise AudioValidationError(
            f"Audio file exceeds maximum allowed size of {max_bytes} bytes (got {size_bytes} bytes).",
            details={"size_bytes": size_bytes, "max_bytes": max_bytes},
        )

    detected_format = detect_audio_format(content[:64])
    if detected_format is None or detected_format not in SUPPORTED_FORMATS:
        raise AudioValidationError(
            f"Unsupported or invalid audio container format. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}.",
            details={"detected_format": detected_format, "magic_bytes_hex": content[:12].hex()},
        )

    channels, sample_rate, duration_seconds = None, None, None
    if detected_format == "wav":
        channels, sample_rate, duration_seconds = parse_wav_header(content)
        if duration_seconds is not None:
            if duration_seconds < min_seconds:
                raise AudioValidationError(
                    f"Audio duration ({duration_seconds:.2f}s) is too short. Minimum required is {min_seconds}s.",
                    details={"duration_seconds": duration_seconds, "min_seconds": min_seconds},
                )
            if duration_seconds > max_seconds:
                raise AudioValidationError(
                    f"Audio duration ({duration_seconds:.1f}s) exceeds maximum allowed {max_seconds} seconds.",
                    details={"duration_seconds": duration_seconds, "max_seconds": max_seconds},
                )

    return AudioMetadata(
        format=detected_format,
        size_bytes=size_bytes,
        duration_seconds=duration_seconds,
        channels=channels,
        sample_rate=sample_rate,
    )
