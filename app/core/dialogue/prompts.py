"""Conversational Kannada prompt selection and grounded response generation.

Conforms to Directive M3.7, 06_DIALOGUE_AND_MEMORY.md Section 6, and 15_IMPLEMENTATION_PLAN.md.
Rules:
1. One piece of missing information at a time.
2. Short, natural, respectful Kannada.
3. Reflects known context and explains clarifications.
4. Non-negotiable invariant: NEVER hallucinate scheme amounts, deadlines, or entitlement approvals.
"""

from typing import Dict, List, Optional
from app.core.dialogue.state_machine import DialogueState
from app.core.profile.schemas import AgriculturalProfile
from app.schemas.extraction import Intent


# Natural Kannada question prompts for individual missing slots
SLOT_QUESTIONS: Dict[str, str] = {
    "district": "ನಿಮ್ಮ ಕೃಷಿ ಜಮೀನು ಯಾವ ಜಿಲ್ಲೆಯಲ್ಲಿದೆ ಎಂದು ದಯವಿಟ್ಟು ತಿಳಿಸಿ.",
    "taluk": "ನಿಮ್ಮ ತಾಲೂಕು ಯಾವುದು ಎಂದು ತಿಳಿಸಿ.",
    "crop": "ನೀವು ಯಾವ ಬೆಳೆ ಬೆಳೆಯುತ್ತಿದ್ದೀರಿ ಅಥವಾ ಬೆಳೆಯಲು ಯೋಜಿಸಿದ್ದೀರಿ?",
    "land_area": "ನಿಮ್ಮ ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ ಎಷ್ಟು ಎಕರೆ ಅಥವಾ ಗುಂಟೆ ಇದೆ ಎಂದು ತಿಳಿಸಿ.",
    "land_ownership": "ಜಮೀನು ನಿಮ್ಮ ಸ್ವಂತ ಹೆಸರಿನಲ್ಲಿದೆಯೇ, ಜಂಟಿ ಖಾತೆಯಲ್ಲಿದೆಯೇ ಅಥವಾ ಗೇಣಿ/ಗುತ್ತಿಗೆಗೆ ಮಾಡುತ್ತಿದ್ದೀರಾ?",
    "irrigation": "ನಿಮ್ಮ ಜಮೀನಿಗೆ ಯಾವ ರೀತಿಯ ನೀರಾವರಿ ಸೌಲಭ್ಯವಿದೆ? (ಉದಾ: ಹನಿ ನೀರಾವರಿ, ಬೋರ್‌ವೆಲ್ ಅಥವಾ ಕಾಲುವೆ)",
    "season": "ಇದು ಯಾವ ಹಂಗಾಮಿನ ಬೆಳೆ? ಮುಂಗಾರು, ಹಿಂಗಾರು ಅಥವಾ ಬೇಸಿಗೆ?",
    "equipment": "ಯಾವ ಕೃಷಿ ಯಂತ್ರೋಪಕರಣದ ಸಹಾಯಧನಕ್ಕಾಗಿ ಹುಡುಕುತ್ತಿದ್ದೀರಿ? (ಉದಾ: ಟ್ರಾಕ್ಟರ್, ರೊಟಾವೇಟರ್)",
    "soil_improvement": "ಯಾವ ರೀತಿಯ ಮಣ್ಣು ಸುಧಾರಣೆ ಅಥವಾ ಗೊಬ್ಬರದ ನೆರವು ನಿಮಗೆ ಬೇಕಾಗಿದೆ?",
    "assistance_need": "ಸರ್ಕಾರದಿಂದ ನಿಮಗೆ ಯಾವ ರೀತಿಯ ಕೃಷಿ ನೆರವು ಬೇಕಾಗಿದೆ? (ಸಹಾಯಧನ, ಸಾಲ ಅಥವಾ ಬೆಳೆ ವಿಮೆ)",
}


# Kannada slot display names for confirmation prompts
SLOT_DISPLAY_NAMES: Dict[str, str] = {
    "district": "ಜಿಲ್ಲೆ",
    "taluk": "ತಾಲೂಕು",
    "crop": "ಮುಖ್ಯ ಬೆಳೆ",
    "land_area": "ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ",
    "land_ownership": "ಜಮೀನಿನ ಮಾಲೀಕತ್ವ",
    "irrigation": "ನೀರಾವರಿ ಸೌಲಭ್ಯ",
    "season": "ಕೃಷಿ ಹಂಗಾಮು",
    "equipment": "ಯಂತ್ರೋಪಕರಣ",
    "soil_improvement": "ಮಣ್ಣು ಸುಧಾರಣೆ",
}


def build_confirmation_prompt(slot_key: str, profile: AgriculturalProfile) -> str:
    """Build a respectful read-back confirmation prompt for a critical slot."""
    slot_label = SLOT_DISPLAY_NAMES.get(slot_key, slot_key)
    val_str = ""

    if slot_key == "land_area" and profile.land_area:
        val_str = f"{profile.land_area.canonical_acres} ಎಕರೆ"
    elif slot_key == "land_ownership" and profile.ownership:
        val_str = profile.ownership.kannada_description
    elif slot_key == "district" and profile.district:
        val_str = profile.district.kannada_name
    elif slot_key == "crop" and profile.primary_crop:
        val_str = profile.primary_crop.kannada_name
    elif slot_key == "irrigation" and profile.irrigation_type:
        val_str = profile.irrigation_type.kannada_name
    elif slot_key == "season" and profile.season:
        val_str = profile.season.kannada_name
    else:
        val_str = "ವಿವರ"

    return f"ನೀವು {slot_label} '{val_str}' ಎಂದು ತಿಳಿಸಿದ್ದೀರಿ. ಇದು ಸರಿಯೇ?"


def generate_dialogue_response(
    state: DialogueState,
    intent: Intent,
    profile: AgriculturalProfile,
    next_missing_slot: Optional[str] = None,
    pending_confirmation_slot: Optional[str] = None,
) -> str:
    """Generate grounded, context-aware native Kannada conversational response text."""

    # 1. Geographic or cross-field contradictions take immediate precedence
    if profile.conflicts:
        return f"ಕ್ಷಮಿಸಿ, {profile.conflicts[0]}. ದಯವಿಟ್ಟು ಸರಿಯಾದ ಮಾಹಿತಿ ತಿಳಿಸಿ."

    # 2. Ambiguity resolution
    if state == DialogueState.CLARIFYING:
        if profile.land_area and profile.land_area.is_ambiguous and profile.land_area.clarification_prompt:
            return profile.land_area.clarification_prompt
        return "ದಯವಿಟ್ಟು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಇನ್ನೊಮ್ಮೆ ಸ್ಪಷ್ಟವಾಗಿ ತಿಳಿಸಿ."

    # 3. Confirmation state
    if state == DialogueState.CONFIRMING:
        slot_to_confirm = pending_confirmation_slot or "land_ownership"
        return build_confirmation_prompt(slot_to_confirm, profile)

    # 4. Evaluation Ready state
    if state == DialogueState.EVALUATION_READY:
        return (
            "ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಎಲ್ಲ ಅಗತ್ಯ ಕೃಷಿ ವಿವರಗಳನ್ನು ಸಂಗ್ರಹಿಸಲಾಗಿದೆ. "
            "ನಿಮ್ಮ ಯೋಜನೆಗಳ ಅರ್ಹತೆ ಪರಿಶೀಲನೆಗೆ ವಿವರಗಳು ಸಿದ್ಧವಾಗಿವೆ."
        )

    # 5. Completed state
    if state == DialogueState.COMPLETED:
        return "ಧನ್ಯವಾದಗಳು. ಕೃಷಿ ಮಿತ್ರ ಸಂಭಾಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ. ಹೆಚ್ಚಿನ ಮಾಹಿತಿಗಾಗಿ ಮತ್ತೆ ಸಂಪರ್ಕಿಸಿ."

    # 6. Paused state
    if state == DialogueState.PAUSED:
        return "ಸಂಭಾಷಣೆಯನ್ನು ತಾತ್ಕಾಲಿಕವಾಗಿ ನಿಲ್ಲಿಸಲಾಗಿದೆ. ನೀವು ಯಾವುದೇ ಸಮಯದಲ್ಲಿ ಇದನ್ನು ಮುಂದುವರಿಸಬಹುದು."

    # 7. Slot collection state: Ask for exactly one missing slot
    if state == DialogueState.COLLECTING_SLOTS:
        if next_missing_slot and next_missing_slot in SLOT_QUESTIONS:
            return SLOT_QUESTIONS[next_missing_slot]
        return "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹೆಚ್ಚಿನ ಕೃಷಿ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ."

    # 8. Greeting state
    if state == DialogueState.GREETING:
        return (
            "ನಮಸ್ಕಾರ, ಕೃಷಿ ಮಿತ್ರ ಸಹಾಯವಾಣಿಗೆ ಸ್ವಾಗತ. "
            "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಮಾಹಿತಿ ಪಡೆಯಲು ನಿಮ್ಮ ಬೆಳೆ, ಜಿಲ್ಲೆ ಅಥವಾ ಸಹಾಯದ ಅಗತ್ಯವನ್ನು ತಿಳಿಸಿ."
        )

    # 9. Responding fallback
    return "ನಿಮ್ಮ ಕೃಷಿ ವಿವರಗಳನ್ನು ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ಮುಂದಿನ ವಿವರ ತಿಳಿಸಿ."
