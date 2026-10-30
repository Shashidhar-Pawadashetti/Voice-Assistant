"""JWT access token and cryptographic refresh token generation and verification."""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any, Dict, Optional
import uuid
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.config import get_settings
from app.core.exceptions import AuthenticationError


def create_access_token(
    farmer_id: uuid.UUID,
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None,
    algorithm: Optional[str] = None,
) -> str:
    """Generate a signed, short-lived JWT access token for an authenticated farmer."""
    settings = get_settings()
    secret = secret_key or getattr(settings, "JWT_SECRET_KEY", None) or settings.APP_SECRET_KEY
    alg = algorithm or getattr(settings, "JWT_ALGORITHM", "HS256")
    expire_minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 15)

    now = datetime.now(timezone.utc)
    expires_at = now + (expires_delta or timedelta(minutes=expire_minutes))

    payload: Dict[str, Any] = {
        "sub": str(farmer_id),
        "type": "access",
        "role": "FARMER",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": uuid.uuid4().hex,
    }

    return jwt.encode(payload, secret, algorithm=alg)


def decode_access_token(
    token: str,
    secret_key: Optional[str] = None,
    algorithm: Optional[str] = None,
) -> Dict[str, Any]:
    """Decode, verify signature, and validate claims of a JWT access token."""
    settings = get_settings()
    secret = secret_key or getattr(settings, "JWT_SECRET_KEY", None) or settings.APP_SECRET_KEY
    alg = algorithm or getattr(settings, "JWT_ALGORITHM", "HS256")

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[alg],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except ExpiredSignatureError:
        raise AuthenticationError("Access token has expired")
    except InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid access token: {exc}")

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type: expected access token")

    if payload.get("role") != "FARMER":
        raise AuthenticationError("Invalid token role")

    return payload


def generate_refresh_token_pair() -> tuple[str, str]:
    """Generate a high-entropy refresh token and its SHA-256 hash for database storage.

    Returns:
        (plaintext_refresh_token, sha256_hash_for_db)
    """
    plaintext_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(plaintext_token.encode("utf-8")).hexdigest()
    return plaintext_token, token_hash
