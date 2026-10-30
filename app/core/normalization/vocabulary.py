"""Versioned Kannada agricultural vocabulary dataset and deterministic normalizer.

Conforms to 02_PRODUCT_REQUIREMENTS.md Section 3 and 05_VOICE_AI_PIPELINE.md Section 4.
Datasets are versioned and maintain canonical codes, native Kannada spellings,
regional aliases, and code-mixed transliterations.
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


VOCABULARY_VERSION = "2026.10.1"


class VocabularyCategory(str, Enum):
    """Agricultural vocabulary categories."""

    CROP = "CROP"
    IRRIGATION = "IRRIGATION"
    SEASON = "SEASON"
    EQUIPMENT = "EQUIPMENT"
    SOIL_IMPROVEMENT = "SOIL_IMPROVEMENT"
    ASSISTANCE_NEED = "ASSISTANCE_NEED"


class NormalizedTerm(BaseModel):
    """Structured representation of a normalized agricultural concept."""

    canonical_id: str = Field(description="Stable canonical code (e.g. SORGHUM, DRIP, KHARIF)")
    category: VocabularyCategory = Field(description="Domain category")
    kannada_name: str = Field(description="Primary native Kannada display name")
    english_name: str = Field(description="Standard English name")
    matched_alias: str = Field(description="The exact spoken phrase or alias that triggered the match")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Match confidence score")
    version: str = Field(default=VOCABULARY_VERSION, description="Vocabulary dataset version")


@dataclass(frozen=True)
class VocabularyEntry:
    canonical_id: str
    category: VocabularyCategory
    kannada_name: str
    english_name: str
    aliases: Tuple[str, ...]


# Curated agricultural reference datasets
AGRICULTURAL_VOCABULARY: List[VocabularyEntry] = [
    # Crops
    VocabularyEntry(
        canonical_id="SORGHUM",
        category=VocabularyCategory.CROP,
        kannada_name="ಜೋಳ",
        english_name="Sorghum / Jowar",
        aliases=(
            "ಜೋಳದ ಬೆಳೆ",
            "ಜೋಳದ",
            "ಜೋಳ",
            "ಬಿಳಿ ಜೋಳ",
            "ಮಾಲ್ದಂಡಿ",
            "ಕೆಂಪು ಜೋಳ",
            "ಬೆಳ್ಳ ಜೋಳ",
            "jowar",
            "sorghum",
            "jola",
        ),
    ),
    VocabularyEntry(
        canonical_id="FINGER_MILLET",
        category=VocabularyCategory.CROP,
        kannada_name="ರಾಗಿ",
        english_name="Finger Millet / Ragi",
        aliases=(
            "ರಾಗಿಯ ಬೆಳೆ",
            "ರಾಗಿಯ",
            "ರಾಗಿ",
            "ಮುದ್ದೆ ರಾಗಿ",
            "ಕೆಂಪು ರಾಗಿ",
            "ಬೆರಕೆ ರಾಗಿ",
            "ragi",
            "finger millet",
        ),
    ),
    VocabularyEntry(
        canonical_id="PIGEON_PEA",
        category=VocabularyCategory.CROP,
        kannada_name="ತೊಗರಿ",
        english_name="Pigeon Pea / Red Gram / Tur",
        aliases=(
            "ತೊಗರಿಯ ಬೆಳೆ",
            "ತೊಗರಿಯ",
            "ತೊಗರಿ ಬೆಳೆ",
            "ತೊಗರಿ",
            "ತೊಗರಿ ಬೇಳೆ",
            "ಕೆಂಪು ತೊಗರಿ",
            "ತುರ್",
            "ತೂರ್ ದಾಲ್",
            "tur",
            "toor",
            "pigeon pea",
            "red gram",
            "thogari",
        ),
    ),
    VocabularyEntry(
        canonical_id="PADDY",
        category=VocabularyCategory.CROP,
        kannada_name="ಭತ್ತ",
        english_name="Paddy / Rice",
        aliases=(
            "ಭತ್ತದ ಬೆಳೆ",
            "ಭತ್ತದ",
            "ಭತ್ತ ಬೆಳೆ",
            "ಭತ್ತ",
            "ನೆಲ್ಲು",
            "ಅಕ್ಕಿ",
            "ಬತ್ತ",
            "paddy",
            "rice",
            "bhatta",
        ),
    ),
    VocabularyEntry(
        canonical_id="COTTON",
        category=VocabularyCategory.CROP,
        kannada_name="ಹತ್ತಿ",
        english_name="Cotton",
        aliases=(
            "ಹತ್ತಿಯ ಬೆಳೆ",
            "ಹತ್ತಿಯ",
            "ಹತ್ತಿ ಬೆಳೆ",
            "ಹತ್ತಿ",
            "ಅರಳೆ",
            "ಕಾಟನ್",
            "ಬಿಳಿ ಬಂಗಾರ",
            "cotton",
            "hatti",
        ),
    ),
    VocabularyEntry(
        canonical_id="SUGARCANE",
        category=VocabularyCategory.CROP,
        kannada_name="ಕಬ್ಬು",
        english_name="Sugarcane",
        aliases=(
            "ಕಬ್ಬಿನ ಬೆಳೆ",
            "ಕಬ್ಬಿನ",
            "ಕಬ್ಬು ಬೆಳೆ",
            "ಕಬ್ಬು",
            "sugarcane",
            "kabbu",
        ),
    ),
    VocabularyEntry(
        canonical_id="GROUNDNUT",
        category=VocabularyCategory.CROP,
        kannada_name="ಶೇಂಗಾ",
        english_name="Groundnut / Peanut",
        aliases=(
            "ಶೇಂಗಾ",
            "ಕಡಲೆಕಾಯಿ",
            "ನೆಲಗಡಲೆ",
            "ನೆಲಗಡಲೆಕಾಯಿ",
            "ಕಡಲೆ ಕಾಯಿ",
            "groundnut",
            "peanut",
            "shenga",
            "kadlekai",
        ),
    ),
    VocabularyEntry(
        canonical_id="MAIZE",
        category=VocabularyCategory.CROP,
        kannada_name="ಮೆಕ್ಕೆಜೋಳ",
        english_name="Maize / Corn",
        aliases=(
            "ಮೆಕ್ಕೆಜೋಳ",
            "ಮೆಕ್ಕೆ ಜೋಳ",
            "ಮುಸುಕಿನ ಜೋಳ",
            "ಮುಸುಕಿ ಜೋಳ",
            "ಕಾರ್ನ್",
            "maize",
            "corn",
            "mekkejola",
        ),
    ),
    VocabularyEntry(
        canonical_id="BENGAL_GRAM",
        category=VocabularyCategory.CROP,
        kannada_name="ಕಡಲೆ",
        english_name="Bengal Gram / Chickpea",
        aliases=(
            "ಕಡಲೆ",
            "ಕಡಲೆ ಕಾಳು",
            "ಕಡಲೆಬೇಳೆ",
            "ಚನಾ",
            "bengal gram",
            "chana",
            "chickpea",
            "kadale",
        ),
    ),
    VocabularyEntry(
        canonical_id="GREEN_GRAM",
        category=VocabularyCategory.CROP,
        kannada_name="ಹೆಸರು",
        english_name="Green Gram / Moong",
        aliases=(
            "ಹೆಸರು",
            "ಹೆಸರು ಕಾಳು",
            "ಹೆಸರುಬೇಳೆ",
            "ಮೂಂಗ್",
            "green gram",
            "moong",
            "hesaru",
        ),
    ),
    VocabularyEntry(
        canonical_id="ONION",
        category=VocabularyCategory.CROP,
        kannada_name="ಈರುಳ್ಳಿ",
        english_name="Onion",
        aliases=(
            "ಈರುಳ್ಳಿ",
            "ಉಳ್ಳಾಗಡ್ಡಿ",
            "ಉಳ್ಳೆಗಡ್ಡಿ",
            "onion",
            "eerulli",
            "ullagaddi",
        ),
    ),
    VocabularyEntry(
        canonical_id="TOMATO",
        category=VocabularyCategory.CROP,
        kannada_name="ಟೊಮೇಟೊ",
        english_name="Tomato",
        aliases=(
            "ಟೊಮೇಟೊ",
            "ಟೊಮೆಟೊ",
            "ಟೊಮಾಟೊ",
            "tomato",
        ),
    ),
    VocabularyEntry(
        canonical_id="CHILLI",
        category=VocabularyCategory.CROP,
        kannada_name="ಮೆಣಸಿನಕಾಯಿ",
        english_name="Chilli",
        aliases=(
            "ಮೆಣಸಿನಕಾಯಿ",
            "ಮೆಣಸಿನ ಕಾಯಿ",
            "ಬ್ಯಾಡಗಿ ಮೆಣಸಿನಕಾಯಿ",
            "ಖಾರದ ಪುಡಿ ಮೆಣಸಿನಕಾಯಿ",
            "chilli",
            "chili",
            "menasinakai",
        ),
    ),
    VocabularyEntry(
        canonical_id="ARECANUT",
        category=VocabularyCategory.CROP,
        kannada_name="ಅಡಿಕೆ",
        english_name="Arecanut / Betel Nut",
        aliases=(
            "ಅಡಿಕೆ",
            "ಅಡಿಕೆ ತೋಟ",
            "arecanut",
            "betelnut",
            "adike",
        ),
    ),
    VocabularyEntry(
        canonical_id="POMEGRANATE",
        category=VocabularyCategory.CROP,
        kannada_name="ದಾಳಿಂಬೆ",
        english_name="Pomegranate",
        aliases=(
            "ದಾಳಿಂಬೆ",
            "ದಾಳಿಂಬ್ರಿ",
            "pomegranate",
            "dalimbe",
        ),
    ),
    VocabularyEntry(
        canonical_id="SUNFLOWER",
        category=VocabularyCategory.CROP,
        kannada_name="ಸೂರ್ಯಕಾಂತಿ",
        english_name="Sunflower",
        aliases=(
            "ಸೂರ್ಯಕಾಂತಿ",
            "ಸೂರ್ಯ ಕಾಂತಿ",
            "sunflower",
            "suryakanthi",
        ),
    ),
    # Irrigation
    VocabularyEntry(
        canonical_id="DRIP",
        category=VocabularyCategory.IRRIGATION,
        kannada_name="ಹನಿ ನೀರಾವರಿ",
        english_name="Drip Irrigation",
        aliases=(
            "ಹನಿ ನೀರಾವರಿ",
            "ಹನಿ",
            "ಡ್ರಿಪ್",
            "ಡ್ರಿಪ್ ಇರಿಗೇಷನ್",
            "ಹನಿನೀರಾವರಿ",
            "drip",
            "drip irrigation",
        ),
    ),
    VocabularyEntry(
        canonical_id="SPRINKLER",
        category=VocabularyCategory.IRRIGATION,
        kannada_name="ತುಂತುರು ನೀರಾವರಿ",
        english_name="Sprinkler Irrigation",
        aliases=(
            "ತುಂತುರು ನೀರಾವರಿ",
            "ತುಂತುರು",
            "ಸ್ಪ್ರಿಂಕ್ಲರ್",
            "ಸ್ಪ್ರಿಂಕ್ಲರ್ ಇರಿಗೇಷನ್",
            "ತುಂತುರುನೀರಾವರಿ",
            "sprinkler",
            "sprinkler irrigation",
        ),
    ),
    VocabularyEntry(
        canonical_id="BOREWELL",
        category=VocabularyCategory.IRRIGATION,
        kannada_name="ಕೊಳವೆ ಬಾವಿ",
        english_name="Borewell",
        aliases=(
            "ಕೊಳವೆ ಬಾವಿ",
            "ಬೋರ್‌ವೆಲ್",
            "ಬೋರ್ ವೆಲ್",
            "ಬೋರ್",
            "ಕೊಳವೆಬಾವಿ",
            "borewell",
            "bore",
        ),
    ),
    VocabularyEntry(
        canonical_id="OPEN_WELL",
        category=VocabularyCategory.IRRIGATION,
        kannada_name="ತೆರೆದ ಬಾವಿ",
        english_name="Open Well",
        aliases=(
            "ತೆರೆದ ಬಾವಿ",
            "ಬಾವಿ",
            "ಬಾವಿ ನೀರು",
            "open well",
            "well",
            "baavi",
        ),
    ),
    VocabularyEntry(
        canonical_id="CANAL",
        category=VocabularyCategory.IRRIGATION,
        kannada_name="ಕಾಲುವೆ",
        english_name="Canal",
        aliases=(
            "ಕಾಲುವೆ",
            "ನಾಲಾ",
            "ಕಾಲುವೆ ನೀರು",
            "canal",
            "kaluve",
        ),
    ),
    VocabularyEntry(
        canonical_id="RAINFED",
        category=VocabularyCategory.IRRIGATION,
        kannada_name="ಮಳೆಯಾಶ್ರಿತ",
        english_name="Rainfed / Dryland",
        aliases=(
            "ಮಳೆಯಾಶ್ರಿತ",
            "ಮಳೆ ಆಶ್ರಿತ",
            "ಮಳೆ ನೀರು",
            "ಒಣಬೇಸಾಯ",
            "ಖುಷ್ಕಿ",
            "rainfed",
            "dryland",
        ),
    ),
    # Seasons
    VocabularyEntry(
        canonical_id="KHARIF",
        category=VocabularyCategory.SEASON,
        kannada_name="ಮುಂಗಾರು",
        english_name="Kharif / Monsoon",
        aliases=(
            "ಮುಂಗಾರು",
            "ಖಾರೀಫ್",
            "ಖಾರಿಫ್",
            "ಮುಂಗಾರು ಬೆಳೆ",
            "kharif",
            "monsoon",
            "mungaru",
        ),
    ),
    VocabularyEntry(
        canonical_id="RABI",
        category=VocabularyCategory.SEASON,
        kannada_name="ಹಿಂಗಾರು",
        english_name="Rabi / Winter",
        aliases=(
            "ಹಿಂಗಾರು",
            "ರಬಿ",
            "ರಬ್ಬಿ",
            "ಹಿಂಗಾರು ಬೆಳೆ",
            "rabi",
            "winter",
            "hingaru",
        ),
    ),
    VocabularyEntry(
        canonical_id="SUMMER",
        category=VocabularyCategory.SEASON,
        kannada_name="ಬೇಸಿಗೆ",
        english_name="Summer / Zaid",
        aliases=(
            "ಬೇಸಿಗೆ",
            "ಬೇಸಿಗೆ ಬೆಳೆ",
            "ಮುಂಗಾರು ಪೂರ್ವ",
            "ಜಾಯಿದ್",
            "summer",
            "zaid",
            "besige",
        ),
    ),
    # Equipment
    VocabularyEntry(
        canonical_id="TRACTOR",
        category=VocabularyCategory.EQUIPMENT,
        kannada_name="ಟ್ರಾಕ್ಟರ್",
        english_name="Tractor",
        aliases=(
            "ಟ್ರಾಕ್ಟರ್",
            "ಟ್ರ್ಯಾಕ್ಟರ್",
            "tractor",
        ),
    ),
    VocabularyEntry(
        canonical_id="POWER_TILLER",
        category=VocabularyCategory.EQUIPMENT,
        kannada_name="ಪವರ್ ಟಿಲ್ಲರ್",
        english_name="Power Tiller",
        aliases=(
            "ಪವರ್ ಟಿಲ್ಲರ್",
            "ಪವರ್‌ಟಿಲ್ಲರ್",
            "ಟಿಲ್ಲರ್",
            "power tiller",
            "tiller",
        ),
    ),
    VocabularyEntry(
        canonical_id="ROTAVATOR",
        category=VocabularyCategory.EQUIPMENT,
        kannada_name="ರೋಟವೇಟರ್",
        english_name="Rotavator",
        aliases=(
            "ರೋಟವೇಟರ್",
            "ರೋಟಾವೇಟರ್",
            "rotavator",
        ),
    ),
    VocabularyEntry(
        canonical_id="WEEDER",
        category=VocabularyCategory.EQUIPMENT,
        kannada_name="ಕಳೆ ಕೀಳುವ ಯಂತ್ರ",
        english_name="Weeder",
        aliases=(
            "ಕಳೆ ಕೀಳುವ ಯಂತ್ರ",
            "ವೀಡರ್",
            "ಕಳೆ ಯಂತ್ರ",
            "weeder",
        ),
    ),
    VocabularyEntry(
        canonical_id="DRONE",
        category=VocabularyCategory.EQUIPMENT,
        kannada_name="ಕೃಷಿ ಡ್ರೋನ್",
        english_name="Agricultural Drone",
        aliases=(
            "ಕೃಷಿ ಡ್ರೋನ್",
            "ಡ್ರೋನ್",
            "drone",
            "agri drone",
        ),
    ),
    # Soil Improvement
    VocabularyEntry(
        canonical_id="SOIL_TESTING",
        category=VocabularyCategory.SOIL_IMPROVEMENT,
        kannada_name="ಮಣ್ಣು ಪರೀಕ್ಷೆ",
        english_name="Soil Health Card / Testing",
        aliases=(
            "ಮಣ್ಣು ಪರೀಕ್ಷೆ",
            "ಮಣ್ಣಿನ ಪರೀಕ್ಷೆ",
            "ಭೂಮಿ ಪರೀಕ್ಷೆ",
            "ಮಣ್ಣು ಆರೋಗ್ಯ ಕಾರ್ಡ್",
            "soil testing",
            "soil test",
            "soil health card",
        ),
    ),
    VocabularyEntry(
        canonical_id="ORGANIC_MANURE",
        category=VocabularyCategory.SOIL_IMPROVEMENT,
        kannada_name="ಸಾವಯವ ಗೊಬ್ಬರ",
        english_name="Organic Manure / Compost",
        aliases=(
            "ಸಾವಯವ ಗೊಬ್ಬರ",
            "ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ",
            "ಕಾಂಪೋಸ್ಟ್",
            "ಎರೆಹುಳು ಗೊಬ್ಬರ",
            "ವರ್ಮಿಕಾಂಪೋಸ್ಟ್",
            "organic manure",
            "compost",
            "vermicompost",
        ),
    ),
    VocabularyEntry(
        canonical_id="GYPSUM",
        category=VocabularyCategory.SOIL_IMPROVEMENT,
        kannada_name="ಜಿಪ್ಸಂ",
        english_name="Gypsum",
        aliases=(
            "ಜಿಪ್ಸಂ",
            "ಜಿಪ್ಸಮ್",
            "gypsum",
        ),
    ),
    VocabularyEntry(
        canonical_id="LIME",
        category=VocabularyCategory.SOIL_IMPROVEMENT,
        kannada_name="ಕೃಷಿ ಸುಣ್ಣ",
        english_name="Agricultural Lime",
        aliases=(
            "ಸುಣ್ಣ",
            "ಕೃಷಿ ಸುಣ್ಣ",
            "lime",
            "agri lime",
        ),
    ),
    # Assistance Categories
    VocabularyEntry(
        canonical_id="SUBSIDY",
        category=VocabularyCategory.ASSISTANCE_NEED,
        kannada_name="ಸಹಾಯಧನ",
        english_name="Subsidy / Financial Grant",
        aliases=(
            "ಸಹಾಯಧನ",
            "ಸಬ್ಸಿಡಿ",
            "ಪ್ರೋತ್ಸಾಹಧನ",
            "ಅನುದಾನ",
            "subsidy",
            "grant",
        ),
    ),
    VocabularyEntry(
        canonical_id="CROP_INSURANCE",
        category=VocabularyCategory.ASSISTANCE_NEED,
        kannada_name="ಬೆಳೆ ವಿಮೆ",
        english_name="Crop Insurance",
        aliases=(
            "ಬೆಳೆ ವಿಮೆ",
            "ವಿಮೆ",
            "ಫಸಲ್ ಬಿಮಾ",
            "ಇನ್ಶೂರೆನ್ಸ್",
            "crop insurance",
            "insurance",
        ),
    ),
    VocabularyEntry(
        canonical_id="COMPENSATION",
        category=VocabularyCategory.ASSISTANCE_NEED,
        kannada_name="ಪರಿಹಾರ",
        english_name="Disaster Relief / Compensation",
        aliases=(
            "ಪರಿಹಾರ",
            "ಬರ ಪರಿಹಾರ",
            "ನೆರೆ ಪರಿಹಾರ",
            "ನಷ್ಟ ಪರಿಹಾರ",
            "relief",
            "compensation",
        ),
    ),
    VocabularyEntry(
        canonical_id="CREDIT_LOAN",
        category=VocabularyCategory.ASSISTANCE_NEED,
        kannada_name="ಕೃಷಿ ಸಾಲ",
        english_name="Agricultural Credit / Loan",
        aliases=(
            "ಸಾಲ",
            "ಕೃಷಿ ಸಾಲ",
            "ಬ್ಯಾಂಕ್ ಸಾಲ",
            "ಶೂನ್ಯ ಬಡ್ಡಿ ಸಾಲ",
            "ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್",
            "ಕೆಸಿಸಿ",
            "kcc",
            "loan",
            "credit",
        ),
    ),
    VocabularyEntry(
        canonical_id="SEED_FERTILIZER",
        category=VocabularyCategory.ASSISTANCE_NEED,
        kannada_name="ಬೀಜ ಮತ್ತು ಗೊಬ್ಬರ",
        english_name="Seeds and Fertilizers",
        aliases=(
            "ಬೀಜ",
            "ಬಿತ್ತನೆ ಬೀಜ",
            "ಗೊಬ್ಬರ",
            "ರಸಗೊಬ್ಬರ",
            "ಯೂರಿಯಾ",
            "seeds",
            "fertilizer",
            "urea",
        ),
    ),
]


# Build alias index sorted by descending length to prevent partial prefix conflicts
def _build_alias_index() -> List[Tuple[re.Pattern, VocabularyEntry, str]]:
    compiled: List[Tuple[re.Pattern, VocabularyEntry, str]] = []
    # Collect all (alias, entry)
    all_pairs: List[Tuple[str, VocabularyEntry]] = []
    for entry in AGRICULTURAL_VOCABULARY:
        for alias in entry.aliases:
            all_pairs.append((alias.strip(), entry))

    # Sort aliases by character length descending so multi-word aliases match before single words
    all_pairs.sort(key=lambda p: len(p[0]), reverse=True)

    for alias, entry in all_pairs:
        # Build word-boundary regex supporting Kannada and English characters
        pattern = re.compile(rf"(?<![\w\u0C80-\u0CFF]){re.escape(alias)}(?![\w\u0C80-\u0CFF])", re.IGNORECASE)
        compiled.append((pattern, entry, alias))

    return compiled


_ALIAS_INDEX = _build_alias_index()


def normalize_term(
    text: str,
    category: Optional[VocabularyCategory] = None,
) -> List[NormalizedTerm]:
    """Extract and normalize agricultural terms from an utterance.

    Never performs unrestricted global string replacement. Matches whole words
    and phrases against curated agricultural alias trees using greedy longest-match.
    """
    if not text or not text.strip():
        return []

    results: List[NormalizedTerm] = []
    matched_canonical_ids: Set[str] = set()
    matched_spans: List[Tuple[int, int]] = []

    for pattern, entry, alias in _ALIAS_INDEX:
        if category is not None and entry.category != category:
            continue

        if entry.canonical_id in matched_canonical_ids:
            continue

        for match in pattern.finditer(text):
            start, end = match.span()
            # Do not allow matches that overlap with already matched longer alias spans
            if any(s < end and start < e for s, e in matched_spans):
                continue

            matched_spans.append((start, end))
            results.append(
                NormalizedTerm(
                    canonical_id=entry.canonical_id,
                    category=entry.category,
                    kannada_name=entry.kannada_name,
                    english_name=entry.english_name,
                    matched_alias=alias,
                    confidence=1.0,
                    version=VOCABULARY_VERSION,
                )
            )
            matched_canonical_ids.add(entry.canonical_id)
            break

    return results


def get_canonical_term(canonical_id: str) -> Optional[VocabularyEntry]:
    """Lookup a vocabulary entry by its canonical ID."""
    for entry in AGRICULTURAL_VOCABULARY:
        if entry.canonical_id == canonical_id:
            return entry
    return None
