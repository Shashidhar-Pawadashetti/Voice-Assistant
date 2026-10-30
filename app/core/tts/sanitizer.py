"""Text preprocessing, sanitization, and number pronunciation expansion for Kannada TTS."""

import re
from typing import Dict


# Kannada digit mappings
KANNADA_DIGIT_MAP: Dict[str, str] = {
    "೦": "0",
    "೧": "1",
    "೨": "2",
    "೩": "3",
    "೪": "4",
    "೫": "5",
    "೬": "6",
    "೭": "7",
    "೮": "8",
    "೯": "9",
}

# Spoken number expansions for single digits and small numbers in Kannada
NUMBER_SPOKEN_MAP: Dict[str, str] = {
    "0": "ಸೊನ್ನೆ",
    "1": "ಒಂದು",
    "2": "ಎರಡು",
    "3": "ಮೂರು",
    "4": "ನಾಲ್ಕು",
    "5": "ಐದು",
    "6": "ಆರು",
    "7": "ಏಳು",
    "8": "ಎಂಟು",
    "9": "ಒಂಬತ್ತು",
    "10": "ಹತ್ತು",
    "20": "ಇಪ್ಪತ್ತು",
    "50": "ಐವತ್ತು",
    "100": "ನೂರು",
    "1000": "ಸಾವಿರ",
    "2000": "ಎರಡು ಸಾವಿರ",
    "6000": "ಆರು ಸಾವಿರ",
}

# Common agricultural terminology pronunciation normalizations
AGRI_PRONUNCIATION_MAP: Dict[str, str] = {
    "PM-KISAN": "ಪಿಎಂ ಕಿಸಾನ್",
    "PMKISAN": "ಪಿಎಂ ಕಿಸಾನ್",
    "PMFBY": "ಪಿಎಂ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ",
    "KCC": "ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್",
    "FID": "ರೈತರ ಐಡಿ",
}

HTML_TAG_REGEX = re.compile(r"<[^>]+>")
UNSAFE_CHAR_REGEX = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def sanitize_tts_text(text: str, max_chars: int = 1000) -> str:
    """Sanitize input text for safe TTS synthesis.

    Strips HTML tags, control characters, truncates excessive length,
    and replaces known Latin scheme acronyms with Kannada phonetic equivalents.
    """
    if not text:
        return ""

    # Strip HTML tags
    cleaned = HTML_TAG_REGEX.sub(" ", text)

    # Strip control characters
    cleaned = UNSAFE_CHAR_REGEX.sub("", cleaned)

    # Replace known acronyms
    for acronym, kn_expansion in AGRI_PRONUNCIATION_MAP.items():
        cleaned = re.sub(rf"\b{re.escape(acronym)}\b", kn_expansion, cleaned, flags=re.IGNORECASE)

    # Convert Kannada native numeral characters (೦-೯) to standard digits
    for kn_char, digit in KANNADA_DIGIT_MAP.items():
        cleaned = cleaned.replace(kn_char, digit)

    # Normalize standalone digits (e.g., '2 ಎಕರೆ' -> 'ಎರಡು ಎಕರೆ')
    cleaned = re.sub(r"\b\d+\b", lambda m: NUMBER_SPOKEN_MAP.get(m.group(0), m.group(0)), cleaned)

    # Normalize excessive whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Bounded character length
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip()

    return cleaned
