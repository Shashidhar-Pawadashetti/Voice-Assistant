"""Argon2id password hashing and validation with timing-attack prevention."""

import logging
from typing import Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

logger = logging.getLogger(__name__)

# Argon2id hasher conforming to OWASP recommendations:
# memory_cost=65536 KiB (64 MiB), time_cost=2 iterations, parallelism=1 thread.
# For high-throughput or resource-constrained nodes, these parameters provide
# memory hardness against GPU cracking while maintaining sub-second user login latency.
_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
)

# Precomputed dummy hash for timing-attack mitigation on non-existent accounts
_DUMMY_HASH = _hasher.hash("krishi_mitra_timing_defense_constant_password")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using Argon2id with a unique per-hash salt."""
    if not plain_password:
        raise ValueError("Password cannot be empty")
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash in constant-time."""
    if not plain_password or not hashed_password:
        return False
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def dummy_verify_password(plain_password: str) -> None:
    """Execute a real Argon2id verification against a fixed dummy hash.

    This ensures that login requests for non-existent farmer accounts take
    approximately the same CPU time as requests for existing accounts, preventing
    timing-based user enumeration.
    """
    try:
        _hasher.verify(_DUMMY_HASH, plain_password or "dummy")
    except Exception:
        pass


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password strength for farmer accounts.

    Rules:
    - Minimum length: 8 characters
    - Maximum length: 128 characters (DoS prevention against memory exhaustion)
    - Cannot be purely whitespace
    """
    if not password:
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    if password.strip() != password:
        return False, "Password must not start or end with whitespace"
    return True, ""
