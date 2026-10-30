"""Official, verified specification for Pradhan Mantri Kisan Samman Nidhi (PM-KISAN).

Conforms to Directive M4.1, M4.2, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 08_SCHEME_CATALOG_SEED.md.
All conditions, exclusions, and citations are extracted directly from official guidelines.
No rules or criteria are invented.
"""

from app.core.scheme.enums import (
    EvidenceLevel,
    GovernmentLevel,
    RuleOperator,
    SchemeClassification,
    VerificationStatus,
)
from app.core.scheme.schemas import EvidenceReference, RuleCondition, SchemeDefinition


PM_KISAN_EVIDENCE = [
    EvidenceReference(
        source_title="Operational Guidelines of Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        source_url="https://pmkisan.gov.in/Documents/OperationalGuidelines_PMKISAN.pdf",
        publisher="Department of Agriculture, Cooperation & Farmers Welfare, Ministry of Agriculture & FW, Government of India",
        publication_date="2020-08-01",
        access_date="2026-10-31",
        section="Clause 2 & 3",
        paragraph="Definition of Beneficiary & Exclusion Criteria",
        summary="Defines eligible landholder farmer families having cultivable land in state revenue records and enumerates institutional and income-based exclusions.",
    ),
    EvidenceReference(
        source_title="PM-KISAN Official Government Portal",
        source_url="https://pmkisan.gov.in/",
        publisher="Ministry of Agriculture and Farmers Welfare, Government of India",
        publication_date="2024-01-01",
        access_date="2026-10-31",
        section="Mandatory Pre-requisites & e-KYC",
        paragraph="Aadhaar-seeded bank account and eKYC requirements",
        summary="Aadhaar linkage, active bank account seeded with Aadhaar (DBT enabled), and state land record (Bhoomi) verification are mandatory.",
    ),
]


PM_KISAN_SCHEME = SchemeDefinition(
    scheme_id="PM_KISAN",
    official_name="Pradhan Mantri Kisan Samman Nidhi",
    display_name="PM-KISAN",
    display_name_kn="ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ (ಪಿಎಂ-ಕಿಸಾನ್)",
    classification=SchemeClassification.REAL_GOVERNMENT,
    government_level=GovernmentLevel.CENTRAL,
    assistance_category="INCOME_SUPPORT",
    description="Central Sector scheme to provide income support to all landholding eligible farmer families having cultivable land in their names.",
    description_kn="ತಮ್ಮ ಹೆಸರಿನಲ್ಲಿ ಕೃಷಿ ಯೋಗ್ಯ ಜಮೀನು ಹೊಂದಿರುವ ಅರ್ಹ ರೈತ ಕುಟುಂಬಗಳಿಗೆ ಆದಾಯ ಬೆಂಬಲ ನೀಡುವ ಕೇಂದ್ರ ಸರ್ಕಾರದ ಯೋಜನೆ.",
    benefit_description="Income support of Rs. 6,000 per year in three equal 4-monthly instalments directly into Aadhaar-seeded bank accounts.",
    benefit_description_kn="ಆಧಾರ್ ಜೋಡಿಸಲಾದ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ನೇರವಾಗಿ 4 ತಿಂಗಳಿಗೊಮ್ಮೆ ತಲಾ ₹2,000 ರಂತೆ ವರ್ಷಕ್ಕೆ ₹6,000 ಆದಾಯ ನೆರವು.",
    application_portal="https://pmkisan.gov.in/",
    application_procedure="Farmers can register online through Farmers Corner on the PM-KISAN portal or via Common Service Centres (CSC). In Karnataka, verification is integrated with Bhoomi land records and FRUITS portal.",
    application_procedure_kn="ರೈತರು ಪಿಎಂ-ಕಿಸಾನ್ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ 'ರೈತರ ಮೂಲೆ' (Farmers Corner) ಅಥವಾ ಗ್ರಾಮ ಒನ್ / ಸಿಎಸ್‌ಸಿ ಕೇಂದ್ರಗಳ ಮೂಲಕ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು. ಕರ್ನಾಟಕದಲ್ಲಿ ಭೂಮಿ ಮತ್ತು ಫ್ರೂಟ್ಸ್ ತಂತ್ರಾಂಶದ ಮೂಲಕ ದಾಖಲೆ ಪರಿಶೀಲನೆ ನಡೆಯುತ್ತದೆ.",
    applicable_geography={"state": "Karnataka", "country": "India"},
    required_slots=["land_ownership", "district"],
    eligibility_conditions=[
        RuleCondition(
            slot_key="land_ownership",
            operator=RuleOperator.IN,
            expected_value=["OWNER", "CO_OWNER"],
            required_provenance=EvidenceLevel.OFFICIALLY_VERIFIED,
            evidence_reference="PM-KISAN Operational Guidelines Clause 2(b)",
            condition_explanation="Cultivable landholding must be held in the name of the farmer or farmer family as per state revenue records.",
            condition_explanation_kn="ಕಂದಾಯ ದಾಖಲೆಗಳ ಪ್ರಕಾರ ಕೃಷಿ ಜಮೀನು ರೈತರ ಅಥವಾ ರೈತ ಕುಟುಂಬದ ಹೆಸರಿನಲ್ಲಿರಬೇಕು.",
            is_exclusion=False,
        ),
    ],
    exclusions=[
        RuleCondition(
            slot_key="land_ownership",
            operator=RuleOperator.EQ,
            expected_value="INSTITUTIONAL",
            evidence_reference="PM-KISAN Operational Guidelines Clause 3(a)",
            condition_explanation="All institutional landholders are excluded.",
            condition_explanation_kn="ಸಾಂಸ್ಥಿಕ ಜಮೀನು ಮಾಲೀಕರು ಈ ಯೋಜನೆಗೆ ಅನರ್ಹರು.",
            is_exclusion=True,
        ),
        RuleCondition(
            slot_key="income_tax_payer",
            operator=RuleOperator.EQ,
            expected_value=True,
            evidence_reference="PM-KISAN Operational Guidelines Clause 3(b)(v)",
            condition_explanation="Any member of the family who paid income tax in the last assessment year is excluded.",
            condition_explanation_kn="ಕಳೆದ ಮೌಲ್ಯಮಾಪನ ವರ್ಷದಲ್ಲಿ ಆದಾಯ ತೆರಿಗೆ ಪಾವತಿಸಿದ ಸದಸ್ಯರಿರುವ ಕುಟುಂಬಗಳು ಅನರ್ಹವಾಗಿವೆ.",
            is_exclusion=True,
        ),
        RuleCondition(
            slot_key="govt_employee",
            operator=RuleOperator.EQ,
            expected_value=True,
            evidence_reference="PM-KISAN Operational Guidelines Clause 3(b)(iii)",
            condition_explanation="Serving or retired government officers and regular employees (excluding Group D / Multi-Tasking Staff) are excluded.",
            condition_explanation_kn="ಸರ್ಕಾರಿ ನೌಕರರು (ಗ್ರೂಪ್-ಡಿ / ಮಲ್ಟಿ-ಟಾಸ್ಕಿಂಗ್ ಸಿಬ್ಬಂದಿ ಹೊರತುಪಡಿಸಿ) ಈ ಯೋಜನೆಗೆ ಅನರ್ಹರು.",
            is_exclusion=True,
        ),
        RuleCondition(
            slot_key="constitutional_post_holder",
            operator=RuleOperator.EQ,
            expected_value=True,
            evidence_reference="PM-KISAN Operational Guidelines Clause 3(b)(i)",
            condition_explanation="Former and present holders of constitutional posts, ministers, MPs, and MLAs are excluded.",
            condition_explanation_kn="ಸಾಂವಿಧಾನಿಕ ಹುದ್ದೆಗಳನ್ನು ಹೊಂದಿರುವವರು ಅಥವಾ ಹೊಂದಿದ್ದವರು ಈ ಯೋಜನೆಗೆ ಅನರ್ಹರು.",
            is_exclusion=True,
        ),
    ],
    required_documents=[
        "Aadhaar Card",
        "Aadhaar-seeded active Bank Account details",
        "Land Record (Bhoomi RTC / Pahani in Karnataka)",
        "Mobile Number linked to Aadhaar for e-KYC",
    ],
    required_documents_kn=[
        "ಆಧಾರ್ ಕಾರ್ಡ್",
        "ಆಧಾರ್ ಜೋಡಿಸಲಾದ ಸಕ್ರಿಯ ಬ್ಯಾಂಕ್ ಖಾತೆ ವಿವರ",
        "ಭೂಮಿ ಪಹಣಿ / ಆರ್‌ಟಿಸಿ (RTC)",
        "ಇ-ಕೆವೈಸಿಗಾಗಿ ಆಧಾರ್‌ಗೆ ಲಿಂಕ್ ಆದ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ",
    ],
    verification_status=VerificationStatus.VERIFIED,
    evidence_references=PM_KISAN_EVIDENCE,
    rule_version="1.0.0",
    dataset_version="2026.1",
    demo_only=False,
    official_verification_required=True,
    notes="Verification against state land records (Bhoomi) and e-KYC is mandatory before any disbursement.",
)
