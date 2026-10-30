"""Multi-worker shared sliding-window rate limiter with Redis and in-memory fallback."""

import asyncio
from collections import defaultdict
import logging
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("krishi.security.rate_limiter")


class RateLimiter:
    """Multi-worker capable sliding-window rate limiter.

    Uses Redis when REDIS_URL is configured; gracefully falls back to thread-safe
    in-memory storage for single-worker or test environments.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self._redis_client = None
        self._attempts: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._redis_tested = False

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
                logger.info("Shared Redis rate limiter connected successfully")
            except Exception as exc:
                logger.warning("Failed to connect to Redis for shared rate limiting (%s); falling back to in-memory", exc)
                self._redis_client = None
            finally:
                self._redis_tested = True
        return self._redis_client

    async def is_rate_limited(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int,
    ) -> Tuple[bool, int]:
        """Check if an action is rate limited under sliding-window policy.

        Returns:
            (is_limited, retry_after_seconds)
        """
        redis_client = await self._get_redis()
        if redis_client:
            try:
                now = time.time()
                cutoff = now - window_seconds
                r_key = f"krishi:rl:{key}"
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(r_key, 0, cutoff)
                pipe.zcard(r_key)
                pipe.zrange(r_key, 0, 0, withscores=True)
                res = await pipe.execute()
                count = res[1]
                oldest_entries = res[2]

                if count >= max_attempts:
                    if oldest_entries:
                        oldest_ts = float(oldest_entries[0][1])
                        retry_after = max(1, int(window_seconds - (now - oldest_ts)))
                    else:
                        retry_after = window_seconds
                    return True, retry_after

                pipe = redis_client.pipeline()
                pipe.zadd(r_key, {f"{now}:{time.monotonic()}": now})
                pipe.expire(r_key, window_seconds + 5)
                await pipe.execute()
                return False, 0
            except Exception as exc:
                logger.warning("Redis rate limiter error (%s), using in-memory fallback", exc)

        # In-memory fallback
        now = time.monotonic()
        cutoff = now - window_seconds
        async with self._lock:
            attempts = [t for t in self._attempts[key] if t > cutoff]
            self._attempts[key] = attempts
            if len(attempts) >= max_attempts:
                oldest = attempts[0] if attempts else now
                retry_after = max(1, int(window_seconds - (now - oldest)))
                return True, retry_after
            self._attempts[key].append(now)
            return False, 0

    async def reset(self, key: str) -> None:
        """Reset attempts for a specific key (e.g. after successful login)."""
        redis_client = await self._get_redis()
        if redis_client:
            try:
                await redis_client.delete(f"krishi:rl:{key}")
            except Exception:
                pass
        async with self._lock:
            self._attempts.pop(key, None)

    async def clear_all(self) -> None:
        """Clear all rate limiting state (useful for tests)."""
        redis_client = await self._get_redis()
        if redis_client:
            try:
                keys = await redis_client.keys("krishi:rl:*")
                if keys:
                    await redis_client.delete(*keys)
            except Exception:
                pass
        async with self._lock:
            self._attempts.clear()


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Return application rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        from app.config import get_settings

        settings = get_settings()
        _rate_limiter = RateLimiter(redis_url=settings.REDIS_URL)
    return _rate_limiter
