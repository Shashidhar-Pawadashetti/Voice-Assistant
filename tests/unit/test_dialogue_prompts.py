"""Unit tests for dialogue prompt selection and response generation."""

from decimal import Decimal
import pytest

from app.core.dialogue.prompts import (
    build_confirmation_prompt,
    generate_dialogue_response,
)
from app.core.dialogue.state_machine import DialogueState
from app.core.normalization.land_area import LandUnit, NormalizedLandArea
from app.core.normalization.location import DistrictInfo
from app.core.profile.schemas import AgriculturalProfile
from app.schemas.extraction import Intent


def test_slot_question_generation():
    profile = AgriculturalProfile()
    resp = generate_dialogue_response(
        state=DialogueState.COLLECTING_SLOTS,
        intent=Intent.FIND_SCHEMES,
        profile=profile,
        next_missing_slot="district",
    )
    assert "ಜಿಲ್ಲೆ" in resp


def test_conflict_takes_precedence_in_response():
    profile = AgriculturalProfile(
        conflicts=["ತಾಲೂಕು 'ಅಥಣಿ' ಜಿಲ್ಲೆ 'ಮಂಡ್ಯ' ವ್ಯಾಪ್ತಿಗೆ ಬರುವುದಿಲ್ಲ"]
    )
    resp = generate_dialogue_response(
        state=DialogueState.COLLECTING_SLOTS,
        intent=Intent.FIND_SCHEMES,
        profile=profile,
    )
    assert "ಕ್ಷಮಿಸಿ" in resp
    assert "ಅಥಣಿ" in resp


def test_confirmation_prompt_formatting():
    profile = AgriculturalProfile(
        land_area=NormalizedLandArea(
            original_utterance="3.5 ಎಕರೆ",
            original_value=Decimal("3.5"),
            original_unit=LandUnit.ACRE,
            canonical_acres=Decimal("3.5000"),
            canonical_guntas=Decimal("140.00"),
            canonical_hectares=Decimal("1.4164"),
        )
    )
    prompt = build_confirmation_prompt("land_area", profile)
    assert "3.5000 ಎಕರೆ" in prompt
    assert "ಸರಿಯೇ" in prompt


def test_evaluation_ready_response():
    profile = AgriculturalProfile()
    resp = generate_dialogue_response(
        state=DialogueState.EVALUATION_READY,
        intent=Intent.INCOME_SUPPORT,
        profile=profile,
    )
    assert "ಧನ್ಯವಾದಗಳು" in resp
    assert "ಸಿದ್ಧವಾಗಿವೆ" in resp
