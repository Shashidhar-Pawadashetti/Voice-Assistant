"""0005_farmer_security_tokens

Revision ID: 0005_farmer_security_tokens
Revises: 0004_auth_and_security_m5
Create Date: 2026-10-31 05:06:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0005_farmer_security_tokens"
down_revision: Union[str, None] = "0004_auth_and_security_m5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "farmers",
        sa.Column("tokens_revoked_before", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("farmers", "tokens_revoked_before")
