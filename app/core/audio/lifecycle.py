"""Ephemeral audio file lifecycle, secure isolation, and guaranteed cleanup."""

import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from app.config import get_settings


logger = logging.getLogger(__name__)


def ensure_audio_temp_dir() -> Path:
    """Ensure the temporary audio directory exists with appropriate permissions."""
    settings = get_settings()
    temp_dir = Path(settings.AUDIO_TEMP_DIR).resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


@asynccontextmanager
async def transient_audio_file(
    content: bytes,
    *,
    suffix: str = ".wav",
) -> AsyncGenerator[Path, None]:
    """Context manager providing a temporary file that is guaranteed to be deleted.

    Deletes the file on success, exception, cancellation, or timeout.
    """
    temp_dir = ensure_audio_temp_dir()
    random_id = uuid.uuid4().hex
    # Enforce safe suffix without directory components
    safe_suffix = suffix if suffix.startswith(".") and "/" not in suffix and "\\" not in suffix else ".wav"
    file_path = temp_dir / f"transient_{random_id}{safe_suffix}"

    try:
        # Write bytes asynchronously in thread pool to not block event loop
        await asyncio.to_thread(file_path.write_bytes, content)
        if os.name != "nt":
            try:
                os.chmod(file_path, 0o600)
            except OSError:
                pass

        yield file_path
    finally:
        # Always remove temporary file
        if file_path.exists():
            try:
                file_path.unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("Failed to remove transient audio file %s: %s", file_path.name, exc)


def cleanup_orphan_audio(
    directory: Path | str | None = None,
    max_age_seconds: int = 600,
) -> int:
    """Scan and delete abandoned audio files older than max_age_seconds.

    Returns the number of files cleaned up.
    """
    if directory is None:
        target_dir = ensure_audio_temp_dir()
    else:
        target_dir = Path(directory)

    if not target_dir.exists():
        return 0

    now = time.time()
    cleaned = 0

    for file_path in target_dir.glob("transient_*"):
        try:
            if not file_path.is_file():
                continue
            file_age = now - file_path.stat().st_mtime
            if file_age >= max_age_seconds:
                file_path.unlink(missing_ok=True)
                cleaned += 1
        except Exception as exc:
            logger.debug("Error checking orphan audio file %s: %s", file_path, exc)

    if cleaned > 0:
        logger.info("Cleaned up %d orphan audio file(s) in %s", cleaned, target_dir)

    return cleaned
