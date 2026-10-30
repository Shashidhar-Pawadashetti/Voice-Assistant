"""Unit tests for dialogue confirmation, rejection, and spoken correction routing."""

import pytest
from app.core.dialogue.confirmation import ConfirmationDecision, analyze_confirmation


def test_affirmative_confirmations():
    for word in ["ಹೌದು", "ಸರಿ", "ಖಚಿತ", "ಹೌದ್ರಿ", "ಹೌದು ಸರಿ", "yes", "correct", "right"]:
        res = analyze_confirmation(word)
        assert res.decision == ConfirmationDecision.AFFIRMED, f"Failed on affirmative '{word}'"


def test_negative_rejections():
    for word in ["ಇಲ್ಲ", "ತಪ್ಪು", "ತಪ್ಪಾಗಿದೆ", "no", "wrong"]:
        res = analyze_confirmation(word)
        assert res.decision == ConfirmationDecision.REJECTED, f"Failed on negative '{word}'"


def test_correction_during_confirmation():
    # Negation with replacement value
    res = analyze_confirmation("ನಾಲ್ಕು ಎಕರೆ ಅಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ")
    assert res.decision == ConfirmationDecision.CORRECTED
    assert "ಮೂರೂವರೆ" in res.corrected_part

    # Negative followed by replacement words
    res2 = analyze_confirmation("ಇಲ್ಲ ಮೂರು ಎಕರೆ")
    assert res2.decision == ConfirmationDecision.CORRECTED


def test_unclear_confirmation():
    assert analyze_confirmation("").decision == ConfirmationDecision.UNCLEAR
    assert analyze_confirmation("ಗೊತ್ತಿಲ್ಲ").decision == ConfirmationDecision.UNCLEAR
