"""Unit tests for EphemeralAudioStore owner binding, multi-worker metadata sidecars, and TTL."""

import asyncio
from pathlib import Path
import time
import pytest
from app.core.tts.storage import EphemeralAudioStore


@pytest.mark.asyncio
async def test_owner_bound_audio_retrieval(tmp_path: Path):
    store = EphemeralAudioStore(storage_dir=tmp_path, default_ttl_seconds=60)
    audio_data = b"RIFF....WAVEfmt test audio"
    owner_a = "farmer-uuid-aaaa-1111"
    owner_b = "farmer-uuid-bbbb-2222"

    # Save audio bound to owner_a
    audio_id = await store.save(audio_data, owner_id=owner_a)

    # 1. Authorized owner retrieves successfully
    retrieved = await store.get(audio_id, owner_id=owner_a)
    assert retrieved == audio_data

    # 2. Critical Invariant: Retrieving owner-bound audio WITHOUT owner_id returns None
    unauthenticated_retrieval = await store.get(audio_id, owner_id=None)
    assert unauthenticated_retrieval is None

    # 3. Cross-tenant attempt: Owner B attempting to get Owner A's audio returns None
    cross_tenant_retrieval = await store.get(audio_id, owner_id=owner_b)
    assert cross_tenant_retrieval is None


@pytest.mark.asyncio
async def test_multi_worker_metadata_sidecar_persistence(tmp_path: Path):
    store1 = EphemeralAudioStore(storage_dir=tmp_path, default_ttl_seconds=60)
    owner = "farmer-uuid-multiworker"
    audio_data = b"fake audio payload"

    # Worker 1 saves audio
    audio_id = await store1.save(audio_data, owner_id=owner)

    # Verify sidecar file exists on disk
    meta_path = tmp_path / f"{audio_id}.meta.json"
    audio_path = tmp_path / f"{audio_id}.wav"
    assert meta_path.exists()
    assert audio_path.exists()

    # Worker 2 (separate store instance with clean memory cache) accesses audio
    store2 = EphemeralAudioStore(storage_dir=tmp_path, default_ttl_seconds=60)
    retrieved = await store2.get(audio_id, owner_id=owner)
    assert retrieved == audio_data

    # Worker 2 denies unowned access
    assert await store2.get(audio_id, owner_id=None) is None


@pytest.mark.asyncio
async def test_ttl_expiration_and_sidecar_purging(tmp_path: Path):
    # Store with 1 second TTL
    store = EphemeralAudioStore(storage_dir=tmp_path, default_ttl_seconds=1)
    owner = "farmer-ttl-owner"
    audio_id = await store.save(b"short lived audio", ttl_seconds=1, owner_id=owner)

    meta_path = tmp_path / f"{audio_id}.meta.json"
    audio_path = tmp_path / f"{audio_id}.wav"
    assert audio_path.exists()
    assert meta_path.exists()

    # Wait for TTL to elapse
    await asyncio.sleep(1.1)

    # Access attempts purge expired files and return None
    assert await store.get(audio_id, owner_id=owner) is None
    assert not audio_path.exists()
    assert not meta_path.exists()


@pytest.mark.asyncio
async def test_delete_for_owner_purges_all_farmer_audio(tmp_path: Path):
    store = EphemeralAudioStore(storage_dir=tmp_path, default_ttl_seconds=60)
    target_farmer = "farmer-to-delete-123"
    other_farmer = "farmer-to-keep-456"

    id1 = await store.save(b"audio1", owner_id=target_farmer)
    id2 = await store.save(b"audio2", owner_id=target_farmer)
    id3 = await store.save(b"audio3", owner_id=other_farmer)

    # Delete all audio for target_farmer
    deleted = await store.delete_for_owner(target_farmer)
    assert deleted == 2

    # Target farmer audio gone
    assert await store.get(id1, owner_id=target_farmer) is None
    assert await store.get(id2, owner_id=target_farmer) is None

    # Other farmer audio untouched
    assert await store.get(id3, owner_id=other_farmer) == b"audio3"


@pytest.mark.asyncio
async def test_path_traversal_defense(tmp_path: Path):
    store = EphemeralAudioStore(storage_dir=tmp_path)
    # Directory traversal payloads
    assert await store.get("../etc/passwd") is None
    assert await store.get("..\\windows\\system32") is None
    assert await store.get("non-hex-id") is None
    assert await store.get("12345") is None
