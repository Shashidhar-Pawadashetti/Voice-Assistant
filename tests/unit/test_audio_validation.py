"""Unit tests for audio upload validation, magic bytes detection, and security constraints."""

import pytest

from app.core.audio.validator import (
    detect_audio_format,
    parse_wav_header,
    validate_audio_file,
)
from app.core.exceptions import AudioValidationError
from tests.fixtures.audio_generator import (
    make_corrupt_wav,
    make_fake_ogg,
    make_fake_webm,
    make_test_wav,
)


def test_validate_valid_wav_passes():
    content = make_test_wav(duration_seconds=1.5, sample_rate=16000, channels=1)
    meta = validate_audio_file(content, max_bytes=100000, max_seconds=10)

    assert meta.format == "wav"
    assert meta.channels == 1
    assert meta.sample_rate == 16000
    assert meta.duration_seconds is not None
    assert 1.4 <= meta.duration_seconds <= 1.6
    assert meta.size_bytes == len(content)


def test_detect_audio_formats():
    wav_bytes = make_test_wav()
    assert detect_audio_format(wav_bytes) == "wav"

    ogg_bytes = make_fake_ogg()
    assert detect_audio_format(ogg_bytes) == "ogg"

    webm_bytes = make_fake_webm()
    assert detect_audio_format(webm_bytes) == "webm"

    mp3_id3 = b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 20
    assert detect_audio_format(mp3_id3) == "mp3"

    non_audio = b"<html><body>Hello</body></html>"
    assert detect_audio_format(non_audio) is None


def test_rejects_empty_and_tiny_audio():
    with pytest.raises(AudioValidationError) as exc:
        validate_audio_file(b"", min_bytes=44)
    assert "too small" in exc.value.message

    with pytest.raises(AudioValidationError):
        validate_audio_file(b"RIFFshort", min_bytes=44)


def test_rejects_oversized_audio():
    content = make_test_wav(duration_seconds=1.0)
    # Set limit below actual size
    with pytest.raises(AudioValidationError) as exc:
        validate_audio_file(content, max_bytes=100)
    assert "exceeds maximum allowed size" in exc.value.message


def test_rejects_excessive_duration():
    content = make_test_wav(duration_seconds=5.0)
    with pytest.raises(AudioValidationError) as exc:
        validate_audio_file(content, max_seconds=2)
    assert "exceeds maximum allowed" in exc.value.message


def test_rejects_non_audio_payloads():
    script_payload = b"#!/bin/bash\necho malicious executable payload\n"
    with pytest.raises(AudioValidationError) as exc:
        validate_audio_file(script_payload)
    assert "Unsupported or invalid audio" in exc.value.message


def test_parse_wav_header_corrupt():
    corrupt = make_corrupt_wav()
    channels, sample_rate, duration = parse_wav_header(corrupt)
    assert duration is None
