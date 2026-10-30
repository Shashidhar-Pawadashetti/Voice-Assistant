"""Unit tests for natural Kannada spoken corrections and negation detection."""

import pytest

from app.core.normalization.corrections import detect_correction


def test_correction_alla_pattern():
    # 'ನಾಲ್ಕು ಎಕರೆ ಅಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ'
    res = detect_correction("ನಾಲ್ಕು ಎಕರೆ ಅಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ")
    assert res.is_correction is True
    assert res.negated_part == "ನಾಲ್ಕು ಎಕರೆ"
    assert res.corrected_part == "ಮೂರೂವರೆ ಎಕರೆ"

    # 'ಧಾರವಾಡ ಅಲ್ಲ ಗದಗ'
    res2 = detect_correction("ಧಾರವಾಡ ಅಲ್ಲ ಗದಗ")
    assert res2.is_correction is True
    assert res2.negated_part == "ಧಾರವಾಡ"
    assert res2.corrected_part == "ಗದಗ"


def test_correction_tappu_pattern():
    # 'ತಪ್ಪಾಯಿತು, ಬೆಳೆ ರಾಗಿ'
    res = detect_correction("ತಪ್ಪಾಯಿತು, ಬೆಳೆ ರಾಗಿ")
    assert res.is_correction is True
    assert "ರಾಗಿ" in res.corrected_part


def test_correction_badalagi_pattern():
    # 'ಜೋಳ ಬದಲಾಗಿ ತೊಗರಿ'
    res = detect_correction("ಜೋಳ ಬದಲಾಗಿ ತೊಗರಿ")
    assert res.is_correction is True
    assert res.negated_part == "ಜೋಳ"
    assert "ತೊಗರಿ" in res.corrected_part


def test_correction_illa_pattern():
    # 'ಇಲ್ಲ, 5 ಎಕರೆ'
    res = detect_correction("ಇಲ್ಲ, 5 ಎಕರೆ")
    assert res.is_correction is True
    assert "5 ಎಕರೆ" in res.corrected_part


def test_non_correction_utterances():
    res1 = detect_correction("ನನಗೆ ಎರಡು ಎಕರೆ ಜಮೀನಿದೆ")
    assert res1.is_correction is False

    res2 = detect_correction("ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು")
    assert res2.is_correction is False
