"""Security, Cryptography, and Authentication Core for Krishi Mitra."""

from app.core.security.password import (
    hash_password,
    verify_password,
    dummy_verify_password,
    validate_password_strength,
)
from app.core.security.crypto import (
    normalize_phone_number,
    compute_phone_hash,
    encrypt_phone_number,
    decrypt_phone_number,
)
from app.core.security.jwt import (
    create_access_token,
    decode_access_token,
    generate_refresh_token_pair,
)
from app.core.security.rate_limiter import RateLimiter, get_rate_limiter
from app.core.security.auth import get_current_farmer, get_current_farmer_id

__all__ = [
    "hash_password",
    "verify_password",
    "dummy_verify_password",
    "validate_password_strength",
    "normalize_phone_number",
    "compute_phone_hash",
    "encrypt_phone_number",
    "decrypt_phone_number",
    "create_access_token",
    "decode_access_token",
    "generate_refresh_token_pair",
    "RateLimiter",
    "get_rate_limiter",
    "get_current_farmer",
    "get_current_farmer_id",
]
