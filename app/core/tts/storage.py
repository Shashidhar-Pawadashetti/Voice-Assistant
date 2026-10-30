"""Ephemeral response-audio store with strict TTL and automatic garbage collection."""

import asyncio
import logging
import re
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from app.config import get_settings


logger = logging.getLogger(__name__)

SAFE_ID_REGEX = re.compile(r"^[a-f0-9]{32}$")


class EphemeralAudioStore:
    """Stores generated TTS audio temporarily for playback with bounded TTL."""

    def __init__(self, storage_dir: Optional[Path | str] = None, default_ttl_seconds: int = 600):
        settings = get_settings()
        base_dir = storage_dir or Path(settings.AUDIO_TEMP_DIR) / "responses"
        self.storage_dir = Path(base_dir).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_seconds = default_ttl_seconds
        # In-memory expiry registry: audio_id -> expiry_timestamp
        self._expiry_registry: Dict[str, float] = {}
        # In-memory ownership registry: audio_id -> owner_id
        self._owner_registry: Dict[str, Optional[str]] = {}

    async def save(
        self,
        audio_bytes: bytes,
        ttl_seconds: Optional[int] = None,
        owner_id: Optional[str] = None,
    ) -> str:
        """Store synthesized audio bytes with optional owner scope and return an ephemeral audio ID."""
        audio_id = uuid.uuid4().hex
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        expires_at = time.time() + ttl

        file_path = self.storage_dir / f"{audio_id}.wav"
        await asyncio.to_thread(file_path.write_bytes, audio_bytes)

        self._expiry_registry[audio_id] = expires_at
        self._owner_registry[audio_id] = owner_id
        return audio_id

    # Alias store to save for consistency across providers
    store = save

    async def get(self, audio_id: str, owner_id: Optional[str] = None) -> Optional[bytes]:
        """Retrieve stored audio bytes if valid, unexpired, and caller is authorized."""
        # Prevent path traversal
        if not SAFE_ID_REGEX.match(audio_id):
            return None

        # Check ownership if owner was bound
        expected_owner = self._owner_registry.get(audio_id)
        if expected_owner is not None and owner_id is not None and expected_owner != owner_id:
            logger.warning("Unauthorized attempt to access response audio %s by owner %s", audio_id, owner_id)
            return None

        file_path = self.storage_dir / f"{audio_id}.wav"
        if not file_path.exists():
            return None

        # Check TTL
        now = time.time()
        expires_at = self._expiry_registry.get(audio_id)

        # Fallback to filesystem mtime if not in memory
        if expires_at is None:
            try:
                mtime = file_path.stat().st_mtime
                expires_at = mtime + self.default_ttl_seconds
            except OSError:
                return None

        if now > expires_at:
            # Expired; purge file
            try:
                file_path.unlink(missing_ok=True)
                self._expiry_registry.pop(audio_id, None)
                self._owner_registry.pop(audio_id, None)
            except OSError:
                pass
            return None

        try:
            return await asyncio.to_thread(file_path.read_bytes)
        except OSError as exc:
            logger.error("Failed to read audio file %s: %s", audio_id, exc)
            return None

    def cleanup_expired(self) -> int:
        """Delete all expired response audio files."""
        now = time.time()
        purged = 0

        # Check memory registry
        expired_ids = [aid for aid, exp in self._expiry_registry.items() if now > exp]
        for aid in expired_ids:
            file_path = self.storage_dir / f"{aid}.wav"
            try:
                file_path.unlink(missing_ok=True)
                purged += 1
            except OSError:
                pass
            self._expiry_registry.pop(aid, None)
            self._owner_registry.pop(aid, None)

        # Also sweep any orphaned files on disk
        for file_path in self.storage_dir.glob("*.wav"):
            try:
                if now - file_path.stat().st_mtime > self.default_ttl_seconds:
                    file_path.unlink(missing_ok=True)
                    purged += 1
            except OSError:
                pass

        if purged > 0:
            logger.info("Purged %d expired response audio files", purged)
        return purged


@lru_cache()
def get_ephemeral_audio_store() -> EphemeralAudioStore:
    """Return singleton instance of EphemeralAudioStore."""
    settings = get_settings()
    return EphemeralAudioStore(default_ttl_seconds=settings.AUDIO_RESPONSE_TTL_SECONDS)
