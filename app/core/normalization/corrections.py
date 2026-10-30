"""Natural Kannada correction semantics, negation parsing, and slot audit trail.

Conforms to 02_PRODUCT_REQUIREMENTS.md Section 1 (FR-009) and M2.5.
Handles spoken corrections like:
- 'ನಾಲ್ಕು ಎಕರೆ ಅಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ'
- 'ಧಾರವಾಡ ಅಲ್ಲ, ಗದಗ'
- 'ತಪ್ಪಾಯಿತು, ಬೆಳೆ ಜೋಳ ಅಲ್ಲ ರಾಗಿ'
- 'ಬದಲಾಗಿ, 5 ಎಕರೆ'
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


CORRECTION_MARKERS = ("ಅಲ್ಲ", "ತಪ್ಪು", "ಬದಲಾಗಿ", "ಇಲ್ಲ", "ತಪ್ಪಾಗಿದೆ", "ಬದಲು", "not")


class SlotAuditRecord(BaseModel):
    """Immutable audit record representing a slot value revision."""

    slot: str = Field(description="Canonical slot key (district, crop, land_area, etc.)")
    previous_value: Any = Field(description="Value before correction")
    new_value: Any = Field(description="Newly affirmed value")
    raw_correction_utterance: str = Field(description="Spoken utterance that modified the slot")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the correction",
    )
    reason: str = Field(default="USER_CORRECTION", description="Provenance reason")


class CorrectionDetectionResult(BaseModel):
    """Analysis of a potential correction utterance."""

    is_correction: bool = Field(default=False, description="Whether utterance is an explicit correction")
    negated_part: Optional[str] = Field(default=None, description="The old rejected fact (e.g. 'ನಾಲ್ಕು ಎಕರೆ')")
    corrected_part: Optional[str] = Field(default=None, description="The replacement fact (e.g. 'ಮೂರೂವರೆ ಎಕರೆ')")
    target_slot: Optional[str] = Field(default=None, description="Target slot name if identifiable")


# Regex for "X ಅಲ್ಲ, Y" or "X ಅಲ್ಲ Y" or "ತಪ್ಪು, Y"
CORRECTION_PATTERNS = [
    # 'X ಅಲ್ಲ, Y' / 'X ಅಲ್ಲ Y'
    re.compile(r"(.+?)\s+ಅಲ್ಲ[,\s]+(.+)", re.IGNORECASE),
    # 'ತಪ್ಪು, Y' / 'ತಪ್ಪಾಯಿತು, Y'
    re.compile(r"(?:ತಪ್ಪಾಯಿತು|ತಪ್ಪು|ತಪ್ಪಾಗಿದೆ)[,\s]+(.+)", re.IGNORECASE),
    # 'X ಬದಲಾಗಿ Y' / 'X ಬದಲು Y'
    re.compile(r"(.+?)\s+(?:ಬದಲಾಗಿ|ಬದಲು)[,\s]+(.+)", re.IGNORECASE),
    # 'ಇಲ್ಲ, Y'
    re.compile(r"^ಇಲ್ಲ[,\s]+(.+)", re.IGNORECASE),
]


def detect_correction(utterance: str) -> CorrectionDetectionResult:
    """Analyze whether a farmer's utterance is an explicit correction."""
    if not utterance or not utterance.strip():
        return CorrectionDetectionResult(is_correction=False)

    text = utterance.strip()

    # Pattern 1: X ಅಲ್ಲ, Y
    match1 = CORRECTION_PATTERNS[0].search(text)
    if match1:
        negated = match1.group(1).strip()
        corrected = match1.group(2).strip()
        return CorrectionDetectionResult(
            is_correction=True,
            negated_part=negated,
            corrected_part=corrected,
        )

    # Pattern 2: ತಪ್ಪಾಯಿತು, Y
    match2 = CORRECTION_PATTERNS[1].search(text)
    if match2:
        corrected = match2.group(1).strip()
        return CorrectionDetectionResult(
            is_correction=True,
            negated_part=None,
            corrected_part=corrected,
        )

    # Pattern 3: X ಬದಲಾಗಿ Y
    match3 = CORRECTION_PATTERNS[2].search(text)
    if match3:
        negated = match3.group(1).strip()
        corrected = match3.group(2).strip()
        return CorrectionDetectionResult(
            is_correction=True,
            negated_part=negated,
            corrected_part=corrected,
        )

    # Pattern 4: ಇಲ್ಲ, Y
    match4 = CORRECTION_PATTERNS[3].search(text)
    if match4:
        corrected = match4.group(1).strip()
        return CorrectionDetectionResult(
            is_correction=True,
            negated_part=None,
            corrected_part=corrected,
        )

    # Single marker check
    for marker in CORRECTION_MARKERS:
        if marker in text:
            return CorrectionDetectionResult(
                is_correction=True,
                negated_part=None,
                corrected_part=text,
            )

    return CorrectionDetectionResult(is_correction=False)
