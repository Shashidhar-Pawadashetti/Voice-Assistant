"""Unit tests for sliding-window RateLimiter."""

import asyncio
import pytest
from app.core.security.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_sliding_window_rate_limiting():
    limiter = RateLimiter()
    key = "test_key"
    max_attempts = 3
    window = 1  # 1 second window

    # First 3 attempts succeed
    for _ in range(max_attempts):
        is_limited, retry_after = await limiter.is_rate_limited(key, max_attempts, window)
        assert is_limited is False
        assert retry_after == 0

    # 4th attempt is rate limited
    is_limited, retry_after = await limiter.is_rate_limited(key, max_attempts, window)
    assert is_limited is True
    assert retry_after >= 1

    # Wait for window to slide
    await asyncio.sleep(1.1)

    # Next attempt allowed
    is_limited, retry_after = await limiter.is_rate_limited(key, max_attempts, window)
    assert is_limited is False


@pytest.mark.asyncio
async def test_rate_limiter_reset():
    limiter = RateLimiter()
    key = "reset_key"
    await limiter.is_rate_limited(key, 1, 60)
    # Exceeded
    assert (await limiter.is_rate_limited(key, 1, 60))[0] is True

    # Reset
    await limiter.reset(key)
    # Allowed again
    assert (await limiter.is_rate_limited(key, 1, 60))[0] is False
