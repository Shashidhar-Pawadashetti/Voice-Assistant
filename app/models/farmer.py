"""SQLAlchemy models for farmer identity, profile, and consent records."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, GUID, TimestampMixin


# Portable JSON type: JSONB on PostgreSQL, JSON on SQLite
PortableJSON = JSONB().with_variant(JSON(), "sqlite")


class Farmer(Base, TimestampMixin):
    """Farmer account model.

    Non-negotiable: Human role only (FARMER). No admin role.
    Passwords hashed with Argon2id.
    """

    __tablename__ = "farmers"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    phone_number_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    phone_number_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(10), default="kn", nullable=False)
    account_status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", nullable=False
    )  # ACTIVE, LOCKED, DELETION_PENDING, DELETED
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", back_populates="farmer", uselist=False, cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="farmer", cascade="all, delete-orphan")
    consent_records: Mapped[list["ConsentRecord"]] = relationship("ConsentRecord", back_populates="farmer", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="farmer", cascade="all, delete-orphan")


class FarmerProfile(Base):
    """Farmer agricultural profile."""

    __tablename__ = "farmer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("farmers.id", ondelete="CASCADE"), unique=True, nullable=False)
    profile_data: Mapped[dict] = mapped_column(PortableJSON, default=dict, nullable=False)
    profile_version: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="profile")


class ConsentRecord(Base):
    """Explicit purpose-specific consent record."""

    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("farmers.id", ondelete="CASCADE"), index=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)  # ACCOUNT, CONVERSATION_HISTORY, TRANSCRIPT_RETENTION, VOICE_PROCESSING
    notice_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # GRANTED, WITHDRAWN
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_metadata: Mapped[dict] = mapped_column(PortableJSON, default=dict, nullable=False)

    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="consent_records")
