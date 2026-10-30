"""Confirmation and rejection semantics for Krishi Mitra conversational intelligence.

Conforms to Directive M3.4 and 06_DIALOGUE_AND_MEMORY.md Section 7.
Handles:
- Spoken confirmation acceptance ("ಹೌದು", "ಸರಿ", "ಖಚಿತ", "yes", "correct").
- Spoken rejection ("ಇಲ್ಲ", "ತಪ್ಪು", "ಅಲ್ಲ", "no", "wrong").
- Spoken correction routing ("ಅಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ").
- Invariant: A user confirmation marks a fact as USER_CONFIRMED, never government-verified.
"""

from enum import Enum
import re
from typing import Optional, Tuple
from pydantic import BaseModel, Field

from app.core.normalization.corrections import detect_correction


class ConfirmationDecision(str, Enum):
    """Dialogue confirmation classification."""

    AFFIRMED = "AFFIRMED"      # Farmer confirmed the stated value
    REJECTED = "REJECTED"      # Farmer rejected without new value
    CORRECTED = "CORRECTED"    # Farmer rejected and supplied replacement value
    UNCLEAR = "UNCLEAR"        # Ambiguous response requiring re-asking


class ConfirmationAnalysis(BaseModel):
    """Result of analyzing a farmer's response during the CONFIRMING state."""

    decision: ConfirmationDecision
    raw_utterance: str
    corrected_part: Optional[str] = Field(
        default=None,
        description="Extracted replacement fact if farmer corrected during confirmation",
    )


# Curated Kannada and code-mixed affirmative expressions
AFFIRMATIVE_PATTERN = re.compile(
    r"(?<![\w\u0C80-\u0CFF])(ಹೌದು|ಸರಿ|ಖಚಿತ|ಹೌದ್ರಿ|ಖಂಡಿತ|ಹೌದುರೀ|ಹೌದು ಸರಿ|ಸರಿಯಾಗಿದೆ|ಅದೇ|ನನ್ನದೇ|yes|correct|true|right|confirm|yeah)(?![\w\u0C80-\u0CFF])",
    re.IGNORECASE,
)

# Curated Kannada and code-mixed negative expressions
NEGATIVE_PATTERN = re.compile(
    r"(?<![\w\u0C80-\u0CFF])(ಇಲ್ಲ|ತಪ್ಪು|ಅಲ್ಲ|ತಪ್ಪಾಗಿದೆ|ಇಲ್ಲ್ರಿ|ತಪ್ಪಾಯಿತು|ಬೇಡ|ಅಲ್ಲವೇ ಅಲ್ಲ|no|wrong|false|incorrect|not)(?![\w\u0C80-\u0CFF])",
    re.IGNORECASE,
)


def analyze_confirmation(utterance: str) -> ConfirmationAnalysis:
    """Classify a farmer's response when waiting for slot confirmation."""
    if not utterance or not utterance.strip():
        return ConfirmationAnalysis(
            decision=ConfirmationDecision.UNCLEAR,
            raw_utterance="",
        )

    clean = utterance.strip()
    has_negative = bool(NEGATIVE_PATTERN.search(clean))
    has_affirmative = bool(AFFIRMATIVE_PATTERN.search(clean))

    # Step 1: Check for pure standalone negation/rejection (e.g. "ಇಲ್ಲ", "ತಪ್ಪು", "no")
    clean_no_punct = re.sub(r"[,.\-!]", " ", clean).strip()
    words = clean_no_punct.split()
    if has_negative and not has_affirmative:
        # Check if all words are negative markers (e.g. "ಇಲ್ಲ", "ತಪ್ಪು", "ತಪ್ಪಾಗಿದೆ")
        if all(NEGATIVE_PATTERN.match(w) for w in words):
            return ConfirmationAnalysis(
                decision=ConfirmationDecision.REJECTED,
                raw_utterance=clean,
            )

    # Step 2: Check for explicit spoken correction ("ನಾಲ್ಕು ಅಲ್ಲ ಮೂರು", "ಇಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ")
    correction_result = detect_correction(clean)
    if correction_result.is_correction and correction_result.corrected_part:
        # Verify corrected_part is not just the negation word itself
        if not NEGATIVE_PATTERN.fullmatch(correction_result.corrected_part.strip()):
            return ConfirmationAnalysis(
                decision=ConfirmationDecision.CORRECTED,
                raw_utterance=clean,
                corrected_part=correction_result.corrected_part,
            )

    # Step 3: Check if negative with additional words (e.g. "ಇಲ್ಲ ಮೂರು ಎಕರೆ")
    if has_negative and not has_affirmative and len(words) > 1:
        rest = " ".join(words[1:]).strip()
        return ConfirmationAnalysis(
            decision=ConfirmationDecision.CORRECTED,
            raw_utterance=clean,
            corrected_part=rest,
        )

    # Step 4: Check for affirmative confirmation
    if has_affirmative and not has_negative:
        return ConfirmationAnalysis(
            decision=ConfirmationDecision.AFFIRMED,
            raw_utterance=clean,
        )

    # Step 5: If only negative and reached here
    if has_negative and not has_affirmative:
        return ConfirmationAnalysis(
            decision=ConfirmationDecision.REJECTED,
            raw_utterance=clean,
        )

    # Ambiguous or contradictory
    return ConfirmationAnalysis(
        decision=ConfirmationDecision.UNCLEAR,
        raw_utterance=clean,
    )
