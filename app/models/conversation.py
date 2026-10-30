"""SQLAlchemy models for conversations, turns, and structured slot values."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin
from app.models.farmer import PortableJSON


class Conversation(Base, TimestampMixin):
    """Dialogue conversation session."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, PAUSED, COMPLETED, DELETED
    state: Mapped[str] = mapped_column(String(50), default="DISCOVERING_INTENT", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="kn", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_conversations_farmer_last_activity", "farmer_id", "last_activity_at"),
    )

    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="conversations")
    turns: Mapped[list["ConversationTurn"]] = relationship("ConversationTurn", back_populates="conversation", cascade="all, delete-orphan")
    slots: Mapped[list["ConversationSlot"]] = relationship("ConversationSlot", back_populates="conversation", cascade="all, delete-orphan")


class ConversationTurn(Base):
    """Individual turn within a conversation."""

    __tablename__ = "conversation_turns"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    farmer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    turn_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # FARMER, ASSISTANT, SYSTEM_EVENT
    input_mode: Mapped[str] = mapped_column(String(20), default="VOICE", nullable=False)  # VOICE, TEXT, NONE
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    assistant_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    asr_model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tts_model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("conversation_id", "turn_number", name="uq_conversation_turns_conv_turn"),
        Index("ix_conversation_turns_conv_turn", "conversation_id", "turn_number"),
    )

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="turns")


class ConversationSlot(Base):
    """Extracted and validated agricultural slot value with provenance."""

    __tablename__ = "conversation_slots"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    farmer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    slot_key: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_value: Mapped[dict] = mapped_column(PortableJSON, nullable=False)
    canonical_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    slot_status: Mapped[str] = mapped_column(String(30), default="PROPOSED", nullable=False)  # MISSING, PROPOSED, CONFIRMED, CONFLICTED, UNKNOWN, NOT_APPLICABLE
    provenance: Mapped[str] = mapped_column(String(30), default="USER_STATED", nullable=False)  # USER_STATED, USER_CONFIRMED, OFFICIAL_SOURCE, SYSTEM_DERIVED
    source_turn_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("conversation_turns.id", ondelete="SET NULL"), nullable=True)
    normalizer_version: Mapped[str] = mapped_column(String(50), default="v0.1.0", nullable=False)
    slot_version: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("conversation_id", "slot_key", "slot_version", name="uq_conversation_slots_conv_key_ver"),
        Index("ix_conversation_slots_conv_key_ver", "conversation_id", "slot_key", "slot_version"),
    )

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="slots")
