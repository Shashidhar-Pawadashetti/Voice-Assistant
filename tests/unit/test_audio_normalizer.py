"""Unit tests for audio normalization using FFmpeg."""

from pathlib import Path
import pytest

from app.core.audio.normalizer import (
    get_ffmpeg_path,
    normalize_to_wav_16k,
    probe_audio_duration,
)
from app.core.audio.validator import parse_wav_header
from app.core.exceptions import AudioNormalizationError, AudioValidationError
from tests.fixtures.audio_generator import make_test_wav


def test_ffmpeg_binary_discovered():
    bin_path = get_ffmpeg_path()
    assert bin_path is not None
    assert Path(bin_path).exists()


def test_probe_audio_duration(tmp_path: Path):
    wav_bytes = make_test_wav(duration_seconds=2.0, sample_rate=16000)
    wav_file = tmp_path / "sample.wav"
    wav_file.write_bytes(wav_bytes)

    duration = probe_audio_duration(wav_file)
    assert duration is not None
    assert 1.9 <= duration <= 2.1


@pytest.mark.asyncio
async def test_normalize_valid_wav_to_16k(tmp_path: Path):
    # Create input stereo 44100Hz WAV
    stereo_input = make_test_wav(duration_seconds=1.0, sample_rate=44100, channels=2)
    in_file = tmp_path / "input_stereo.wav"
    in_file.write_bytes(stereo_input)

    out_file = tmp_path / "normalized_16k.wav"

    normalized = await normalize_to_wav_16k(in_file, out_file)
    assert normalized.exists()

    # Verify output properties: mono, 16000Hz PCM
    data = normalized.read_bytes()
    channels, sample_rate, duration = parse_wav_header(data)
    assert channels == 1
    assert sample_rate == 16000
    assert duration is not None
    assert 0.9 <= duration <= 1.1


@pytest.mark.asyncio
async def test_normalize_duration_limit_exceeded(tmp_path: Path):
    long_input = make_test_wav(duration_seconds=3.0, sample_rate=16000)
    in_file = tmp_path / "long.wav"
    in_file.write_bytes(long_input)
    out_file = tmp_path / "out.wav"

    with pytest.raises(AudioValidationError) as exc:
        await normalize_to_wav_16k(in_file, out_file, max_duration_seconds=2.0)
    assert "exceeds maximum allowed" in exc.value.message


@pytest.mark.asyncio
async def test_normalize_nonexistent_file(tmp_path: Path):
    in_file = tmp_path / "missing.wav"
    out_file = tmp_path / "out.wav"

    with pytest.raises(AudioNormalizationError):
        await normalize_to_wav_16k(in_file, out_file)
