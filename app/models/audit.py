"""SQLAlchemy models for non-sensitive audit events and DPDP deletion requests."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID
from app.models.farmer import PortableJSON


class DeletionRequest(Base):
    """Farmer data erasure workflow request."""

    __tablename__ = "deletion_requests"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)  # Nullable after anonymization
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_summary: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)


class AuditEvent(Base):
    """Immutable audit trail for security-relevant lifecycle events.

    Non-negotiable rule (11_SECURITY_AND_PRIVACY.md, Section 9):
    No audio, transcript, prompt, token, phone, or bank details in metadata.
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)  # FARMER, SYSTEM
    actor_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", PortableJSON, nullable=True)

    __table_args__ = (
        Index("ix_audit_events_created_actor", "created_at", "actor_id"),
    )
