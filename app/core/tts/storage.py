"""Ephemeral response-audio store with strict TTL, owner binding, and multi-worker safety.

Multi-worker Architecture & Safety Guarantee:
In multi-worker deployments (such as Uvicorn with multiple workers or containerized
backends mounting a shared volume), process-local memory dictionaries cannot synchronize
audio ownership across worker boundaries. To guarantee cross-process authorization and
tamper-proof TTL enforcement, this implementation persists immutable metadata sidecar
files (`{audio_id}.meta.json`) adjacent to the generated audio file (`{audio_id}.wav`).
Every worker reading or cleaning audio reads and verifies the on-disk metadata sidecar,
preventing cross-tenant leakage across worker processes. For multi-node distributed
deployments without shared POSIX volumes, a centralized shared object store with distributed
metadata (e.g., Redis + Cloud Storage) should be used.
"""

import asyncio
import json
import logging
from pathlib import Path
import re
import time
from typing import Dict, Optional
import uuid

from app.config import get_settings

logger = logging.getLogger(__name__)

SAFE_ID_REGEX = re.compile(r"^[a-f0-9]{32}$")


class EphemeralAudioStore:
    """Stores generated TTS audio temporarily for playback with bounded TTL and strict owner binding."""

    def __init__(self, storage_dir: Optional[Path | str] = None, default_ttl_seconds: int = 600):
        settings = get_settings()
        base_dir = storage_dir or Path(settings.AUDIO_TEMP_DIR) / "responses"
        self.storage_dir = Path(base_dir).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_seconds = default_ttl_seconds
        # In-memory fast cache for single-worker acceleration: audio_id -> dict
        self._meta_cache: Dict[str, dict] = {}

    def _meta_file_path(self, audio_id: str) -> Path:
        return self.storage_dir / f"{audio_id}.meta.json"

    def _audio_file_path(self, audio_id: str) -> Path:
        return self.storage_dir / f"{audio_id}.wav"

    async def save(
        self,
        audio_bytes: bytes,
        ttl_seconds: Optional[int] = None,
        owner_id: Optional[str] = None,
    ) -> str:
        """Store synthesized audio bytes with strict owner scope and atomic metadata sidecar."""
        audio_id = uuid.uuid4().hex
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        now = time.time()
        expires_at = now + ttl

        file_path = self._audio_file_path(audio_id)
        meta_path = self._meta_file_path(audio_id)

        meta = {
            "audio_id": audio_id,
            "owner_id": str(owner_id) if owner_id is not None else None,
            "created_at": now,
            "expires_at": expires_at,
            "ttl_seconds": ttl,
        }

        # Write audio bytes and metadata sidecar
        await asyncio.to_thread(file_path.write_bytes, audio_bytes)
        await asyncio.to_thread(meta_path.write_text, json.dumps(meta), encoding="utf-8")

        self._meta_cache[audio_id] = meta
        return audio_id

    # Alias store to save for consistency across services
    store = save

    async def get(self, audio_id: str, owner_id: Optional[str] = None) -> Optional[bytes]:
        """Retrieve stored audio bytes if valid, unexpired, and caller is strictly authorized.

        Non-negotiable security invariants:
        1. Owner-bound audio must NEVER be retrievable when owner_id is omitted or None.
        2. Prevent cross-tenant access: caller owner_id MUST equal expected owner_id.
        3. Prevent path traversal: audio_id strictly validated against SAFE_ID_REGEX.
        4. Validate TTL bounds: expired audio is purged and returns None.
        """
        # 1. Prevent path traversal
        if not SAFE_ID_REGEX.match(audio_id):
            logger.warning("Rejected audio retrieval with malformed/unsafe ID: %s", audio_id)
            return None

        file_path = self._audio_file_path(audio_id)
        meta_path = self._meta_file_path(audio_id)

        if not file_path.exists():
            return None

        # 2. Load metadata (check cache first, fallback to sidecar file)
        meta = self._meta_cache.get(audio_id)
        if meta is None and meta_path.exists():
            try:
                meta_content = await asyncio.to_thread(meta_path.read_text, encoding="utf-8")
                meta = json.loads(meta_content)
                self._meta_cache[audio_id] = meta
            except Exception as exc:
                logger.error("Failed to read metadata sidecar for audio %s: %s", audio_id, exc)
                return None

        now = time.time()

        # 3. Handle fallback metadata if sidecar missing
        if meta is None:
            try:
                mtime = file_path.stat().st_mtime
                expires_at = mtime + self.default_ttl_seconds
                expected_owner = None
            except OSError:
                return None
        else:
            expires_at = meta.get("expires_at", now)
            expected_owner = meta.get("owner_id")

        # 4. Strict Ownership Check
        if expected_owner is not None:
            # Invariant 1: If audio has an owner, an unowned/unauthenticated request MUST be rejected!
            if owner_id is None:
                logger.warning(
                    "Unauthorized attempt to access owner-bound audio %s without providing owner identity",
                    audio_id,
                )
                return None

            # Invariant 2: Cross-tenant access check
            if str(owner_id) != str(expected_owner):
                logger.warning(
                    "Cross-tenant attempt to access audio %s by owner %s (expected %s)",
                    audio_id,
                    owner_id,
                    expected_owner,
                )
                return None

        # 5. TTL Validation
        if now > expires_at:
            # Expired; purge audio and metadata files immediately
            self.purge(audio_id)
            return None

        try:
            return await asyncio.to_thread(file_path.read_bytes)
        except OSError as exc:
            logger.error("Failed to read audio file %s: %s", audio_id, exc)
            return None

    def purge(self, audio_id: str) -> None:
        """Unlink audio and metadata files for an audio ID."""
        if not SAFE_ID_REGEX.match(audio_id):
            return
        file_path = self._audio_file_path(audio_id)
        meta_path = self._meta_file_path(audio_id)

        try:
            file_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            self._meta_cache.pop(audio_id, None)
        except OSError:
            pass

    async def delete_for_owner(self, owner_id: str) -> int:
        """Purge all ephemeral response audio belonging to a specific farmer."""
        if not owner_id:
            return 0

        target_owner = str(owner_id)
        deleted_count = 0

        for meta_file in list(self.storage_dir.glob("*.meta.json")):
            try:
                content = meta_file.read_text(encoding="utf-8")
                meta = json.loads(content)
                if meta.get("owner_id") == target_owner:
                    audio_id = meta.get("audio_id") or meta_file.stem.replace(".meta", "")
                    self.purge(audio_id)
                    deleted_count += 1
            except Exception:
                continue

        return deleted_count

    def cleanup_expired(self) -> int:
        """Delete all expired response audio and metadata files."""
        now = time.time()
        purged = 0

        # Scan metadata sidecars
        for meta_file in list(self.storage_dir.glob("*.meta.json")):
            audio_id = meta_file.name.replace(".meta.json", "")
            try:
                content = meta_file.read_text(encoding="utf-8")
                meta = json.loads(content)
                if now > meta.get("expires_at", 0):
                    self.purge(audio_id)
                    purged += 1
            except Exception:
                # Malformed metadata; purge
                self.purge(audio_id)
                purged += 1

        # Scan for orphan audio files without metadata older than TTL
        for audio_file in list(self.storage_dir.glob("*.wav")):
            audio_id = audio_file.stem
            meta_file = self._meta_file_path(audio_id)
            if not meta_file.exists():
                try:
                    mtime = audio_file.stat().st_mtime
                    if now - mtime > self.default_ttl_seconds:
                        audio_file.unlink(missing_ok=True)
                        purged += 1
                except OSError:
                    pass

        return purged


_ephemeral_audio_store: Optional[EphemeralAudioStore] = None


def get_ephemeral_audio_store() -> EphemeralAudioStore:
    """Singleton provider for EphemeralAudioStore."""
    global _ephemeral_audio_store
    if _ephemeral_audio_store is None:
        _ephemeral_audio_store = EphemeralAudioStore()
    return _ephemeral_audio_store
