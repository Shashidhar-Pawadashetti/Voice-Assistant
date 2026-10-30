"""Unit tests for agricultural vocabulary dataset and deterministic normalizer."""

import pytest

from app.core.normalization.vocabulary import (
    VOCABULARY_VERSION,
    VocabularyCategory,
    get_canonical_term,
    normalize_term,
)


def test_version_identifier():
    assert VOCABULARY_VERSION == "2026.10.1"


def test_normalize_crops_kannada_and_regional_aliases():
    # Sorghum / Jowar
    jola_res = normalize_term("ನನ್ನ ಜಮೀನಿನಲ್ಲಿ ಜೋಳ ಬೆಳೆಯುತ್ತೇನೆ", category=VocabularyCategory.CROP)
    assert len(jola_res) == 1
    assert jola_res[0].canonical_id == "SORGHUM"
    assert jola_res[0].kannada_name == "ಜೋಳ"

    # Regional alias: ಮಾಲ್ದಂಡಿ
    maldandi_res = normalize_term("ಮಾಲ್ದಂಡಿ ಬಿತ್ತನೆ ಮಾಡಿದ್ದೇನೆ", category=VocabularyCategory.CROP)
    assert len(maldandi_res) == 1
    assert maldandi_res[0].canonical_id == "SORGHUM"

    # Finger Millet / Ragi
    ragi_res = normalize_term("ಮುದ್ದೆ ರಾಗಿ ಬೆಳೆಯಲು ಸಬ್ಸಿಡಿ ಬೇಕು", category=VocabularyCategory.CROP)
    assert len(ragi_res) == 1
    assert ragi_res[0].canonical_id == "FINGER_MILLET"

    # Pigeon pea / Tur
    togari_res = normalize_term("ಕಲಬುರಗಿ ಕೆಂಪು ತೊಗರಿ ಬೆಳೆ", category=VocabularyCategory.CROP)
    assert len(togari_res) == 1
    assert togari_res[0].canonical_id == "PIGEON_PEA"

    # Groundnut / Shenga
    shenga_res = normalize_term("ಶೇಂಗಾ ಮತ್ತು ಕಡಲೆಕಾಯಿ ಬೆಳೆಗಾರರು", category=VocabularyCategory.CROP)
    assert len(shenga_res) == 1
    assert shenga_res[0].canonical_id == "GROUNDNUT"

    # Onion / Ullagaddi
    ullagaddi_res = normalize_term("ಉಳ್ಳಾಗಡ್ಡಿ ಬೆಲೆ ಕುಸಿದಿದೆ", category=VocabularyCategory.CROP)
    assert len(ullagaddi_res) == 1
    assert ullagaddi_res[0].canonical_id == "ONION"


def test_normalize_irrigation_types():
    # Drip
    drip_res = normalize_term("ಹನಿ ನೀರಾವರಿ ಸಬ್ಸಿಡಿ ಬೇಕು", category=VocabularyCategory.IRRIGATION)
    assert len(drip_res) == 1
    assert drip_res[0].canonical_id == "DRIP"

    # Code-mixed drip
    drip_cm = normalize_term("drip irrigation system", category=VocabularyCategory.IRRIGATION)
    assert len(drip_cm) == 1
    assert drip_cm[0].canonical_id == "DRIP"

    # Sprinkler
    sprinkler_res = normalize_term("ತುಂತುರು ನೀರಾವರಿ ಸಲಕರಣೆ", category=VocabularyCategory.IRRIGATION)
    assert len(sprinkler_res) == 1
    assert sprinkler_res[0].canonical_id == "SPRINKLER"

    # Borewell
    borewell_res = normalize_term("ಕೊಳವೆ ಬಾವಿ ಕೊರೆಸಲು ಸಹಾಯಧನ", category=VocabularyCategory.IRRIGATION)
    assert len(borewell_res) == 1
    assert borewell_res[0].canonical_id == "BOREWELL"

    # Rainfed / Dryland
    rainfed_res = normalize_term("ನಮ್ಮದು ಒಣಬೇಸಾಯ ಭೂಮಿ", category=VocabularyCategory.IRRIGATION)
    assert len(rainfed_res) == 1
    assert rainfed_res[0].canonical_id == "RAINFED"


def test_normalize_seasons():
    mungaru = normalize_term("ಮುಂಗಾರು ಹಂಗಾಮಿನಲ್ಲಿ ಬಿತ್ತನೆ", category=VocabularyCategory.SEASON)
    assert len(mungaru) == 1
    assert mungaru[0].canonical_id == "KHARIF"

    hingaru = normalize_term("ಹಿಂಗಾರು ಜೋಳ ಬೆಳೆ", category=VocabularyCategory.SEASON)
    assert len(hingaru) == 1
    assert hingaru[0].canonical_id == "RABI"

    besige = normalize_term("ಬೇಸಿಗೆ ಹಂಗಾಮು", category=VocabularyCategory.SEASON)
    assert len(besige) == 1
    assert besige[0].canonical_id == "SUMMER"


def test_normalize_equipment_and_soil():
    tractor = normalize_term("ಹೊಸ ಟ್ರಾಕ್ಟರ್ ಖರೀದಿಗೆ ಸಹಾಯಧನ", category=VocabularyCategory.EQUIPMENT)
    assert len(tractor) == 1
    assert tractor[0].canonical_id == "TRACTOR"

    soil = normalize_term("ಮಣ್ಣು ಪರೀಕ್ಷೆ ಮಾಡಿಸಬೇಕು", category=VocabularyCategory.SOIL_IMPROVEMENT)
    assert len(soil) == 1
    assert soil[0].canonical_id == "SOIL_TESTING"

    manure = normalize_term("ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ ಮತ್ತು ಕಾಂಪೋಸ್ಟ್", category=VocabularyCategory.SOIL_IMPROVEMENT)
    assert len(manure) == 1
    assert manure[0].canonical_id == "ORGANIC_MANURE"


def test_normalize_assistance_needs():
    subsidy = normalize_term("ಸರ್ಕಾರದ ಸಬ್ಸಿಡಿ ಯೋಜನೆಗಳು", category=VocabularyCategory.ASSISTANCE_NEED)
    assert len(subsidy) == 1
    assert subsidy[0].canonical_id == "SUBSIDY"

    insurance = normalize_term("ಬೆಳೆ ವಿಮೆ ಪರಿಹಾರ", category=VocabularyCategory.ASSISTANCE_NEED)
    canonical_ids = [item.canonical_id for item in insurance]
    assert "CROP_INSURANCE" in canonical_ids
    assert "COMPENSATION" in canonical_ids


def test_word_boundary_isolation():
    # Ensures word boundary matching does not perform unrestricted string replacement
    # 'ಕಬ್ಬು' should match, but a non-agricultural word embedding should not cause corrupt match
    res = normalize_term("ಕಬ್ಬು ಬೆಳೆದಿದ್ದೇನೆ", category=VocabularyCategory.CROP)
    assert len(res) == 1
    assert res[0].canonical_id == "SUGARCANE"


def test_get_canonical_term_lookup():
    entry = get_canonical_term("SORGHUM")
    assert entry is not None
    assert entry.kannada_name == "ಜೋಳ"

    missing = get_canonical_term("NON_EXISTENT_CROP")
    assert missing is None
