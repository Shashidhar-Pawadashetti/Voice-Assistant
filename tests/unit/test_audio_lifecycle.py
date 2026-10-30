"""Unit tests for transient audio file lifecycle, guaranteed cleanup, and orphan scanning."""

import asyncio
from pathlib import Path
import pytest

from app.core.audio.lifecycle import cleanup_orphan_audio, transient_audio_file
from tests.fixtures.audio_generator import make_test_wav


@pytest.mark.asyncio
async def test_transient_audio_file_unlinks_on_success():
    content = make_test_wav(duration_seconds=0.5)
    captured_path: Path | None = None

    async with transient_audio_file(content, suffix=".wav") as temp_path:
        captured_path = temp_path
        assert captured_path.exists()
        assert captured_path.stat().st_size == len(content)

    # After context exit, file must be strictly deleted
    assert not captured_path.exists()


@pytest.mark.asyncio
async def test_transient_audio_file_unlinks_on_exception():
    content = make_test_wav(duration_seconds=0.5)
    captured_path: Path | None = None

    with pytest.raises(RuntimeError):
        async with transient_audio_file(content, suffix=".wav") as temp_path:
            captured_path = temp_path
            assert captured_path.exists()
            raise RuntimeError("Intentional error during processing")

    # File must be deleted even when exception was raised
    assert captured_path is not None
    assert not captured_path.exists()


@pytest.mark.asyncio
async def test_cleanup_orphan_audio(tmp_path: Path):
    # Create artificial old and fresh transient files
    old_file = tmp_path / "transient_old_test.wav"
    old_file.write_bytes(b"dummy")

    fresh_file = tmp_path / "transient_fresh_test.wav"
    fresh_file.write_bytes(b"dummy")

    # Non-transient file that should not be touched
    unrelated_file = tmp_path / "important_model_file.bin"
    unrelated_file.write_bytes(b"preserve")

    # Cleanup with max_age_seconds=0 deletes both old and fresh transient files
    cleaned = cleanup_orphan_audio(directory=tmp_path, max_age_seconds=0)
    assert cleaned == 2
    assert not old_file.exists()
    assert not fresh_file.exists()
    assert unrelated_file.exists()
