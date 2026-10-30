"""FastAPI authentication dependencies for identity-derived farmer authorization."""

from datetime import datetime, timezone
import logging
from typing import Annotated, Optional
import uuid

from fastapi import Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security.jwt import decode_access_token
from app.database import get_db_session
from app.models.farmer import Farmer

logger = logging.getLogger("krishi.security.auth")


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is offset-aware in UTC for safe comparisons across SQLite and Postgres."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def extract_bearer_token(
    authorization: Annotated[Optional[str], Header(description="Bearer <token>")] = None,
) -> str:
    """Extract and validate Bearer token scheme from Authorization header."""
    if not authorization:
        raise AuthenticationError("Authorization header is required")

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization format: Bearer token scheme required")

    return parts[1]


async def get_current_farmer(
    token: str = Depends(extract_bearer_token),
    db: AsyncSession = Depends(get_db_session),
) -> Farmer:
    """Derive authenticated farmer principal strictly from validated access token.

    Non-negotiable invariants:
    1. Identity is derived strictly from validated JWT claims (sub).
    2. Never trust x-farmer-id, query params, or body claims.
    3. Check account lock status and active lifecycle.
    4. Reject locked, pending deletion, or deleted farmer accounts.
    """
    payload = decode_access_token(token)

    sub = payload.get("sub")
    if not sub:
        raise AuthenticationError("Token payload missing subject claim")

    try:
        farmer_id = uuid.UUID(sub)
    except ValueError:
        raise AuthenticationError("Invalid subject claim: not a valid UUID")

    farmer = await db.get(Farmer, farmer_id)
    if not farmer:
        raise AuthenticationError("Farmer account not found or session revoked")

    now = datetime.now(timezone.utc)

    # Check lockout
    if farmer.account_status == "LOCKED":
        locked_until_utc = _ensure_utc(farmer.locked_until)
        if locked_until_utc and locked_until_utc > now:
            raise AuthenticationError("Account is temporarily locked due to multiple failed login attempts. Please try again later.")
        else:
            # Auto-unlock expired lockout
            farmer.account_status = "ACTIVE"
            farmer.failed_login_attempts = 0
            farmer.locked_until = None
            await db.flush()

    if farmer.account_status in ("DELETED", "DELETION_PENDING"):
        raise AuthenticationError("Account is inactive or pending deletion")

    return farmer


async def get_current_farmer_id(
    current_farmer: Farmer = Depends(get_current_farmer),
) -> uuid.UUID:
    """Convenience dependency returning validated farmer UUID."""
    return current_farmer.id
