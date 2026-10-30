"""Access token revocation store and concurrency-safe token rotation cache.

Conforms to Directive M7.1:
1. Concurrency-safe refresh-token rotation with in-flight waiter deduplication.
2. Immediate access-token revocation semantics (JTI denylist with TTL).
3. Redis-backed shared store with robust in-memory fallback.
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger("krishi.security.revocation")


class TokenRevocationStore:
    """Manages JTI-level access token revocation and concurrency-safe rotation across workers."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self._redis_client = None
        self._redis_tested = False
        # In-memory fallbacks: jti -> expires_at (monotonic)
        self._revoked_jtis: Dict[str, float] = {}
        # Concurrency coordination for refresh token rotation
        self._rotation_locks: Dict[str, asyncio.Lock] = {}
        self._rotation_waiters: Dict[str, int] = {}
        self._concurrent_results: Dict[str, Tuple[str, str]] = {}
        self._lock = asyncio.Lock()

    async def _get_redis(self):
        if not self.redis_url:
            return None
        if self._redis_client is None and not self._redis_tested:
            try:
                import redis.asyncio as aioredis

                self._redis_client = aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0,
                )
                await self._redis_client.ping()
                logger.info("Shared Redis token revocation store connected")
            except Exception as exc:
                logger.warning("Failed to connect to Redis for token revocation (%s); using in-memory store", exc)
                self._redis_client = None
            finally:
                self._redis_tested = True
        return self._redis_client

    async def revoke_access_token(self, jti: str, expires_in_seconds: int = 900) -> None:
        """Denylist an access token by JTI until its natural expiration."""
        if not jti:
            return
        ttl = max(1, expires_in_seconds)
        redis_client = await self._get_redis()
        if redis_client:
            try:
                await redis_client.set(f"krishi:revoked_jti:{jti}", "1", ex=ttl)
                return
            except Exception as exc:
                logger.warning("Redis error revoking JTI (%s), using in-memory", exc)

        now = time.monotonic()
        async with self._lock:
            # Clean expired entries
            self._revoked_jtis = {k: v for k, v in self._revoked_jtis.items() if v > now}
            self._revoked_jtis[jti] = now + ttl

    async def is_access_token_revoked(self, jti: str) -> bool:
        """Check whether an access token JTI has been explicitly revoked."""
        if not jti:
            return False
        redis_client = await self._get_redis()
        if redis_client:
            try:
                val = await redis_client.get(f"krishi:revoked_jti:{jti}")
                return val is not None
            except Exception as exc:
                logger.warning("Redis error checking JTI revocation (%s), using in-memory", exc)

        now = time.monotonic()
        async with self._lock:
            exp = self._revoked_jtis.get(jti)
            if exp is None:
                return False
            if exp <= now:
                del self._revoked_jtis[jti]
                return False
            return True

    async def acquire_rotation_lock(self, token_hash: str) -> Tuple[asyncio.Lock, bool]:
        """Acquire in-flight lock for a token rotation.

        Returns:
            (lock, was_concurrently_in_flight)
        """
        async with self._lock:
            if token_hash not in self._rotation_locks:
                self._rotation_locks[token_hash] = asyncio.Lock()
                self._rotation_waiters[token_hash] = 0
            lock = self._rotation_locks[token_hash]
            is_in_flight = lock.locked()
            if is_in_flight:
                self._rotation_waiters[token_hash] += 1

        await lock.acquire()
        return lock, is_in_flight

    async def publish_rotation_result(
        self,
        token_hash: str,
        lock: asyncio.Lock,
        access_token: str,
        refresh_token: str,
    ) -> None:
        """Publish rotation output for concurrent in-flight waiters and release lock."""
        async with self._lock:
            waiters = self._rotation_waiters.get(token_hash, 0)
            if waiters > 0:
                self._concurrent_results[token_hash] = (access_token, refresh_token)
        lock.release()

    async def consume_concurrent_result(
        self,
        token_hash: str,
        lock: asyncio.Lock,
    ) -> Optional[Tuple[str, str]]:
        """Consume rotation output if caller waited on an in-flight rotation, then release lock."""
        result: Optional[Tuple[str, str]] = None
        try:
            async with self._lock:
                result = self._concurrent_results.get(token_hash)
                waiters = self._rotation_waiters.get(token_hash, 1) - 1
                self._rotation_waiters[token_hash] = max(0, waiters)
                if waiters <= 0:
                    self._concurrent_results.pop(token_hash, None)
                    self._rotation_locks.pop(token_hash, None)
                    self._rotation_waiters.pop(token_hash, None)
            return result
        finally:
            lock.release()

    async def release_rotation_lock(self, token_hash: str, lock: asyncio.Lock) -> None:
        """Clean release of rotation lock in error cases."""
        async with self._lock:
            self._concurrent_results.pop(token_hash, None)
            self._rotation_locks.pop(token_hash, None)
            self._rotation_waiters.pop(token_hash, None)
        if lock.locked():
            lock.release()

    async def clear_all(self) -> None:
        """Clear all revocation and rotation state (for tests)."""
        redis_client = await self._get_redis()
        if redis_client:
            try:
                keys = await redis_client.keys("krishi:revoked_jti:*")
                if keys:
                    await redis_client.delete(*keys)
            except Exception:
                pass
        async with self._lock:
            self._revoked_jtis.clear()
            self._concurrent_results.clear()
            self._rotation_locks.clear()
            self._rotation_waiters.clear()


_revocation_store: Optional[TokenRevocationStore] = None


def get_token_revocation_store() -> TokenRevocationStore:
    """Return application token revocation store singleton."""
    global _revocation_store
    if _revocation_store is None:
        from app.config import get_settings

        settings = get_settings()
        _revocation_store = TokenRevocationStore(redis_url=settings.REDIS_URL)
    return _revocation_store
