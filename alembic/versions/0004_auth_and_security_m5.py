"""0004_auth_and_security_m5

Revision ID: 0004_auth_and_security_m5
Revises: 0003_scheme_catalogue_m4
Create Date: 2026-10-31 01:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0004_auth_and_security_m5"
down_revision: Union[str, None] = "0003_scheme_catalogue_m4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add security and lifecycle columns to farmers table
    op.add_column(
        "farmers",
        sa.Column("failed_login_attempts", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "farmers",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "farmers",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Create refresh_tokens table for token rotation and family reuse detection
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farmer_id", sa.String(36), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("family_id", sa.String(36), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("replaced_by_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_refresh_tokens_farmer_id", "refresh_tokens", ["farmer_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_family_revoked", "refresh_tokens", ["family_id", "is_revoked"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_family_revoked", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_farmer_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_column("farmers", "deleted_at")
    op.drop_column("farmers", "locked_until")
    op.drop_column("farmers", "failed_login_attempts")
