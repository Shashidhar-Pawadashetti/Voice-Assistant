"""SQLAlchemy models for asynchronous jobs, worker leases, and idempotency tracking."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID


class Job(Base):
    """Durable job record for voice processing, NLU extraction, and TTS generation."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)  # request_id
    farmer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    turn_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("conversation_turns.id", ondelete="SET NULL"), nullable=True)
    idempotency_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="QUEUED", nullable=False
    )  # QUEUED, PROCESSING, COMPLETED, FAILED_RETRYABLE, FAILED_FINAL, CANCELLED
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    worker_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ASR, NLU, TTS, TURN_ORCHESTRATOR
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("farmer_id", "idempotency_key_hash", name="uq_jobs_farmer_idempotency"),
        Index("ix_jobs_status_created", "status", "created_at"),
    )
