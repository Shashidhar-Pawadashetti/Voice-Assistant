"""Land measurement normalization with Decimal precision and colloquial Kannada fractions.

Conforms to 02_PRODUCT_REQUIREMENTS.md Section 1 (FR-007) and 05_VOICE_AI_PIPELINE.md Section 8.
Conversion constants:
- 1 acre = 40 guntas (1 gunta = 0.025 acres)
- 1 hectare = 2.471053814671653 acres (1 acre = 0.40468564224 hectares)
"""

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import re
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel, Field


# Conversion constants using Decimal for exact financial and entitlement calculations
ACRE_TO_GUNTA = Decimal("40")
GUNTA_TO_ACRE = Decimal("1") / ACRE_TO_GUNTA  # 0.025
HECTARE_TO_ACRE = Decimal("2.471053814671653")
ACRE_TO_HECTARE = Decimal("0.40468564224")


class LandUnit(str, Enum):
    """Supported agricultural land units."""

    ACRE = "ACRE"
    GUNTA = "GUNTA"
    HECTARE = "HECTARE"


class NormalizedLandArea(BaseModel):
    """Immutable, precision-validated agricultural land measurement."""

    original_utterance: str = Field(description="Exact snippet or utterance")
    original_value: Decimal = Field(description="Numeric value as extracted from source")
    original_unit: LandUnit = Field(description="Extracted or inferred unit")
    canonical_acres: Decimal = Field(description="Normalized area in standard Decimal acres")
    canonical_guntas: Decimal = Field(description="Normalized area in guntas")
    canonical_hectares: Decimal = Field(description="Normalized area in hectares")
    is_ambiguous: bool = Field(default=False, description="Whether verbal clarification is needed")
    clarification_prompt: Optional[str] = Field(
        default=None,
        description="Kannada follow-up prompt if measurement is ambiguous",
    )
    conversion_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Exact conversion multipliers and rounding provenance",
    )


# Colloquial Kannada numeric and fractional word mappings
KANNADA_FRACTION_MAP: Dict[str, Decimal] = {
    "ಕಾಲು": Decimal("0.25"),
    "ಅರ್ಧ": Decimal("0.5"),
    "ಅರೆ": Decimal("0.5"),
    "ಮುಕ್ಕಾಲು": Decimal("0.75"),
    "ಒಂದೂವರೆ": Decimal("1.5"),
    "ಒಂದುವರೆ": Decimal("1.5"),
    "ಒಂದು ಮುಕ್ಕಾಲು": Decimal("1.75"),
    "ಎರಡೂವರೆ": Decimal("2.5"),
    "ಎರಡುವರೆ": Decimal("2.5"),
    "ಎರಡು ಮುಕ್ಕಾಲು": Decimal("2.75"),
    "ಮೂರಾವರೆ": Decimal("3.5"),
    "ಮೂರನ್ನರೆ": Decimal("3.5"),
    "ಮೂರೂವರೆ": Decimal("3.5"),
    "ಮೂರುವರೆ": Decimal("3.5"),
    "ಮೂರು ಮುಕ್ಕಾಲು": Decimal("3.75"),
    "ನಾಲ್ಕೂವರೆ": Decimal("4.5"),
    "ನಾಲ್ಕನ್ನರೆ": Decimal("4.5"),
    "ನಾಲ್ಕಾವರೆ": Decimal("4.5"),
    "ನಾಲ್ಕವರೆ": Decimal("4.5"),
    "ನಾಲ್ಕು ಮುಕ್ಕಾಲು": Decimal("4.75"),
    "ಐದೂವರೆ": Decimal("5.5"),
    "ಐದನ್ನರೆ": Decimal("5.5"),
    "ಐದಾವರೆ": Decimal("5.5"),
    "ಐದವರೆ": Decimal("5.5"),
}

# Standalone Kannada word numerals
KANNADA_WORD_NUMBERS: Dict[str, Decimal] = {
    "ಒಂದು": Decimal("1"),
    "ಎರಡು": Decimal("2"),
    "ಮೂರು": Decimal("3"),
    "ನಾಲ್ಕು": Decimal("4"),
    "ಐದು": Decimal("5"),
    "ಆರು": Decimal("6"),
    "ಏಳು": Decimal("7"),
    "ಎಂಟು": Decimal("8"),
    "ಒಂಬತ್ತು": Decimal("9"),
    "ಹತ್ತು": Decimal("10"),
    "ಹದಿನೈದು": Decimal("15"),
    "ಇಪ್ಪತ್ತು": Decimal("20"),
    "ಇಪ್ಪತ್ತೈದು": Decimal("25"),
    "ಮೂವತ್ತು": Decimal("30"),
    "ಮೂವತ್ತೈದು": Decimal("35"),
    "ನಲವತ್ತು": Decimal("40"),
    "ಐವತ್ತು": Decimal("50"),
}


def _detect_unit(text: str) -> Optional[LandUnit]:
    """Detect whether utterance references acres, guntas, or hectares."""
    lower = text.lower()

    if re.search(r"(?<![\w\u0C80-\u0CFF])(ಗುಂಟೆ|ಗುಂಟಾ|ಗಂಟೆ|gunta|guntas)(?![\w\u0C80-\u0CFF])", lower):
        return LandUnit.GUNTA
    if re.search(r"(?<![\w\u0C80-\u0CFF])(ಹೆಕ್ಟೇರ್|ಹೆಕ್ಟೇರು|ಹೆಕ್ಟೇರ|hectare|hectares)(?![\w\u0C80-\u0CFF])", lower):
        return LandUnit.HECTARE
    if re.search(r"(?<![\w\u0C80-\u0CFF])(ಎಕರೆ|ಎಕ್ರೆ|ಎಕರಾ|acre|acres)(?![\w\u0C80-\u0CFF])", lower):
        return LandUnit.ACRE

    return None


def normalize_land_area(utterance: str) -> Optional[NormalizedLandArea]:
    """Parse and normalize land measurement from a Kannada or code-mixed utterance.

    Handles whole numbers, decimals, colloquial fractions (ಒಂದೂವರೆ, ಎರಡೂವರೆ),
    and composite expressions (e.g., 2 ಎಕರೆ 20 ಗುಂಟೆ).

    Returns:
        NormalizedLandArea on success, or an object with is_ambiguous=True if unit is missing.
    """
    if not utterance or not utterance.strip():
        return None

    clean_text = utterance.strip()
    detected_unit = _detect_unit(clean_text)

    # 1. Check for Composite "X ಎಕರೆ Y ಗುಂಟೆ" (e.g. 2 ಎಕರೆ 20 ಗುಂಟೆ or 3 acre 15 gunta)
    composite_match = re.search(
        r"(\d+(?:\.\d+)?|[a-zA-Z\u0C80-\u0CFF]+)\s*(?:ಎಕರೆ|ಎಕ್ರೆ|acre|acres)\s*(\d+(?:\.\d+)?|[a-zA-Z\u0C80-\u0CFF]+)\s*(?:ಗುಂಟೆ|gunta|guntas)",
        clean_text,
        re.IGNORECASE,
    )
    if composite_match:
        raw_acre = composite_match.group(1).strip()
        raw_gunta = composite_match.group(2).strip()

        acre_val = KANNADA_FRACTION_MAP.get(raw_acre) or KANNADA_WORD_NUMBERS.get(raw_acre)
        if acre_val is None:
            try:
                acre_val = Decimal(raw_acre)
            except Exception:
                pass

        gunta_val = KANNADA_WORD_NUMBERS.get(raw_gunta)
        if gunta_val is None:
            try:
                gunta_val = Decimal(raw_gunta)
            except Exception:
                pass

        if acre_val is not None and gunta_val is not None:
            total_acres = acre_val + (gunta_val * GUNTA_TO_ACRE)
            return _create_normalized_result(
                utterance=clean_text,
                original_value=acre_val,
                original_unit=LandUnit.ACRE,
                total_acres=total_acres,
                metadata={"composite": True, "acres_part": str(acre_val), "guntas_part": str(gunta_val)},
            )

    # 2. Check for colloquial fractions (e.g. 'ಎರಡೂವರೆ ಎಕರೆ', 'ಮುಕ್ಕಾಲು ಎಕರೆ')
    # Sort phrases by length descending so longer phrases match before subphrases
    sorted_fractions = sorted(KANNADA_FRACTION_MAP.items(), key=lambda p: len(p[0]), reverse=True)
    for frac_phrase, frac_val in sorted_fractions:
        frac_pattern = re.compile(
            rf"(?<![\w\u0C80-\u0CFF]){re.escape(frac_phrase)}(?![\w\u0C80-\u0CFF])",
            re.IGNORECASE,
        )
        if frac_pattern.search(clean_text):
            unit = detected_unit or LandUnit.ACRE  # default to ACRE for Kannada colloquial fractions
            total_acres = _convert_to_acres(frac_val, unit)
            return _create_normalized_result(
                utterance=clean_text,
                original_value=frac_val,
                original_unit=unit,
                total_acres=total_acres,
                metadata={"fraction_phrase": frac_phrase},
            )

    # 3. Check for standalone Kannada word numerals with unit (e.g. "ಎರಡು ಎಕರೆ", "ಹತ್ತು ಗುಂಟೆ")
    for word_num, dec_val in KANNADA_WORD_NUMBERS.items():
        # Word boundary pattern
        if re.search(rf"(?<![\w\u0C80-\u0CFF]){re.escape(word_num)}(?![\w\u0C80-\u0CFF])", clean_text):
            if detected_unit is not None:
                total_acres = _convert_to_acres(dec_val, detected_unit)
                return _create_normalized_result(
                    utterance=clean_text,
                    original_value=dec_val,
                    original_unit=detected_unit,
                    total_acres=total_acres,
                    metadata={"word_number": word_num},
                )
            else:
                # Number found but unit missing -> Ambiguous!
                return NormalizedLandArea(
                    original_utterance=clean_text,
                    original_value=dec_val,
                    original_unit=LandUnit.ACRE,
                    canonical_acres=dec_val,
                    canonical_guntas=dec_val * ACRE_TO_GUNTA,
                    canonical_hectares=dec_val * ACRE_TO_HECTARE,
                    is_ambiguous=True,
                    clarification_prompt="ದಯವಿಟ್ಟು ನಿಮ್ಮ ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ ಎಕರೆ, ಗುಂಟೆ ಅಥವಾ ಹೆಕ್ಟೇರ್‌ನಲ್ಲಿದೆಯೇ ಎಂದು ತಿಳಿಸಿ.",
                )

    # 4. Check for standard numeric digits (e.g., "2.5 ಎಕರೆ", "4 acres", "100 guntas", "3.2 hectare")
    digit_match = re.search(r"(\d+(?:\.\d+)?)\s*(ಎಕರೆ|ಎಕ್ರೆ|ಗುಂಟೆ|ಹೆಕ್ಟೇರ್|hectare|acre|gunta)?", clean_text, re.IGNORECASE)
    if digit_match:
        num_str = digit_match.group(1)
        raw_unit_str = digit_match.group(2)
        try:
            val = Decimal(num_str)
        except Exception:
            return None

        unit = _detect_unit(raw_unit_str) if raw_unit_str else detected_unit
        if unit is None:
            # Ambiguous: farmer gave a bare number (e.g. "ನನ್ನ ಬಳಿ 5 ಇದೆ")
            return NormalizedLandArea(
                original_utterance=clean_text,
                original_value=val,
                original_unit=LandUnit.ACRE,
                canonical_acres=val,
                canonical_guntas=val * ACRE_TO_GUNTA,
                canonical_hectares=val * ACRE_TO_HECTARE,
                is_ambiguous=True,
                clarification_prompt="ದಯವಿಟ್ಟು ನಿಮ್ಮ ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ ಎಕರೆ, ಗುಂಟೆ ಅಥವಾ ಹೆಕ್ಟೇರ್‌ನಲ್ಲಿದೆಯೇ ಎಂದು ತಿಳಿಸಿ.",
            )

        total_acres = _convert_to_acres(val, unit)
        return _create_normalized_result(
            utterance=clean_text,
            original_value=val,
            original_unit=unit,
            total_acres=total_acres,
            metadata={"numeric_pattern": num_str},
        )

    return None


def _convert_to_acres(value: Decimal, unit: LandUnit) -> Decimal:
    """Convert input unit value to standard acres using Decimal."""
    if unit == LandUnit.ACRE:
        return value
    if unit == LandUnit.GUNTA:
        return value * GUNTA_TO_ACRE
    if unit == LandUnit.HECTARE:
        return value * HECTARE_TO_ACRE
    return value


def _create_normalized_result(
    utterance: str,
    original_value: Decimal,
    original_unit: LandUnit,
    total_acres: Decimal,
    metadata: Dict[str, Any],
) -> NormalizedLandArea:
    """Assemble the precision Decimal NormalizedLandArea result."""
    # Round canonical values to 4 decimal places for reporting, while keeping precise math
    acres_rounded = total_acres.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    guntas_rounded = (total_acres * ACRE_TO_GUNTA).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    hectares_rounded = (total_acres * ACRE_TO_HECTARE).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    meta = {
        **metadata,
        "raw_acres_exact": str(total_acres),
        "formula_used": f"{original_value} {original_unit.value} -> {acres_rounded} ACRES",
    }

    return NormalizedLandArea(
        original_utterance=utterance,
        original_value=original_value,
        original_unit=original_unit,
        canonical_acres=acres_rounded,
        canonical_guntas=guntas_rounded,
        canonical_hectares=hectares_rounded,
        is_ambiguous=False,
        clarification_prompt=None,
        conversion_metadata=meta,
    )
