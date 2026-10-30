"""Synthetic demonstration scheme for Micro-Irrigation.

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


DEMO_MICRO_IRRIGATION_SCHEME = SchemeDefinition(
    scheme_id="DEMO_MICRO_IRRIGATION",
    official_name="Demo Micro-Irrigation Support (Demonstration Only)",
    display_name="Demo Micro-Irrigation Support",
    display_name_kn="ಮಾದರಿ ಹನಿ ನೀರಾವರಿ ಸಹಾಯಧನ (ಡೆಮೊ ಮಾತ್ರ)",
    classification=SchemeClassification.SYNTHETIC_DEMO,
    government_level=GovernmentLevel.NONE,
    assistance_category="MICRO_IRRIGATION",
    description="Synthetic demonstration decision path for testing drip and sprinkler irrigation recommendation flows.",
    description_kn="ಹನಿ ಮತ್ತು ತುಂತುರು ನೀರಾವರಿ ಸಲಹೆ ಪರೀಕ್ಷಿಸಲು ರೂಪಿಸಲಾದ ಮಾದರಿ (ಡೆಮೊ) ಯೋಜನೆ. ಇದು ಕೇವಲ ತಾಂತ್ರಿಕ ಪ್ರಾತ್ಯಕ್ಷಿಕೆಗಾಗಿ ಮಾತ್ರ.",
    benefit_description="Synthetic subsidy test fixture for testing micro-irrigation decision rules. Confers NO real entitlement.",
    benefit_description_kn="ತಾಂತ್ರಿಕ ಪ್ರಾತ್ಯಕ್ಷಿಕೆಗಾಗಿ ರೂಪಿಸಲಾದ ಮಾದರಿ ಸಹಾಯಧನ ಪರೀಕ್ಷೆ. ಯಾವುದೇ ನೈಜ ಸರ್ಕಾರಿ ಸವಲತ್ತು ಇರುವುದಿಲ್ಲ.",
    application_portal="https://example.gov.in/demo-micro-irrigation",
    application_procedure="Synthetic test application flow for automated testing and demonstrations.",
    application_procedure_kn="ಪ್ರಾತ್ಯಕ್ಷಿಕೆ ಮತ್ತು ತಂತ್ರಜ್ಞಾನ ಪರೀಕ್ಷೆಗಾಗಿ ಮಾತ್ರ ಈ ವಿವರಗಳನ್ನು ನೀಡಲಾಗಿದೆ.",
    applicable_geography={"state": "Karnataka"},
    required_slots=["district", "land_area", "irrigation"],
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
            slot_key="land_area",
            operator=RuleOperator.GT,
            expected_value=0.0,
            unit="acres",
            condition_explanation="Cultivable land area must be greater than zero.",
            condition_explanation_kn="ಕೃಷಿ ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ ಶೂನ್ಯಕ್ಕಿಂತ ಹೆಚ್ಚಿರಬೇಕು.",
            is_exclusion=False,
        ),
        RuleCondition(
            slot_key="irrigation",
            operator=RuleOperator.IN,
            expected_value=["DRIP", "SPRINKLER", "BOREWELL", "CANAL", "OPEN_WELL", "RAIN_FED", "OTHER"],
            condition_explanation="Requires an identified water source or micro-irrigation interest.",
            condition_explanation_kn="ನೀರಾವರಿ ಅಥವಾ ನೀರಿನ ಮೂಲದ ವಿವರ ಅಗತ್ಯವಿದೆ.",
            is_exclusion=False,
        ),
    ],
    exclusions=[],
    required_documents=[
        "Demo Farmer ID",
        "Demo Land Record",
    ],
    required_documents_kn=[
        "ಮಾದರಿ ರೈತ ಗುರುತಿನ ಸಂಖ್ಯೆ",
        "ಮಾದರಿ ಜಮೀನು ದಾಖಲೆ",
    ],
    verification_status=VerificationStatus.VERIFIED_FOR_DEMO_ONLY,
    evidence_references=[
        EvidenceReference(
            source_title="Krishi Mitra Prototype Challenge Synthetic Seed Catalog",
            source_url="https://github.com/Shashidhar-Pawadashetti/Voice-Assistant",
            publisher="Krishi Mitra Specification 08",
            access_date="2026-10-31",
            section="Section 3",
            paragraph="DEMO_MICRO_IRRIGATION",
            summary="Synthetic demonstration seed record for prototype multi-turn evaluation testing.",
        )
    ],
    rule_version="1.0.0",
    dataset_version="2026.1",
    demo_only=True,
    official_verification_required=False,
    notes="DEMO_ONLY synthetic scheme. Never display as real government assistance.",
)
