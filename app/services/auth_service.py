"""Authentication and Identity Service for Krishi Mitra farmers.

Conforms to Directive M5.1, M5.2, 11_SECURITY_AND_PRIVACY.md.
Invariants:
1. Pure farmer role (FARMER); no admin or unauthenticated privilege elevation.
2. Passwords hashed using Argon2id with per-user salt.
3. Plaintext refresh tokens are never persisted; only SHA-256 hashes.
4. Token family rotation and automatic reuse revocation.
5. Generic login error messages preventing account enumeration.
6. Constant-time dummy verification on non-existent accounts.
7. Brute-force rate limiting and adaptive account lockout.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import logging
from typing import Optional
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AuthenticationError, KrishiMitraError
from app.core.security.crypto import (
    compute_phone_hash,
    encrypt_phone_number,
    normalize_phone_number,
)
from app.core.security.jwt import (
    create_access_token,
    decode_access_token,
    generate_refresh_token_pair,
)
from app.core.security.password import (
    dummy_verify_password,
    hash_password,
    verify_password,
)
from app.core.security.rate_limiter import get_rate_limiter
from app.core.security.revocation import get_token_revocation_store
from app.models.audit import AuditEvent
from app.models.auth import RefreshToken
from app.models.farmer import ConsentRecord, Farmer, FarmerProfile
from app.schemas.auth import (
    ChangePasswordRequest,
    FarmerResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)

logger = logging.getLogger("krishi.service.auth")


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is offset-aware in UTC for safe comparisons across SQLite and Postgres."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def mask_phone_number(normalized_phone: str) -> str:
    """Mask phone number for safe display (e.g., '+91 ******1234')."""
    if len(normalized_phone) >= 10:
        last4 = normalized_phone[-4:]
        prefix = normalized_phone[:3] if normalized_phone.startswith("+91") else ""
        return f"{prefix} ******{last4}"
    return "******"


class AuthService:
    """Manages farmer registration, credentials, token issuance, and rotation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.rate_limiter = get_rate_limiter()
        self.revocation_store = get_token_revocation_store()

    async def register_farmer(
        self,
        request: RegisterRequest,
        client_ip: str = "unknown",
    ) -> RegisterResponse:
        """Register a new farmer account with Argon2id password and initial tokens."""
        # 1. Rate Limiting Check
        rate_key = f"reg_ip_{client_ip}"
        is_limited, retry_after = await self.rate_limiter.is_rate_limited(
            rate_key,
            max_attempts=self.settings.AUTH_RATE_LIMIT_REGISTER_MAX_ATTEMPTS,
            window_seconds=self.settings.AUTH_RATE_LIMIT_REGISTER_WINDOW_SECONDS,
        )
        if is_limited:
            raise KrishiMitraError(
                f"Too many registration attempts. Please retry after {retry_after} seconds.",
                code="RATE_LIMIT_EXCEEDED",
                status_code=429,
                details={"retry_after": retry_after},
            )

        # 2. Check for duplicate account using blind index (separate key support)
        blind_key = self.settings.BLIND_INDEX_KEY or self.settings.APP_SECRET_KEY
        phone_hash = compute_phone_hash(request.phone_number, blind_key)
        stmt = select(Farmer).where(Farmer.phone_number_hash == phone_hash)
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise KrishiMitraError(
                "An account with this phone number already exists.",
                code="ACCOUNT_ALREADY_EXISTS",
                status_code=409,
            )

        # 3. Create Farmer record
        pwd_hash = hash_password(request.password)
        enc_key = self.settings.ENCRYPTION_KEY or self.settings.APP_SECRET_KEY
        enc_phone = encrypt_phone_number(request.phone_number, enc_key)
        now = datetime.now(timezone.utc)
        farmer_id = uuid.uuid4()

        farmer = Farmer(
            id=farmer_id,
            phone_number_encrypted=enc_phone,
            phone_number_hash=phone_hash,
            password_hash=pwd_hash,
            preferred_language=request.preferred_language,
            account_status="ACTIVE",
            last_login_at=now,
        )
        self.db.add(farmer)

        # 4. Create empty FarmerProfile
        profile = FarmerProfile(
            farmer_id=farmer_id,
            profile_data={},
            profile_version=1,
        )
        self.db.add(profile)

        # 5. Record initial Purpose Consent
        consent = ConsentRecord(
            farmer_id=farmer_id,
            purpose="ACCOUNT",
            notice_version="2026.1",
            status="GRANTED",
            evidence_metadata={"registration_ip": client_ip, "timestamp": now.isoformat()},
        )
        self.db.add(consent)

        # 6. Issue initial access token and rotated refresh token
        family_id = uuid.uuid4()
        plaintext_refresh, token_hash = generate_refresh_token_pair()
        refresh_expires = now + timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_row = RefreshToken(
            farmer_id=farmer_id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=refresh_expires,
            is_revoked=False,
        )
        self.db.add(refresh_row)

        access_token = create_access_token(farmer_id)

        # 7. Audit Event
        audit = AuditEvent(
            actor_type="FARMER",
            actor_id=farmer_id,
            event_type="FARMER_REGISTERED",
            resource_type="FARMER",
            resource_id=farmer_id,
            metadata_={"language": request.preferred_language},
        )
        self.db.add(audit)

        await self.db.commit()

        masked = mask_phone_number(request.phone_number)
        return RegisterResponse(
            farmer=FarmerResponse(
                id=farmer_id,
                phone_number_masked=masked,
                preferred_language=farmer.preferred_language,
                account_status=farmer.account_status,
                created_at=farmer.created_at,
                last_login_at=farmer.last_login_at,
            ),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=plaintext_refresh,
                token_type="bearer",
                expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
        )

    async def login_farmer(
        self,
        request: LoginRequest,
        client_ip: str = "unknown",
    ) -> TokenResponse:
        """Authenticate farmer credentials with timing mitigation, lockout, and token issuance."""
        # 1. Rate Limiting Check by IP
        rate_key = f"login_ip_{client_ip}"
        is_limited, retry_after = await self.rate_limiter.is_rate_limited(
            rate_key,
            max_attempts=self.settings.AUTH_RATE_LIMIT_LOGIN_MAX_ATTEMPTS * 2,
            window_seconds=self.settings.AUTH_RATE_LIMIT_LOGIN_WINDOW_SECONDS,
        )
        if is_limited:
            raise KrishiMitraError(
                f"Too many login attempts. Please retry after {retry_after} seconds.",
                code="RATE_LIMIT_EXCEEDED",
                status_code=429,
                details={"retry_after": retry_after},
            )

        blind_key = self.settings.BLIND_INDEX_KEY or self.settings.APP_SECRET_KEY
        phone_hash = compute_phone_hash(request.phone_number, blind_key)
        now = datetime.now(timezone.utc)

        # 2. Look up account by blind index
        stmt = select(Farmer).where(Farmer.phone_number_hash == phone_hash)
        res = await self.db.execute(stmt)
        farmer = res.scalar_one_or_none()

        # 3. Account Non-existence Timing Defense
        if not farmer:
            dummy_verify_password(request.password)
            # Generic error message: never reveal whether account exists
            raise AuthenticationError("Invalid phone number or password")

        # 4. Check Lockout Status
        if farmer.account_status == "LOCKED":
            locked_until_utc = _ensure_utc(farmer.locked_until)
            if locked_until_utc and locked_until_utc > now:
                raise AuthenticationError(
                    "Account is temporarily locked due to multiple failed login attempts. Please try again later."
                )
            else:
                # Expired lockout; reset
                farmer.account_status = "ACTIVE"
                farmer.failed_login_attempts = 0
                farmer.locked_until = None

        if farmer.account_status in ("DELETED", "DELETION_PENDING"):
            # Do not reveal deletion status to unauthenticated callers
            raise AuthenticationError("Invalid phone number or password")

        # 5. Verify Password
        if not verify_password(request.password, farmer.password_hash):
            farmer.failed_login_attempts += 1
            if farmer.failed_login_attempts >= self.settings.AUTH_LOCKOUT_ATTEMPTS:
                farmer.account_status = "LOCKED"
                farmer.locked_until = now + timedelta(minutes=self.settings.AUTH_LOCKOUT_DURATION_MINUTES)
                # Audit lockout
                lock_audit = AuditEvent(
                    actor_type="SYSTEM",
                    actor_id=farmer.id,
                    event_type="ACCOUNT_LOCKED",
                    resource_type="FARMER",
                    resource_id=farmer.id,
                    metadata_={"attempts": farmer.failed_login_attempts},
                )
                self.db.add(lock_audit)

            await self.db.commit()
            raise AuthenticationError("Invalid phone number or password")

        # 6. Login Success: Reset lockout counters
        farmer.failed_login_attempts = 0
        farmer.locked_until = None
        farmer.last_login_at = now

        # Issue new token family on fresh login
        family_id = uuid.uuid4()
        plaintext_refresh, token_hash = generate_refresh_token_pair()
        refresh_expires = now + timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_row = RefreshToken(
            farmer_id=farmer.id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=refresh_expires,
            is_revoked=False,
        )
        self.db.add(refresh_row)

        access_token = create_access_token(farmer.id)

        # Audit login
        login_audit = AuditEvent(
            actor_type="FARMER",
            actor_id=farmer.id,
            event_type="FARMER_LOGGED_IN",
            resource_type="FARMER",
            resource_id=farmer.id,
            metadata_={"ip": client_ip},
        )
        self.db.add(login_audit)

        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=plaintext_refresh,
            token_type="bearer",
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        """Rotate refresh token and issue a new access token with concurrency-safe coordination and reuse detection."""
        token_hash = hashlib.sha256(refresh_token_str.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        # 1. Acquire rotation coordination lock
        lock, was_concurrent = await self.revocation_store.acquire_rotation_lock(token_hash)

        try:
            # If caller was an in-flight concurrent waiter, consume the result of the prior rotation
            if was_concurrent:
                concurrent_res = await self.revocation_store.consume_concurrent_result(token_hash, lock)
                if concurrent_res:
                    access_token, refresh_token = concurrent_res
                    return TokenResponse(
                        access_token=access_token,
                        refresh_token=refresh_token,
                        token_type="bearer",
                        expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    )

            # Normal path: inspect database token record
            stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            res = await self.db.execute(stmt)
            token_record = res.scalar_one_or_none()

            if not token_record:
                raise AuthenticationError("Invalid or expired refresh token")

            # Family Reuse Detection: If this token was already revoked/rotated, reuse has occurred!
            if token_record.is_revoked:
                logger.warning(
                    "Refresh token reuse detected for farmer %s! Revoking token family %s",
                    token_record.farmer_id,
                    token_record.family_id,
                )
                # Revoke entire token family
                revoke_stmt = (
                    update(RefreshToken)
                    .where(RefreshToken.family_id == token_record.family_id)
                    .values(is_revoked=True, revoked_at=now)
                )
                await self.db.execute(revoke_stmt)

                reuse_audit = AuditEvent(
                    actor_type="SYSTEM",
                    actor_id=token_record.farmer_id,
                    event_type="TOKEN_REUSE_DETECTED",
                    resource_type="REFRESH_TOKEN_FAMILY",
                    resource_id=token_record.family_id,
                    metadata_={"family_id": str(token_record.family_id)},
                )
                self.db.add(reuse_audit)
                await self.db.commit()

                raise AuthenticationError("Token reuse detected. All sessions in this family have been terminated.")

            # Check Expiration
            expires_at_utc = _ensure_utc(token_record.expires_at)
            if expires_at_utc and expires_at_utc < now:
                token_record.is_revoked = True
                token_record.revoked_at = now
                await self.db.commit()
                raise AuthenticationError("Refresh token has expired")

            # Successful Rotation: Revoke current token and issue successor under same family
            new_token_id = uuid.uuid4()
            new_plaintext, new_token_hash = generate_refresh_token_pair()
            refresh_expires = now + timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)

            token_record.is_revoked = True
            token_record.revoked_at = now
            token_record.replaced_by_id = new_token_id

            new_refresh_row = RefreshToken(
                id=new_token_id,
                farmer_id=token_record.farmer_id,
                family_id=token_record.family_id,
                token_hash=new_token_hash,
                expires_at=refresh_expires,
                is_revoked=False,
            )
            self.db.add(new_refresh_row)

            access_token = create_access_token(token_record.farmer_id)
            await self.db.commit()

            # Publish rotation output for any concurrent in-flight waiters and release lock
            await self.revocation_store.publish_rotation_result(
                token_hash, lock, access_token, new_plaintext
            )

            return TokenResponse(
                access_token=access_token,
                refresh_token=new_plaintext,
                token_type="bearer",
                expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )
        except Exception:
            await self.revocation_store.release_rotation_lock(token_hash, lock)
            raise

    async def logout_farmer(
        self,
        farmer_id: uuid.UUID,
        refresh_token_str: Optional[str] = None,
        current_access_token: Optional[str] = None,
    ) -> None:
        """Revoke active refresh tokens and immediately denylist the calling access token."""
        now = datetime.now(timezone.utc)

        # 1. Immediate access-token revocation (M7.1)
        if current_access_token:
            try:
                payload = decode_access_token(current_access_token)
                jti = payload.get("jti")
                exp = payload.get("exp")
                remaining_ttl = int(exp - now.timestamp()) if exp else 900
                if jti:
                    await self.revocation_store.revoke_access_token(jti, remaining_ttl)
            except Exception:
                pass

        if refresh_token_str:
            token_hash = hashlib.sha256(refresh_token_str.encode("utf-8")).hexdigest()
            stmt = (
                update(RefreshToken)
                .where(RefreshToken.token_hash == token_hash, RefreshToken.farmer_id == farmer_id)
                .values(is_revoked=True, revoked_at=now)
            )
            await self.db.execute(stmt)
        else:
            # Revoke all active tokens for farmer and invalidate all prior access tokens
            farmer = await self.db.get(Farmer, farmer_id)
            if farmer:
                farmer.tokens_revoked_before = now

            stmt = (
                update(RefreshToken)
                .where(RefreshToken.farmer_id == farmer_id, RefreshToken.is_revoked == False)  # noqa: E712
                .values(is_revoked=True, revoked_at=now)
            )
            await self.db.execute(stmt)

        logout_audit = AuditEvent(
            actor_type="FARMER",
            actor_id=farmer_id,
            event_type="FARMER_LOGGED_OUT",
            resource_type="FARMER",
            resource_id=farmer_id,
        )
        self.db.add(logout_audit)
        await self.db.commit()

    async def change_password(
        self,
        farmer_id: uuid.UUID,
        request: ChangePasswordRequest,
    ) -> None:
        """Change farmer password, revoke all active sessions, and force re-login."""
        farmer = await self.db.get(Farmer, farmer_id)
        if not farmer:
            raise AuthenticationError("Farmer account not found")

        if not verify_password(request.old_password, farmer.password_hash):
            raise AuthenticationError("Current password is incorrect")

        now = datetime.now(timezone.utc)
        farmer.password_hash = hash_password(request.new_password)
        farmer.tokens_revoked_before = now
        farmer.updated_at = now

        # Revoke all active refresh tokens for the farmer
        revoke_stmt = (
            update(RefreshToken)
            .where(RefreshToken.farmer_id == farmer_id, RefreshToken.is_revoked == False)  # noqa: E712
            .values(is_revoked=True, revoked_at=now)
        )
        await self.db.execute(revoke_stmt)

        audit = AuditEvent(
            actor_type="FARMER",
            actor_id=farmer_id,
            event_type="PASSWORD_CHANGED",
            resource_type="FARMER",
            resource_id=farmer_id,
        )
        self.db.add(audit)
        await self.db.commit()
