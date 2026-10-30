"""Synthetic demonstration scheme for Agricultural Equipment Assistance.

Conforms to Directive M4.1, M4.2, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 08_SCHEME_CATALOG_SEED.md.
CRITICAL INVARIANT:
This is a synthetic test fixture labelled DEMO_ONLY at all layers.
It confers no legal or governmental entitlement.
"""

from app.core.scheme.enums import (
    GovernmentLevel,
    RuleOperator,
    SchemeClassification,
    VerificationStatus,
)
from app.core.scheme.schemas import EvidenceReference, RuleCondition, SchemeDefinition


DEMO_EQUIPMENT_SCHEME = SchemeDefinition(
    scheme_id="DEMO_EQUIPMENT_ASSISTANCE",
    official_name="Demo Agricultural Equipment Assistance (Demonstration Only)",
    display_name="Demo Agricultural Equipment Assistance",
    display_name_kn="ಮಾದರಿ ಕೃಷಿ ಯಂತ್ರೋಪಕರಣ ಸಹಾಯಧನ (ಡೆಮೊ ಮಾತ್ರ)",
    classification=SchemeClassification.SYNTHETIC_DEMO,
    government_level=GovernmentLevel.NONE,
    assistance_category="AGRICULTURAL_EQUIPMENT",
    description="Synthetic demonstration decision path for testing equipment subsidy decision rules.",
    description_kn="ಕೃಷಿ ಯಂತ್ರೋಪಕರಣಗಳ ಸಹಾಯಧನ ನಿಯಮಗಳನ್ನು ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ (ಡೆಮೊ) ಯೋಜನೆ.",
    benefit_description="Synthetic subsidy test fixture for farm machinery decision rules. Confers NO real entitlement.",
    benefit_description_kn="ಯಂತ್ರೋಪಕರಣಗಳ ಸಲಹೆ ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ ನೆರವು. ನೈಜ ಮಂಜೂರಾತಿ ಇರುವುದಿಲ್ಲ.",
    application_portal="https://example.gov.in/demo-equipment",
    application_procedure="Synthetic test procedure for automated testing and demonstrations.",
    application_procedure_kn="ತಂತ್ರಜ್ಞಾನ ಪ್ರಾತ್ಯಕ್ಷಿಕೆಗಾಗಿ ಮಾತ್ರ ಈ ವಿಧಾನವನ್ನು ನೀಡಲಾಗಿದೆ.",
    applicable_geography={"state": "Karnataka"},
    required_slots=["district", "equipment"],
    eligibility_conditions=[
        RuleCondition(
            slot_key="district",
            operator=RuleOperator.EXISTS,
            expected_value=True,
            condition_explanation="Requires valid location in Karnataka.",
            condition_explanation_kn="ಕರ್ನಾಟಕದ ಯಾವುದೇ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜಮೀನು ಇರಬೇಕು.",
            is_exclusion=False,
        ),
        RuleCondition(
            slot_key="equipment",
            operator=RuleOperator.EXISTS,
            expected_value=True,
            condition_explanation="Requires specified agricultural equipment.",
            condition_explanation_kn="ಯಂತ್ರೋಪಕರಣದ ಹೆಸರು ನಿರ್ದಿಷ್ಟವಾಗಿರಬೇಕು.",
            is_exclusion=False,
        ),
    ],
    exclusions=[],
    required_documents=[
        "Demo Equipment Quotation",
    ],
    required_documents_kn=[
        "ಮಾದರಿ ಉಪಕರಣ ಬೆಲೆ ಪಟ್ಟಿ (Quotation)",
    ],
    verification_status=VerificationStatus.VERIFIED_FOR_DEMO_ONLY,
    evidence_references=[
        EvidenceReference(
            source_title="Krishi Mitra Prototype Challenge Synthetic Seed Catalog",
            source_url="https://github.com/Shashidhar-Pawadashetti/Voice-Assistant",
            publisher="Krishi Mitra Specification 08",
            access_date="2026-10-31",
            section="Section 3",
            paragraph="DEMO_EQUIPMENT_ASSISTANCE",
            summary="Synthetic demonstration seed record for equipment subsidy test flows.",
        )
    ],
    rule_version="1.0.0",
    dataset_version="2026.1",
    demo_only=True,
    official_verification_required=False,
    notes="DEMO_ONLY synthetic scheme. Never display as real government assistance.",
)
