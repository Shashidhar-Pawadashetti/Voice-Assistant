"""Synthetic demonstration scheme for Soil Improvement Support.

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


DEMO_SOIL_SCHEME = SchemeDefinition(
    scheme_id="DEMO_SOIL_IMPROVEMENT",
    official_name="Demo Soil Improvement Support (Demonstration Only)",
    display_name="Demo Soil Improvement Support",
    display_name_kn="ಮಾದರಿ ಮಣ್ಣು ಸುಧಾರಣೆ ಸಹಾಯಧನ (ಡೆಮೊ ಮಾತ್ರ)",
    classification=SchemeClassification.SYNTHETIC_DEMO,
    government_level=GovernmentLevel.NONE,
    assistance_category="SOIL_IMPROVEMENT",
    description="Synthetic demonstration decision path for testing soil health and fertilizer subsidy recommendation paths.",
    description_kn="ಮಣ್ಣು ಸುಧಾರಣೆ ಮತ್ತು ಪೋಷಕಾಂಶಗಳ ಸಹಾಯಧನ ನಿಯಮಗಳನ್ನು ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ (ಡೆಮೊ) ಯೋಜನೆ.",
    benefit_description="Synthetic subsidy test fixture for soil improvement decision rules. Confers NO real entitlement.",
    benefit_description_kn="ಮಣ್ಣು ಪರೀಕ್ಷೆ ಮತ್ತು ಸುಧಾರಣೆ ಸಲಹೆ ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ ನೆರವು. ನೈಜ ಮಂಜೂರಾತಿ ಇರುವುದಿಲ್ಲ.",
    application_portal="https://example.gov.in/demo-soil",
    application_procedure="Synthetic test procedure for automated testing and demonstrations.",
    application_procedure_kn="ತಂತ್ರಜ್ಞಾನ ಪ್ರಾತ್ಯಕ್ಷಿಕೆಗಾಗಿ ಮಾತ್ರ ಈ ವಿಧಾನವನ್ನು ನೀಡಲಾಗಿದೆ.",
    applicable_geography={"state": "Karnataka"},
    required_slots=["district", "crop"],
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
            slot_key="crop",
            operator=RuleOperator.EXISTS,
            expected_value=True,
            condition_explanation="Requires specified primary crop.",
            condition_explanation_kn="ಮುಖ್ಯ ಬೆಳೆಯ ವಿವರ ಅಗತ್ಯವಿದೆ.",
            is_exclusion=False,
        ),
    ],
    exclusions=[],
    required_documents=[
        "Demo Soil Test Health Card",
    ],
    required_documents_kn=[
        "ಮಾದರಿ ಮಣ್ಣು ಆರೋಗ್ಯ ಕಾರ್ಡ್ (Soil Health Card)",
    ],
    verification_status=VerificationStatus.VERIFIED_FOR_DEMO_ONLY,
    evidence_references=[
        EvidenceReference(
            source_title="Krishi Mitra Prototype Challenge Synthetic Seed Catalog",
            source_url="https://github.com/Shashidhar-Pawadashetti/Voice-Assistant",
            publisher="Krishi Mitra Specification 08",
            access_date="2026-10-31",
            section="Section 3",
            paragraph="DEMO_SOIL_IMPROVEMENT",
            summary="Synthetic demonstration seed record for soil improvement test flows.",
        )
    ],
    rule_version="1.0.0",
    dataset_version="2026.1",
    demo_only=True,
    official_verification_required=False,
    notes="DEMO_ONLY synthetic scheme. Never display as real government assistance.",
)
