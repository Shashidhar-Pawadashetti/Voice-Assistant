"""Kannada ASR evaluation benchmarks: Character Error Rate (CER) and Word Error Rate (WER)."""

from typing import List, Tuple
import jiwer
import pytest


# Reviewed Kannada reference evaluation dataset
KANNADA_EVALUATION_DATASET: List[Tuple[str, str, str]] = [
    (
        "utt_001_dharwad_sorghum",
        "ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು",
        "North Karnataka dialect query for sorghum subsidy in Dharwad",
    ),
    (
        "utt_002_mandya_drip",
        "ನನಗೆ ಎರಡು ಎಕರೆ ಜಮೀನಿದೆ ಹನಿ ನೀರಾವರಿ ಸಬ್ಸಿಡಿ ಬೇಕಾಗಿದೆ",
        "Southern Karnataka query for drip irrigation on 2 acres",
    ),
    (
        "utt_003_kalaburagi_pigeonpea",
        "ಕಲಬುರಗಿ ತಾಲೂಕು ತೊಗರಿ ಬೆಳೆ ಬರ ಪರಿಹಾರ ಯೋಜನೆ",
        "Kalyana Karnataka query for pigeon pea drought relief in Kalaburagi",
    ),
    (
        "utt_004_codemixed_insurance",
        "ಬೆಳೆ ಇನ್ಶೂರೆನ್ಸ್ ಸ್ಟೇಟಸ್ ಚೆಕ್ ಮಾಡಬೇಕು",
        "Code-mixed Kannada-English query for crop insurance status",
    ),
]


def compute_transcription_metrics(
    reference: str,
    hypothesis: str,
) -> dict[str, float]:
    """Compute CER and WER between reference and hypothesis transcripts."""
    # Standardize whitespace
    ref_norm = " ".join(reference.strip().split())
    hyp_norm = " ".join(hypothesis.strip().split())

    wer = jiwer.wer(ref_norm, hyp_norm)
    cer = jiwer.cer(ref_norm, hyp_norm)

    return {"wer": round(wer, 4), "cer": round(cer, 4)}


def test_evaluation_exact_match():
    """Identical reference and hypothesis must yield 0.0 WER and 0.0 CER."""
    for _sample_id, reference, _desc in KANNADA_EVALUATION_DATASET:
        metrics = compute_transcription_metrics(reference, reference)
        assert metrics["wer"] == 0.0
        assert metrics["cer"] == 0.0


def test_evaluation_single_word_substitution():
    """Single word substitution in 5-word sentence produces expected WER."""
    reference = "ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು"
    # One word changed ("ಜೋಳ" -> "ರಾಗಿ")
    hypothesis = "ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ರಾಗಿ ಬೆಳೆಯಲು ಸಹಾಯಧನ ಬೇಕು"

    metrics = compute_transcription_metrics(reference, hypothesis)
    # 1 word error in 6 words ~ 0.1667 WER
    assert 0.10 <= metrics["wer"] <= 0.20
    # CER should be small (1-2 character changes out of ~40 chars)
    assert 0.01 <= metrics["cer"] <= 0.10


def test_evaluation_code_mixed_tolerance():
    reference = "ಬೆಳೆ ಇನ್ಶೂರೆನ್ಸ್ ಸ್ಟೇಟಸ್ ಚೆಕ್ ಮಾಡಬೇಕು"
    # Transcribed with slight English phonetic spelling variation
    hypothesis = "ಬೆಳೆ ಇನ್ಶುರೆನ್ಸ್ ಸ್ಟೇಟಸ್ ಚೆಕ್ ಮಾಡಬೇಕು"

    metrics = compute_transcription_metrics(reference, hypothesis)
    assert metrics["wer"] <= 0.25
    assert metrics["cer"] <= 0.05
