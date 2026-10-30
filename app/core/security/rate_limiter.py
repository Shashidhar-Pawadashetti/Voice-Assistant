"""Sliding-window in-memory rate limiter for authentication endpoints."""

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
import time
from typing import Dict, List, Tuple


class RateLimiter:
    """Thread-safe, in-memory sliding-window rate limiter for sensitive routes."""

    def __init__(self):
        # Key -> list of attempt timestamps (monotonic seconds)
        self._attempts: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

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
        now = time.monotonic()
        cutoff = now - window_seconds

        async with self._lock:
            # Filter attempts older than sliding window
            attempts = [t for t in self._attempts[key] if t > cutoff]
            self._attempts[key] = attempts

            if len(attempts) >= max_attempts:
                # Time until earliest attempt exits the window
                oldest = attempts[0] if attempts else now
                retry_after = max(1, int(window_seconds - (now - oldest)))
                return True, retry_after

            # Record this attempt
            self._attempts[key].append(now)
            return False, 0

    async def reset(self, key: str) -> None:
        """Reset attempts for a specific key (e.g. after successful login)."""
        async with self._lock:
            self._attempts.pop(key, None)

    async def clear_all(self) -> None:
        """Clear all rate limiting state (useful for tests)."""
        async with self._lock:
            self._attempts.clear()


_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Return application rate limiter singleton."""
    return _rate_limiter
