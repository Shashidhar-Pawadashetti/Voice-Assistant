"""Official specification for Pradhan Mantri Fasal Bima Yojana (PMFBY).

Conforms to Directive M4.1, M4.2, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 08_SCHEME_CATALOG_SEED.md.
Official source: Ministry of Agriculture and Farmers Welfare, Government of India.

CRITICAL INVARIANT (Directive M4.2 & Seed Policy):
PMFBY eligibility is legally and operationally contingent upon:
1. Current seasonal gazette notification by the State Government (Kharif/Rabi/Summer).
2. Notified Defined Area (District, Taluk, Hobli, Gram Panchayat).
3. Notified Crop list for that specific defined area.
4. Active cut-off date adherence.
Because state seasonal notifications cannot be invented, this scheme is preserved with
verification_status: INCOMPLETE, which deterministically produces RULES_NOT_VERIFIED.
"""

from app.core.scheme.enums import (
    GovernmentLevel,
    RuleOperator,
    SchemeClassification,
    VerificationStatus,
)
from app.core.scheme.schemas import EvidenceReference, RuleCondition, SchemeDefinition


PMFBY_EVIDENCE = [
    EvidenceReference(
        source_title="Revised Operational Guidelines for Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        source_url="https://pmfby.gov.in/",
        publisher="Department of Agriculture, Cooperation & Farmers Welfare, Ministry of Agriculture & FW, Government of India",
        publication_date="2020-04-01",
        access_date="2026-10-31",
        section="Section II & III",
        paragraph="Coverage of Farmers & Notified Crops/Areas",
        summary="Requires seasonal government notification defining eligible insurance units (Gram Panchayat/Hobli), notified crops, and strict enrollment cut-off dates.",
    ),
    EvidenceReference(
        source_title="PMFBY Official National Crop Insurance Portal",
        source_url="https://pmfby.gov.in/",
        publisher="Ministry of Agriculture and Farmers Welfare, Government of India",
        publication_date="2024-01-01",
        access_date="2026-10-31",
        section="Seasonal Notifications & Premium Calculator",
        paragraph="State Seasonal Notifications",
        summary="Karnataka State Department of Agriculture notifies specific crops and insurance units each season under Samrakshane portal.",
    ),
]


PMFBY_SCHEME = SchemeDefinition(
    scheme_id="PMFBY",
    official_name="Pradhan Mantri Fasal Bima Yojana",
    display_name="Pradhan Mantri Fasal Bima Yojana (PMFBY)",
    display_name_kn="ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ (ಪಿಎಂಎಫ್‌ಬಿವೈ)",
    classification=SchemeClassification.REAL_GOVERNMENT,
    government_level=GovernmentLevel.CENTRAL,
    assistance_category="CROP_INSURANCE",
    description="Comprehensive crop insurance scheme providing financial support to farmers suffering crop loss or damage due to unforeseen natural events.",
    description_kn="ನೈಸರ್ಗಿಕ ವಿಕೋಪಗಳಿಂದ ಉಂಟಾಗುವ ಬೆಳೆ ನಷ್ಟಕ್ಕೆ ಆರ್ಥಿಕ ಭದ್ರತೆ ನೀಡುವ ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ.",
    benefit_description="Insurance coverage and financial support for notified crops against non-preventable natural risks from pre-sowing to post-harvest.",
    benefit_description_kn="ಅಧಿಸೂಚಿತ ಬೆಳೆಗಳಿಗೆ ನೈಸರ್ಗಿಕ ವಿಕೋಪಗಳಿಂದ ಆಗುವ ಹಾನಿಗೆ ವಿಮಾ ರಕ್ಷಣೆ ಮತ್ತು ಪರಿಹಾರ ನೆರವು.",
    application_portal="https://pmfby.gov.in/",
    application_procedure="Farmers can enroll through banks, Primary Agricultural Credit Societies (PACS), CSCs, or Samrakshane portal in Karnataka within the notified cut-off date.",
    application_procedure_kn="ರೈತರು ಬ್ಯಾಂಕ್, ಪ್ರಾಥಮಿಕ ಕೃಷಿ ಪತ್ತಿನ ಸಹಕಾರ ಸಂಘ (PACS), ಗ್ರಾಮ ಒನ್ ಅಥವಾ ಕರ್ನಾಟಕದ 'ಸಂರಕ್ಷಣೆ' ಪೋರ್ಟಲ್ ಮೂಲಕ ನಿಗದಿತ ದಿನಾಂಕದೊಳಗೆ ನೋಂದಾಯಿಸಿಕೊಳ್ಳಬಹುದು.",
    applicable_geography={"state": "Karnataka", "country": "India"},
    required_slots=["district", "crop", "season"],
    eligibility_conditions=[
        RuleCondition(
            slot_key="district",
            operator=RuleOperator.EXISTS,
            expected_value=True,
            evidence_reference="PMFBY Guidelines Section III - Notified Unit",
            condition_explanation="Requires land location in a notified district.",
            condition_explanation_kn="ಅಧಿಸೂಚಿತ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜಮೀನು ಹೊಂದಿರಬೇಕು.",
            is_exclusion=False,
        ),
        RuleCondition(
            slot_key="crop",
            operator=RuleOperator.EXISTS,
            expected_value=True,
            evidence_reference="PMFBY Guidelines Section III - Notified Crop",
            condition_explanation="Crop must be officially notified for insurance in the specific taluk/hobli.",
            condition_explanation_kn="ಸಂಬಂಧಪಟ್ಟ ತಾಲೂಕು/ಹೋಬಳಿಗೆ ಬೆಳೆ ಅಧಿಸೂಚನೆ ಆಗಿರಬೇಕು.",
            is_exclusion=False,
        ),
        RuleCondition(
            slot_key="season",
            operator=RuleOperator.EXISTS,
            expected_value=True,
            evidence_reference="PMFBY Guidelines Section III - Notified Season",
            condition_explanation="Must correspond to an active notified crop season (Kharif/Rabi/Summer).",
            condition_explanation_kn="ಪ್ರಸ್ತುತ ಚಾಲ್ತಿಯಲ್ಲಿರುವ ಕೃಷಿ ಹಂಗಾಮು (ಮುಂಗಾರು/ಹಿಂಗಾರು) ಆಗಿರಬೇಕು.",
            is_exclusion=False,
        ),
    ],
    exclusions=[],
    required_documents=[
        "Aadhaar Card",
        "Land Record (Bhoomi Pahani / RTC)",
        "Sowing Certificate / Crop Sown Declaration from Village Accountant or Farmer Declaration",
        "Active Bank Account Passbook",
    ],
    required_documents_kn=[
        "ಆಧಾರ್ ಕಾರ್ಡ್",
        "ಭೂಮಿ ಪಹಣಿ / ಆರ್‌ಟಿಸಿ (RTC)",
        "ಬೆಳೆ ದೃಢೀಕರಣ ಪತ್ರ / ರೈತರ ಬೆಳೆ ಘೋಷಣೆ",
        "ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್ ಪ್ರತಿ",
    ],
    verification_status=VerificationStatus.INCOMPLETE,
    evidence_references=PMFBY_EVIDENCE,
    rule_version="0.0.0",
    dataset_version="2026.1",
    demo_only=False,
    official_verification_required=True,
    notes="Verification status is INCOMPLETE pending seasonal gazette crop notifications. Returns RULES_NOT_VERIFIED to protect farmers from unverified claims.",
)
