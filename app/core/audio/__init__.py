"""Audio processing, validation, normalization, and lifecycle management."""

from app.core.audio.validator import AudioMetadata, validate_audio_file, detect_audio_format
from app.core.audio.normalizer import normalize_to_wav_16k, get_ffmpeg_path, probe_audio_duration
from app.core.audio.lifecycle import transient_audio_file, cleanup_orphan_audio

__all__ = [
    "AudioMetadata",
    "validate_audio_file",
    "detect_audio_format",
    "normalize_to_wav_16k",
    "get_ffmpeg_path",
    "probe_audio_duration",
    "transient_audio_file",
    "cleanup_orphan_audio",
]
