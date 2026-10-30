"""SQLAlchemy models for scheme catalog, immutable rule versions, and recommendation traces."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID
from app.models.farmer import PortableJSON


class Scheme(Base):
    """Scheme catalog entry."""

    __tablename__ = "schemes"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    scheme_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    classification: Mapped[str] = mapped_column(String(30), nullable=False)  # REAL_GOVERNMENT, SYNTHETIC_DEMO
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name_kn: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_kn: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefit_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefit_description_kn: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_portal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    applicable_geography: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    dataset_version: Mapped[str] = mapped_column(String(50), default="2026.1", nullable=False)
    assistance_category: Mapped[str] = mapped_column(String(100), nullable=False)
    government_level: Mapped[str] = mapped_column(String(50), default="NONE", nullable=False)  # CENTRAL, STATE, NONE
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rule_versions: Mapped[list["SchemeRuleVersion"]] = relationship("SchemeRuleVersion", back_populates="scheme", cascade="all, delete-orphan")


class SchemeRuleVersion(Base):
    """Immutable versioned scheme rule definition with official source provenance."""

    __tablename__ = "scheme_rule_versions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    scheme_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(50), nullable=False)
    definition: Mapped[dict] = mapped_column(PortableJSON, nullable=False)
    definition_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(30), default="INCOMPLETE", nullable=False
    )  # VERIFIED, DRAFT, INCOMPLETE, EXPIRED, VERIFIED_FOR_DEMO_ONLY
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("scheme_id", "rule_version", name="uq_scheme_rule_versions_scheme_ver"),
    )

    scheme: Mapped["Scheme"] = relationship("Scheme", back_populates="rule_versions")


class RecommendationRun(Base):
    """Reproducible, auditable record of deterministic scheme rule evaluation."""

    __tablename__ = "recommendation_runs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    profile_snapshot: Mapped[dict] = mapped_column(PortableJSON, nullable=False)
    scheme_rule_version_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("scheme_rule_versions.id", ondelete="RESTRICT"), nullable=False)
    evaluator_version: Mapped[str] = mapped_column(String(50), default="v0.1.0", nullable=False)
    outcome: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # POTENTIALLY_MATCHED, NEEDS_MORE_INFORMATION, NOT_MATCHED, RULES_NOT_VERIFIED
    explanation_trace: Mapped[dict] = mapped_column(PortableJSON, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_recommendation_runs_conv_evaluated", "conversation_id", "evaluated_at"),
    )
