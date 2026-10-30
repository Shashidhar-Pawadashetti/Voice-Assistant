"""Land ownership classification and assertion provenance handling.

Conforms to 02_PRODUCT_REQUIREMENTS.md Section 3, 05_VOICE_AI_PIPELINE.md Section 6, and M2.4.
Non-negotiable rule:
Farming activity (e.g. 'ನಾನು ಬೆಳೆಯುತ್ತಿದ್ದೇನೆ' / 'I cultivate') must NEVER be inferred
as legal land ownership. User-stated facts can NEVER be labeled as government-verified.
"""

from enum import Enum
import re
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class OwnershipType(str, Enum):
    """Agricultural land ownership taxonomy."""

    OWNER = "OWNER"
    CO_OWNER = "CO_OWNER"
    LEASED = "LEASED"
    TENANT_OR_CULTIVATOR = "TENANT_OR_CULTIVATOR"
    UNKNOWN = "UNKNOWN"


class ProvenanceAssertion(str, Enum):
    """Assertion provenance level."""

    USER_STATED = "USER_STATED"
    USER_CONFIRMED = "USER_CONFIRMED"
    SYSTEM_DERIVED = "SYSTEM_DERIVED"


class NormalizedOwnership(BaseModel):
    """Normalized land tenure assertion with provenance and confirmation guard."""

    ownership_type: OwnershipType = Field(description="Classified tenure type")
    kannada_description: str = Field(description="Kannada phrase describing tenure")
    raw_utterance: str = Field(description="Farmer utterance excerpt")
    assertion: ProvenanceAssertion = Field(
        default=ProvenanceAssertion.USER_STATED,
        description="Strict provenance: USER_STATED, USER_CONFIRMED, or SYSTEM_DERIVED",
    )
    requires_confirmation: bool = Field(
        default=True,
        description="Critical slot requiring explicit confirmation before rule execution",
    )
    is_legal_ownership_proven: bool = Field(
        default=False,
        description="Invariant: always False for conversational turns without official land records",
    )


# Curated Kannada tenure phrases
OWNERSHIP_PATTERNS: List[Tuple[re.Pattern, OwnershipType, str]] = [
    # Explicit Sole Owner
    (
        re.compile(
            r"(?<![\w\u0C80-\u0CFF])(ಸ್ವಂತ ಜಮೀನು|ಸ್ವಂತ ಭೂಮಿ|ನನ್ನದೇ ಜಮೀನು|ನನ್ನ ಸ್ವಂತ|ನನ್ನ ಜಮೀನು|ಸ್ವಂತ ಖಾತೆ|ಖಾತೆದಾರ|ಮಾಲೀಕ|ಖಾತೆ ನನ್ನ ಹೆಸರಲ್ಲಿದೆ|ಸ್ವಂತ|owner|own land)(?![\w\u0C80-\u0CFF])",
            re.IGNORECASE,
        ),
        OwnershipType.OWNER,
        "ಸ್ವಂತ ಜಮೀನು",
    ),
    # Co-owner / Joint ownership
    (
        re.compile(
            r"(?<![\w\u0C80-\u0CFF])(ಜಂಟಿ ಖಾತೆ|ಪಾಲುದಾರಿಕೆ|ಅಣ್ಣ ತಮ್ಮಂದಿರ ಜಮೀನು|ಕುಟುಂಬದ ಜಮೀನು|ಪಾಲು|co-owner|joint account)(?![\w\u0C80-\u0CFF])",
            re.IGNORECASE,
        ),
        OwnershipType.CO_OWNER,
        "ಜಂಟಿ ಮಾಲೀಕತ್ವ",
    ),
    # Leased
    (
        re.compile(
            r"(?<![\w\u0C80-\u0CFF])(ಗುತ್ತಿಗೆ|ಗುತ್ತಿಗೆಗೆ ತಗೊಂಡಿದ್ದೇನೆ|ಲೀಸ್|ಲೀಸ್‌ಗೆ|lease|leased)(?![\w\u0C80-\u0CFF])",
            re.IGNORECASE,
        ),
        OwnershipType.LEASED,
        "ಗುತ್ತಿಗೆ ಜಮೀನು",
    ),
    # Tenant / Cultivator (Cultivation activity 'ಸಾಗುವಳಿ' indicates cultivator/tenant, but does NOT imply legal ownership!)
    (
        re.compile(
            r"(?<![\w\u0C80-\u0CFF])(ಗೇಣಿದಾರ|ಗೇಣಿದಾರನು|ಗೇಣಿದಾರರು|ಗೇಣಿ ಜಮೀನು|ಗೇಣಿ|ಸಾಗುವಳಿದಾರ|ಸಾಗುವಳಿದಾರರು|ಸಾಗುವಳಿ ಮಾಡುತ್ತಿದ್ದೇನೆ|ಸಾಗುವಳಿ ಜಮೀನು|ಸಾಗುವಳಿ|ಉಳುಮೆ ಮಾಡುತ್ತಿದ್ದೇನೆ|tenant|cultivator)(?![\w\u0C80-\u0CFF])",
            re.IGNORECASE,
        ),
        OwnershipType.TENANT_OR_CULTIVATOR,
        "ಗೇಣಿದಾರ / ಸಾಗುವಳಿದಾರ",
    ),
]


def normalize_ownership(
    text: str,
    assertion: ProvenanceAssertion = ProvenanceAssertion.USER_STATED,
) -> NormalizedOwnership:
    """Classify land ownership from an utterance without assuming legal title from cultivation."""
    if not text or not text.strip():
        return NormalizedOwnership(
            ownership_type=OwnershipType.UNKNOWN,
            kannada_description="ಮಾಲೀಕತ್ವದ ವಿವರ ತಿಳಿದಿಲ್ಲ",
            raw_utterance="",
            assertion=assertion,
            requires_confirmation=True,
            is_legal_ownership_proven=False,
        )

    clean_text = text.strip()

    for pattern, tenure_type, desc in OWNERSHIP_PATTERNS:
        if pattern.search(clean_text):
            return NormalizedOwnership(
                ownership_type=tenure_type,
                kannada_description=desc,
                raw_utterance=clean_text,
                assertion=assertion,
                # All critical ownership assertions require verbal confirmation
                requires_confirmation=True,
                is_legal_ownership_proven=False,  # Invariant: Never claim government verification
            )

    return NormalizedOwnership(
        ownership_type=OwnershipType.UNKNOWN,
        kannada_description="ಮಾಲೀಕತ್ವದ ವಿವರ ತಿಳಿದಿಲ್ಲ",
        raw_utterance=clean_text,
        assertion=assertion,
        requires_confirmation=True,
        is_legal_ownership_proven=False,
    )
