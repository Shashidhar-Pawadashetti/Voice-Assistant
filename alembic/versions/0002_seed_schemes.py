"""0002_seed_schemes

Revision ID: 0002_seed_schemes
Revises: 0001_initial_schema
Create Date: 2026-10-30 22:25:00.000000

"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0002_seed_schemes"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEED_SCHEMES = [
    {
        "scheme_id": "PM_KISAN",
        "display_name": "PM-KISAN",
        "classification": "REAL_GOVERNMENT",
        "government_level": "CENTRAL",
        "assistance_category": "INCOME_SUPPORT",
        "verification_status": "INCOMPLETE",
        "rule_version": "0.0.0",
        "definition": {
            "official_source_urls": ["https://pmkisan.gov.in/"],
            "note": "Do not infer entitlement from land ownership alone. Official exclusions and current enrolment/eKYC requirements must be encoded from current primary guidance before a real recommendation is enabled.",
        },
    },
    {
        "scheme_id": "PMFBY",
        "display_name": "Pradhan Mantri Fasal Bima Yojana",
        "classification": "REAL_GOVERNMENT",
        "government_level": "CENTRAL",
        "assistance_category": "CROP_INSURANCE",
        "verification_status": "INCOMPLETE",
        "rule_version": "0.0.0",
        "definition": {
            "official_source_urls": ["https://pmfby.gov.in/"],
            "note": "Requires current season, crop, notified area and applicable state/district notification. Never recommend based only on crop name.",
        },
    },
    {
        "scheme_id": "DEMO_MICRO_IRRIGATION",
        "display_name": "Demo Micro-Irrigation Support",
        "classification": "SYNTHETIC_DEMO",
        "government_level": "NONE",
        "assistance_category": "MICRO_IRRIGATION",
        "verification_status": "VERIFIED_FOR_DEMO_ONLY",
        "rule_version": "1.0.0",
        "definition": {
            "demo_only": True,
            "note": "Synthetic rule path for testing a drip-irrigation request. It is not a government scheme and implies no entitlement.",
        },
    },
    {
        "scheme_id": "DEMO_EQUIPMENT_ASSISTANCE",
        "display_name": "Demo Agricultural Equipment Assistance",
        "classification": "SYNTHETIC_DEMO",
        "government_level": "NONE",
        "assistance_category": "AGRICULTURAL_EQUIPMENT",
        "verification_status": "VERIFIED_FOR_DEMO_ONLY",
        "rule_version": "1.0.0",
        "definition": {
            "demo_only": True,
            "note": "Synthetic decision-rule test path. Do not represent as a real subsidy.",
        },
    },
    {
        "scheme_id": "DEMO_SOIL_IMPROVEMENT",
        "display_name": "Demo Soil Improvement Support",
        "classification": "SYNTHETIC_DEMO",
        "government_level": "NONE",
        "assistance_category": "SOIL_IMPROVEMENT",
        "verification_status": "VERIFIED_FOR_DEMO_ONLY",
        "rule_version": "1.0.0",
        "definition": {
            "demo_only": True,
            "note": "Synthetic test path for additional rule-based recommendation flows.",
        },
    },
]


def upgrade() -> None:
    schemes_table = sa.table(
        "schemes",
        sa.column("id", sa.String(36)),
        sa.column("scheme_id", sa.String(100)),
        sa.column("classification", sa.String(30)),
        sa.column("display_name", sa.String(255)),
        sa.column("assistance_category", sa.String(100)),
        sa.column("government_level", sa.String(50)),
        sa.column("active", sa.Boolean()),
    )

    rule_versions_table = sa.table(
        "scheme_rule_versions",
        sa.column("id", sa.String(36)),
        sa.column("scheme_id", sa.String(36)),
        sa.column("rule_version", sa.String(50)),
        sa.column("definition", sa.JSON()),
        sa.column("definition_hash", sa.String(64)),
        sa.column("verification_status", sa.String(30)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    now = datetime.now(timezone.utc)

    for item in SEED_SCHEMES:
        scheme_uuid = str(uuid.uuid4())
        op.bulk_insert(
            schemes_table,
            [
                {
                    "id": scheme_uuid,
                    "scheme_id": item["scheme_id"],
                    "classification": item["classification"],
                    "display_name": item["display_name"],
                    "assistance_category": item["assistance_category"],
                    "government_level": item["government_level"],
                    "active": True,
                }
            ],
        )

        def_str = json.dumps(item["definition"], sort_keys=True)
        def_hash = hashlib.sha256(def_str.encode("utf-8")).hexdigest()

        op.bulk_insert(
            rule_versions_table,
            [
                {
                    "id": str(uuid.uuid4()),
                    "scheme_id": scheme_uuid,
                    "rule_version": item["rule_version"],
                    "definition": item["definition"],
                    "definition_hash": def_hash,
                    "verification_status": item["verification_status"],
                    "created_at": now,
                }
            ],
        )


def downgrade() -> None:
    op.execute("DELETE FROM scheme_rule_versions")
    op.execute("DELETE FROM schemes")
