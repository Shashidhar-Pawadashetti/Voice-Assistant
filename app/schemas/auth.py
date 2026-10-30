"""Pydantic schemas for authentication, token management, and farmer identity."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, field_validator

from app.core.security.crypto import normalize_phone_number
from app.core.security.password import validate_password_strength


class RegisterRequest(BaseModel):
    """Farmer account registration payload."""

    phone_number: str = Field(description="Indian mobile phone number (10 digits)")
    password: str = Field(description="Account password (min 8 chars)")
    preferred_language: str = Field(default="kn", description="Preferred language code (default: kn)")
    consent_given: bool = Field(default=True, description="Explicit consent to create account and process data")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        try:
            return normalize_phone_number(v)
        except ValueError as exc:
            raise ValueError(str(exc))

    @field_validator("password")
    @classmethod
    def validate_pwd(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v

    @field_validator("consent_given")
    @classmethod
    def validate_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Farmer consent is required to create an account")
        return v


class LoginRequest(BaseModel):
    """Farmer account login credentials."""

    phone_number: str = Field(description="Registered Indian mobile phone number")
    password: str = Field(description="Account password")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        try:
            return normalize_phone_number(v)
        except ValueError as exc:
            raise ValueError(str(exc))


class TokenResponse(BaseModel):
    """OAuth2-compatible Bearer access and refresh token pair."""

    access_token: str = Field(description="Signed JWT access token")
    refresh_token: str = Field(description="High-entropy refresh token")
    token_type: str = Field(default="bearer", description="Token scheme (bearer)")
    expires_in: int = Field(description="Access token lifespan in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token rotation request."""

    refresh_token: str = Field(description="Active refresh token string")


class LogoutRequest(BaseModel):
    """Logout and session invalidation request."""

    refresh_token: Optional[str] = Field(default=None, description="Optional refresh token to revoke explicitly")


class ChangePasswordRequest(BaseModel):
    """Farmer password change request."""

    old_password: str = Field(description="Current password")
    new_password: str = Field(description="New password (min 8 characters)")

    @field_validator("new_password")
    @classmethod
    def validate_new_pwd(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class FarmerResponse(BaseModel):
    """Authenticated farmer profile representation."""

    id: uuid.UUID
    phone_number_masked: str
    preferred_language: str
    account_status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None


class RegisterResponse(BaseModel):
    """Registration outcome with initial authentication tokens."""

    farmer: FarmerResponse
    tokens: TokenResponse
