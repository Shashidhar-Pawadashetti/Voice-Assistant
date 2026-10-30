"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-30 22:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Farmers table
    op.create_table(
        "farmers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("phone_number_encrypted", sa.Text(), nullable=False),
        sa.Column("phone_number_hash", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("preferred_language", sa.String(10), server_default="kn", nullable=False),
        sa.Column("account_status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_farmers_phone_number_hash", "farmers", ["phone_number_hash"])

    # 2. Farmer profiles table
    op.create_table(
        "farmer_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farmer_id", sa.String(36), sa.ForeignKey("farmers.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("profile_data", sa.JSON(), nullable=False),
        sa.Column("profile_version", sa.BigInteger(), server_default="1", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Consent records table
    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farmer_id", sa.String(36), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("notice_version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_metadata", sa.JSON(), nullable=False),
    )
    op.create_index("ix_consent_records_farmer_id", "consent_records", ["farmer_id"])

    # 4. Conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farmer_id", sa.String(36), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column("state", sa.String(50), server_default="DISCOVERING_INTENT", nullable=False),
        sa.Column("language", sa.String(10), server_default="kn", nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default="1", nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_conversations_farmer_last_activity", "conversations", ["farmer_id", "last_activity_at"])

    # 5. Conversation turns table
    op.create_table(
        "conversation_turns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("farmer_id", sa.String(36), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turn_number", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("input_mode", sa.String(20), server_default="VOICE", nullable=False),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("assistant_text", sa.Text(), nullable=True),
        sa.Column("asr_model_version", sa.String(100), nullable=True),
        sa.Column("llm_model_version", sa.String(100), nullable=True),
        sa.Column("tts_model_version", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), server_default="COMPLETED", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("conversation_id", "turn_number", name="uq_conversation_turns_conv_turn"),
    )
    op.create_index("ix_conversation_turns_conv_turn", "conversation_turns", ["conversation_id", "turn_number"])

    # 6. Conversation slots table
    op.create_table(
        "conversation_slots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("farmer_id", sa.String(36), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slot_key", sa.String(100), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("canonical_value", sa.JSON(), nullable=False),
        sa.Column("canonical_unit", sa.String(50), nullable=True),
        sa.Column("slot_status", sa.String(30), server_default="PROPOSED", nullable=False),
        sa.Column("provenance", sa.String(30), server_default="USER_STATED", nullable=False),
        sa.Column("source_turn_id", sa.String(36), sa.ForeignKey("conversation_turns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("normalizer_version", sa.String(50), server_default="v0.1.0", nullable=False),
        sa.Column("slot_version", sa.BigInteger(), server_default="1", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("conversation_id", "slot_key", "slot_version", name="uq_conversation_slots_conv_key_ver"),
    )
    op.create_index("ix_conversation_slots_conv_key_ver", "conversation_slots", ["conversation_id", "slot_key", "slot_version"])

    # 7. Schemes table
    op.create_table(
        "schemes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scheme_id", sa.String(100), unique=True, nullable=False),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("assistance_category", sa.String(100), nullable=False),
        sa.Column("government_level", sa.String(50), server_default="NONE", nullable=False),
        sa.Column("active", sa.Boolean(), server_default="1", nullable=False),
    )
    op.create_index("ix_schemes_scheme_id", "schemes", ["scheme_id"])

    # 8. Scheme rule versions table
    op.create_table(
        "scheme_rule_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scheme_id", sa.String(36), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_version", sa.String(50), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("definition_hash", sa.String(64), nullable=False),
        sa.Column("verification_status", sa.String(30), server_default="INCOMPLETE", nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("scheme_id", "rule_version", name="uq_scheme_rule_versions_scheme_ver"),
    )

    # 9. Recommendation runs table
    op.create_table(
        "recommendation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farmer_id", sa.String(36), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_snapshot", sa.JSON(), nullable=False),
        sa.Column("scheme_rule_version_id", sa.String(36), sa.ForeignKey("scheme_rule_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evaluator_version", sa.String(50), server_default="v0.1.0", nullable=False),
        sa.Column("outcome", sa.String(50), nullable=False),
        sa.Column("explanation_trace", sa.JSON(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recommendation_runs_conv_evaluated", "recommendation_runs", ["conversation_id", "evaluated_at"])

    # 10. Jobs table
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farmer_id", sa.String(36), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turn_id", sa.String(36), sa.ForeignKey("conversation_turns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("idempotency_key_hash", sa.String(64), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), server_default="QUEUED", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("worker_type", sa.String(50), nullable=False),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("farmer_id", "idempotency_key_hash", name="uq_jobs_farmer_idempotency"),
    )
    op.create_index("ix_jobs_status_created", "jobs", ["status", "created_at"])

    # 11. Deletion requests table
    op.create_table(
        "deletion_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farmer_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(30), server_default="PENDING", nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=True),
    )

    # 12. Audit events table
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
    )
    op.create_index("ix_audit_events_created_actor", "audit_events", ["created_at", "actor_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("deletion_requests")
    op.drop_table("jobs")
    op.drop_table("recommendation_runs")
    op.drop_table("scheme_rule_versions")
    op.drop_table("schemes")
    op.drop_table("conversation_slots")
    op.drop_table("conversation_turns")
    op.drop_table("conversations")
    op.drop_table("consent_records")
    op.drop_table("farmer_profiles")
    op.drop_table("farmers")
