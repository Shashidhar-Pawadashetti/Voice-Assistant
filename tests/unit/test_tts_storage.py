"""Unit tests for Ephemeral response-audio storage, TTL expiration, and security checks."""

import asyncio
from pathlib import Path
import pytest

from app.core.tts.storage import EphemeralAudioStore
from tests.fixtures.audio_generator import make_test_wav


@pytest.mark.asyncio
async def test_store_and_retrieve_audio(tmp_path: Path):
    store = EphemeralAudioStore(storage_dir=tmp_path, default_ttl_seconds=60)
    wav_bytes = make_test_wav(duration_seconds=0.5)

    audio_id = await store.save(wav_bytes)
    assert len(audio_id) == 32

    retrieved = await store.get(audio_id)
    assert retrieved == wav_bytes


@pytest.mark.asyncio
async def test_ttl_expiration_purges_file(tmp_path: Path):
    # Store with 0-second TTL
    store = EphemeralAudioStore(storage_dir=tmp_path, default_ttl_seconds=0)
    wav_bytes = make_test_wav(duration_seconds=0.5)

    audio_id = await store.save(wav_bytes, ttl_seconds=0)

    # Allow clock to tick slightly
    await asyncio.sleep(0.05)

    # Retrieval after expiry must return None and remove the file
    retrieved = await store.get(audio_id)
    assert retrieved is None
    assert not (tmp_path / f"{audio_id}.wav").exists()


@pytest.mark.asyncio
async def test_prevents_path_traversal(tmp_path: Path):
    store = EphemeralAudioStore(storage_dir=tmp_path)

    # Malicious IDs
    assert await store.get("../../etc/passwd") is None
    assert await store.get("non-hex-id-with-dashes-1234") is None
    assert await store.get("short") is None


@pytest.mark.asyncio
async def test_cleanup_expired_files(tmp_path: Path):
    store = EphemeralAudioStore(storage_dir=tmp_path, default_ttl_seconds=0)
    wav_bytes = make_test_wav(duration_seconds=0.5)

    aid1 = await store.save(wav_bytes, ttl_seconds=0)
    aid2 = await store.save(wav_bytes, ttl_seconds=0)

    await asyncio.sleep(0.05)

    purged = store.cleanup_expired()
    assert purged == 2
    assert not (tmp_path / f"{aid1}.wav").exists()
    assert not (tmp_path / f"{aid2}.wav").exists()
