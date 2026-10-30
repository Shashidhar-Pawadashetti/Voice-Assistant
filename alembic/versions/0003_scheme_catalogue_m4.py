"""0003_scheme_catalogue_m4

Revision ID: 0003_scheme_catalogue_m4
Revises: 0002_seed_schemes
Create Date: 2026-10-31 00:15:00.000000

"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0003_scheme_catalogue_m4"
down_revision: Union[str, None] = "0002_seed_schemes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEME_UPDATES = [
    {
        "scheme_id": "PM_KISAN",
        "display_name_kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ (ಪಿಎಂ-ಕಿಸಾನ್)",
        "description": "Central Sector scheme to provide income support to all landholding eligible farmer families having cultivable land in their names.",
        "description_kn": "ತಮ್ಮ ಹೆಸರಿನಲ್ಲಿ ಕೃಷಿ ಯೋಗ್ಯ ಜಮೀನು ಹೊಂದಿರುವ ಅರ್ಹ ರೈತ ಕುಟುಂಬಗಳಿಗೆ ಆದಾಯ ಬೆಂಬಲ ನೀಡುವ ಕೇಂದ್ರ ಸರ್ಕಾರದ ಯೋಜನೆ.",
        "benefit_description": "Income support of Rs. 6,000 per year in three equal 4-monthly instalments directly into Aadhaar-seeded bank accounts.",
        "benefit_description_kn": "ಆಧಾರ್ ಜೋಡಿಸಲಾದ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ನೇರವಾಗಿ 4 ತಿಂಗಳಿಗೊಮ್ಮೆ ತಲಾ ₹2,000 ರಂತೆ ವರ್ಷಕ್ಕೆ ₹6,000 ಆದಾಯ ನೆರವು.",
        "application_portal": "https://pmkisan.gov.in/",
        "applicable_geography": {"state": "Karnataka", "country": "India"},
        "dataset_version": "2026.1",
        "rule_version": "1.0.0",
        "verification_status": "VERIFIED",
        "definition": {
            "required_slots": ["land_ownership", "district"],
            "eligibility_conditions": [
                {
                    "slot_key": "land_ownership",
                    "operator": "IN",
                    "expected_value": ["OWNER", "CO_OWNER"],
                    "required_provenance": "OFFICIALLY_VERIFIED",
                    "evidence_reference": "PM-KISAN Operational Guidelines Clause 2(b)",
                }
            ],
            "exclusions": [
                {"slot_key": "land_ownership", "operator": "EQ", "expected_value": "INSTITUTIONAL", "is_exclusion": True},
                {"slot_key": "income_tax_payer", "operator": "EQ", "expected_value": True, "is_exclusion": True},
                {"slot_key": "govt_employee", "operator": "EQ", "expected_value": True, "is_exclusion": True},
                {"slot_key": "constitutional_post_holder", "operator": "EQ", "expected_value": True, "is_exclusion": True},
            ],
            "official_source_urls": ["https://pmkisan.gov.in/"],
            "official_verification_required": True,
        },
    },
    {
        "scheme_id": "PMFBY",
        "display_name_kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ (ಪಿಎಂಎಫ್‌ಬಿವೈ)",
        "description": "Comprehensive crop insurance scheme providing financial support to farmers suffering crop loss or damage due to unforeseen natural events.",
        "description_kn": "ನೈಸರ್ಗಿಕ ವಿಕೋಪಗಳಿಂದ ಉಂಟಾಗುವ ಬೆಳೆ ನಷ್ಟಕ್ಕೆ ಆರ್ಥಿಕ ಭದ್ರತೆ ನೀಡುವ ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ.",
        "benefit_description": "Insurance coverage and financial support for notified crops against non-preventable natural risks from pre-sowing to post-harvest.",
        "benefit_description_kn": "ಅಧಿಸೂಚಿತ ಬೆಳೆಗಳಿಗೆ ನೈಸರ್ಗಿಕ ವಿಕೋಪಗಳಿಂದ ಆಗುವ ಹಾನಿಗೆ ವಿಮಾ ರಕ್ಷಣೆ ಮತ್ತು ಪರಿಹಾರ ನೆರವು.",
        "application_portal": "https://pmfby.gov.in/",
        "applicable_geography": {"state": "Karnataka", "country": "India"},
        "dataset_version": "2026.1",
        "rule_version": "0.0.0",
        "verification_status": "INCOMPLETE",
        "definition": {
            "required_slots": ["district", "crop", "season"],
            "eligibility_conditions": [
                {"slot_key": "district", "operator": "EXISTS", "expected_value": True},
                {"slot_key": "crop", "operator": "EXISTS", "expected_value": True},
                {"slot_key": "season", "operator": "EXISTS", "expected_value": True},
            ],
            "official_source_urls": ["https://pmfby.gov.in/"],
            "official_verification_required": True,
            "note": "Requires current season, crop, notified area and applicable state/district notification. Kept INCOMPLETE to prevent invented rule claims.",
        },
    },
    {
        "scheme_id": "DEMO_MICRO_IRRIGATION",
        "display_name_kn": "ಮಾದರಿ ಹನಿ ನೀರಾವರಿ ಸಹಾಯಧನ (ಡೆಮೊ ಮಾತ್ರ)",
        "description": "Synthetic demonstration decision path for testing drip and sprinkler irrigation recommendation flows.",
        "description_kn": "ಹನಿ ಮತ್ತು ತುಂತುರು ನೀರಾವರಿ ಸಲಹೆ ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ (ಡೆಮೊ) ಯೋಜನೆ.",
        "benefit_description": "Synthetic subsidy test fixture for testing micro-irrigation decision rules. Confers NO real entitlement.",
        "benefit_description_kn": "ತಾಂತ್ರಿಕ ಪ್ರಾತ್ಯಕ್ಷಿಕೆಗಾಗಿ ರೂಪಿಸಲಾದ ಮಾದರಿ ಸಹಾಯಧನ ಪರೀಕ್ಷೆ. ಯಾವುದೇ ನೈಜ ಸರ್ಕಾರಿ ಸವಲತ್ತು ಇರುವುದಿಲ್ಲ.",
        "application_portal": "https://example.gov.in/demo-micro-irrigation",
        "applicable_geography": {"state": "Karnataka"},
        "dataset_version": "2026.1",
        "rule_version": "1.0.0",
        "verification_status": "VERIFIED_FOR_DEMO_ONLY",
        "definition": {
            "demo_only": True,
            "required_slots": ["district", "land_area", "irrigation"],
            "eligibility_conditions": [
                {"slot_key": "district", "operator": "EXISTS", "expected_value": True},
                {"slot_key": "land_area", "operator": "GT", "expected_value": 0.0, "unit": "acres"},
                {"slot_key": "irrigation", "operator": "IN", "expected_value": ["DRIP", "SPRINKLER", "BOREWELL", "CANAL", "OPEN_WELL", "RAIN_FED", "OTHER"]},
            ],
        },
    },
    {
        "scheme_id": "DEMO_EQUIPMENT_ASSISTANCE",
        "display_name_kn": "ಮಾದರಿ ಕೃಷಿ ಯಂತ್ರೋಪಕರಣ ಸಹಾಯಧನ (ಡೆಮೊ ಮಾತ್ರ)",
        "description": "Synthetic demonstration decision path for testing equipment subsidy decision rules.",
        "description_kn": "ಕೃಷಿ ಯಂತ್ರೋಪಕರಣಗಳ ಸಹಾಯಧನ ನಿಯಮಗಳನ್ನು ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ (ಡೆಮೊ) ಯೋಜನೆ.",
        "benefit_description": "Synthetic subsidy test fixture for farm machinery decision rules. Confers NO real entitlement.",
        "benefit_description_kn": "ಯಂತ್ರೋಪಕರಣಗಳ ಸಲಹೆ ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ ನೆರವು. ನೈಜ ಮಂಜೂರಾತಿ ಇರುವುದಿಲ್ಲ.",
        "application_portal": "https://example.gov.in/demo-equipment",
        "applicable_geography": {"state": "Karnataka"},
        "dataset_version": "2026.1",
        "rule_version": "1.0.0",
        "verification_status": "VERIFIED_FOR_DEMO_ONLY",
        "definition": {
            "demo_only": True,
            "required_slots": ["district", "equipment"],
            "eligibility_conditions": [
                {"slot_key": "district", "operator": "EXISTS", "expected_value": True},
                {"slot_key": "equipment", "operator": "EXISTS", "expected_value": True},
            ],
        },
    },
    {
        "scheme_id": "DEMO_SOIL_IMPROVEMENT",
        "display_name_kn": "ಮಾದರಿ ಮಣ್ಣು ಸುಧಾರಣೆ ಸಹಾಯಧನ (ಡೆಮೊ ಮಾತ್ರ)",
        "description": "Synthetic demonstration decision path for testing soil health and fertilizer subsidy recommendation paths.",
        "description_kn": "ಮಣ್ಣು ಸುಧಾರಣೆ ಮತ್ತು ಪೋಷಕಾಂಶಗಳ ಸಹಾಯಧನ ನಿಯಮಗಳನ್ನು ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ (ಡೆಮೊ) ಯೋಜನೆ.",
        "benefit_description": "Synthetic subsidy test fixture for soil improvement decision rules. Confers NO real entitlement.",
        "benefit_description_kn": "ಮಣ್ಣು ಪರೀಕ್ಷೆ ಮತ್ತು ಸುಧಾರಣೆ ಸಲಹೆ ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ ನೆರವು. ನೈಜ ಮಂಜೂರಾತಿ ಇರುವುದಿಲ್ಲ.",
        "application_portal": "https://example.gov.in/demo-soil",
        "applicable_geography": {"state": "Karnataka"},
        "dataset_version": "2026.1",
        "rule_version": "1.0.0",
        "verification_status": "VERIFIED_FOR_DEMO_ONLY",
        "definition": {
            "demo_only": True,
            "required_slots": ["district", "crop"],
            "eligibility_conditions": [
                {"slot_key": "district", "operator": "EXISTS", "expected_value": True},
                {"slot_key": "crop", "operator": "EXISTS", "expected_value": True},
            ],
        },
    },
]


def upgrade() -> None:
    # 1. Add new columns to schemes table
    op.add_column("schemes", sa.Column("display_name_kn", sa.String(255), nullable=True))
    op.add_column("schemes", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("schemes", sa.Column("description_kn", sa.Text(), nullable=True))
    op.add_column("schemes", sa.Column("benefit_description", sa.Text(), nullable=True))
    op.add_column("schemes", sa.Column("benefit_description_kn", sa.Text(), nullable=True))
    op.add_column("schemes", sa.Column("application_portal", sa.String(500), nullable=True))
    op.add_column("schemes", sa.Column("applicable_geography", sa.JSON(), nullable=True))
    op.add_column("schemes", sa.Column("dataset_version", sa.String(50), server_default="2026.1", nullable=False))

    # 2. Update scheme rows with catalogue metadata
    schemes_table = sa.table(
        "schemes",
        sa.column("id", sa.String(36)),
        sa.column("scheme_id", sa.String(100)),
        sa.column("display_name_kn", sa.String(255)),
        sa.column("description", sa.Text()),
        sa.column("description_kn", sa.Text()),
        sa.column("benefit_description", sa.Text()),
        sa.column("benefit_description_kn", sa.Text()),
        sa.column("application_portal", sa.String(500)),
        sa.column("applicable_geography", sa.JSON()),
        sa.column("dataset_version", sa.String(50)),
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

    connection = op.get_bind()
    now = datetime.now(timezone.utc)

    for item in SCHEME_UPDATES:
        scheme_id = item["scheme_id"]
        # Update schemes table
        connection.execute(
            schemes_table.update()
            .where(schemes_table.c.scheme_id == scheme_id)
            .values(
                display_name_kn=item["display_name_kn"],
                description=item["description"],
                description_kn=item["description_kn"],
                benefit_description=item["benefit_description"],
                benefit_description_kn=item["benefit_description_kn"],
                application_portal=item["application_portal"],
                applicable_geography=item["applicable_geography"],
                dataset_version=item["dataset_version"],
            )
        )

        # Lookup scheme UUID
        result = connection.execute(
            sa.select(schemes_table.c.id).where(schemes_table.c.scheme_id == scheme_id)
        ).first()

        if result:
            scheme_uuid = result[0]
            def_str = json.dumps(item["definition"], sort_keys=True)
            def_hash = hashlib.sha256(def_str.encode("utf-8")).hexdigest()

            # Insert or update rule version
            existing_rv = connection.execute(
                sa.select(rule_versions_table.c.id).where(
                    sa.and_(
                        rule_versions_table.c.scheme_id == scheme_uuid,
                        rule_versions_table.c.rule_version == item["rule_version"],
                    )
                )
            ).first()

            if existing_rv:
                connection.execute(
                    rule_versions_table.update()
                    .where(rule_versions_table.c.id == existing_rv[0])
                    .values(
                        definition=item["definition"],
                        definition_hash=def_hash,
                        verification_status=item["verification_status"],
                    )
                )
            else:
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
    op.drop_column("schemes", "dataset_version")
    op.drop_column("schemes", "applicable_geography")
    op.drop_column("schemes", "application_portal")
    op.drop_column("schemes", "benefit_description_kn")
    op.drop_column("schemes", "benefit_description")
    op.drop_column("schemes", "description_kn")
    op.drop_column("schemes", "description")
    op.drop_column("schemes", "display_name_kn")
