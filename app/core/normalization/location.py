"""Canonical Karnataka geographic reference dataset and location normalizer.

Conforms to 02_PRODUCT_REQUIREMENTS.md Section 3 and 05_VOICE_AI_PIPELINE.md Section 4.
Covers all 31 districts of Karnataka and their officially notified taluks.
Validates district/taluk parentage relationships and rejects non-existent locations.
"""

from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


LOCATION_DATASET_VERSION = "2026.10.1"


class DistrictInfo(BaseModel):
    """Canonical district entity."""

    district_id: str = Field(description="Canonical uppercase district code (e.g. DHARWAD)")
    kannada_name: str = Field(description="Official native Kannada district name")
    english_name: str = Field(description="Official English district name")
    matched_alias: str = Field(description="Utterance text that matched")


class TalukInfo(BaseModel):
    """Canonical taluk entity."""

    taluk_id: str = Field(description="Canonical uppercase taluk code (e.g. HUBLI_URBAN)")
    parent_district_id: str = Field(description="Parent canonical district code")
    kannada_name: str = Field(description="Official native Kannada taluk name")
    english_name: str = Field(description="Official English taluk name")
    matched_alias: str = Field(description="Utterance text that matched")


@dataclass(frozen=True)
class DistrictRecord:
    district_id: str
    kannada_name: str
    english_name: str
    aliases: Tuple[str, ...]
    taluks: Tuple["TalukRecord", ...]


@dataclass(frozen=True)
class TalukRecord:
    taluk_id: str
    kannada_name: str
    english_name: str
    aliases: Tuple[str, ...]


# Canonical 31 Karnataka Districts and Taluks
KARNATAKA_DISTRICTS: List[DistrictRecord] = [
    DistrictRecord(
        district_id="DHARWAD",
        kannada_name="ಧಾರವಾಡ",
        english_name="Dharwad",
        aliases=("ಧಾರವಾಡ", "dharwad", "dhawad", "darwad", "dharwar"),
        taluks=(
            TalukRecord("DHARWAD", "ಧಾರವಾಡ", "Dharwad", ("ಧಾರವಾಡ", "dharwad")),
            TalukRecord("HUBLI_URBAN", "ಹುಬ್ಬಳ್ಳಿ ನಗರ", "Hubballi Urban", ("ಹುಬ್ಬಳ್ಳಿ", "ಹುಬ್ಬಳ್ಳಿ ನಗರ", "hubli", "hubballi")),
            TalukRecord("HUBLI_RURAL", "ಹುಬ್ಬಳ್ಳಿ ಗ್ರಾಮೀಣ", "Hubballi Rural", ("ಹುಬ್ಬಳ್ಳಿ ಗ್ರಾಮೀಣ", "hubli rural")),
            TalukRecord("KUNDGOL", "ಕುಂದಗೋಳ", "Kundgol", ("ಕುಂದಗೋಳ", "kundgol")),
            TalukRecord("NAVALGUND", "ನವಲಗುಂದ", "Navalgund", ("ನವಲಗುಂದ", "navalgund")),
            TalukRecord("KALGHATGI", "ಕಲಘಟಗಿ", "Kalghatgi", ("ಕಲಘಟಗಿ", "kalghatgi")),
            TalukRecord("ALNAVAR", "ಅಳ್ನಾವರ", "Alnavar", ("ಅಳ್ನಾವರ", "ಅಳನಾವರ", "alnavar")),
            TalukRecord("ANNIGERI", "ಅಣ್ಣಿಗೇರಿ", "Annigeri", ("ಅಣ್ಣಿಗೇರಿ", "annigeri")),
        ),
    ),
    DistrictRecord(
        district_id="BELAGAVI",
        kannada_name="ಬೆಳಗಾವಿ",
        english_name="Belagavi",
        aliases=("ಬೆಳಗಾವಿ", "ಬೆಳಗಾಂ", "belagavi", "belgaum"),
        taluks=(
            TalukRecord("BELAGAVI", "ಬೆಳಗಾವಿ", "Belagavi", ("ಬೆಳಗಾವಿ", "belagavi", "belgaum")),
            TalukRecord("ATHANI", "ಅಥಣಿ", "Athani", ("ಅಥಣಿ", "athani")),
            TalukRecord("BAILHONGAL", "ಬೈಲಹೊಂಗಲ", "Bailhongal", ("ಬೈಲಹೊಂಗಲ", "bailhongal")),
            TalukRecord("CHIKKODI", "ಚಿಕ್ಕೋಡಿ", "Chikkodi", ("ಚಿಕ್ಕೋಡಿ", "chikkodi", "chikodi")),
            TalukRecord("GOKAK", "ಗೋಕಾಕ", "Gokak", ("ಗೋಕಾಕ", "ಗೋಕಾಕ್", "gokak")),
            TalukRecord("HUKKERI", "ಹುಕ್ಕೇರಿ", "Hukkeri", ("ಹುಕ್ಕೇರಿ", "hukkeri")),
            TalukRecord("KHANAPUR", "ಖಾನಾಪುರ", "Khanapur", ("ಖಾನಾಪುರ", "khanapur")),
            TalukRecord("RAMDURG", "ರಾಮದುರ್ಗ", "Ramdurg", ("ರಾಮದುರ್ಗ", "ramdurg")),
            TalukRecord("RAYBAG", "ರಾಯಭಾಗ", "Raybag", ("ರಾಯಭಾಗ", "raybag", "raibag")),
            TalukRecord("SAUNDATTI", "ಸವದತ್ತಿ", "Saundatti", ("ಸವದತ್ತಿ", "ಸೌಂದತ್ತಿ", "saundatti", "savadatti")),
            TalukRecord("KAGWAD", "ಕಾಗವಾಡ", "Kagwad", ("ಕಾಗವಾಡ", "kagwad")),
            TalukRecord("MUDALGI", "ಮೂಡಲಗಿ", "Mudalgi", ("ಮೂಡಲಗಿ", "mudalgi")),
            TalukRecord("NIPPANI", "ನಿಪ್ಪಾಣಿ", "Nippani", ("ನಿಪ್ಪಾಣಿ", "nippani")),
            TalukRecord("KITTUR", "ಕಿತ್ತೂರು", "Kittur", ("ಕಿತ್ತೂರು", "kittur")),
        ),
    ),
    DistrictRecord(
        district_id="KALABURAGI",
        kannada_name="ಕಲಬುರಗಿ",
        english_name="Kalaburagi",
        aliases=("ಕಲಬುರಗಿ", "ಕಲಬುರ್ಗಿ", "ಗುಲ್ಬರ್ಗಾ", "ಗುಲ್ಬರ್ಗ", "kalaburagi", "gulbarga"),
        taluks=(
            TalukRecord("KALABURAGI", "ಕಲಬುರಗಿ", "Kalaburagi", ("ಕಲಬುರಗಿ", "ಕಲಬುರ್ಗಿ", "kalaburagi", "gulbarga")),
            TalukRecord("AFZALPUR", "ಅಫಜಲಪುರ", "Afzalpur", ("ಅಫಜಲಪುರ", "ಅಫ್ಜಲ್ಪುರ", "afzalpur")),
            TalukRecord("ALAND", "ಆಳಂದ", "Aland", ("ಆಳಂದ", "aland")),
            TalukRecord("CHINCHOLI", "ಚಿಂಚೋಳಿ", "Chincholi", ("ಚಿಂಚೋಳಿ", "chincholi")),
            TalukRecord("CHITAPUR", "ಚಿತ್ತಾಪುರ", "Chitapur", ("ಚಿತ್ತಾಪುರ", "ಚಿತ್ತಾಪೂರ", "chitapur")),
            TalukRecord("JEWARGI", "ಜೇವರ್ಗಿ", "Jewargi", ("ಜೇವರ್ಗಿ", "jewargi")),
            TalukRecord("SEDAM", "ಸೇಡಂ", "Sedam", ("ಸೇಡಂ", "sedam")),
            TalukRecord("KAMALAPUR", "ಕಮಲಾಪುರ", "Kamalapur", ("ಕಮಲಾಪುರ", "kamalapur")),
            TalukRecord("KALAGI", "ಕಾಳಗಿ", "Kalagi", ("ಕಾಳಗಿ", "kalagi")),
            TalukRecord("SHAHABAD", "ಶಹಾಬಾದ್", "Shahabad", ("ಶಹಾಬಾದ್", "shahabad")),
            TalukRecord("YEDRAMI", "ಯಡ್ರಾಮಿ", "Yedrami", ("ಯಡ್ರಾಮಿ", "yedrami")),
        ),
    ),
    DistrictRecord(
        district_id="MANDYA",
        kannada_name="ಮಂಡ್ಯ",
        english_name="Mandya",
        aliases=("ಮಂಡ್ಯ", "mandya"),
        taluks=(
            TalukRecord("MANDYA", "ಮಂಡ್ಯ", "Mandya", ("ಮಂಡ್ಯ", "mandya")),
            TalukRecord("MADDUR", "ಮದ್ದೂರು", "Maddur", ("ಮದ್ದೂರು", "maddur")),
            TalukRecord("MALAVALLI", "ಮಳವಳ್ಳಿ", "Malavalli", ("ಮಳವಳ್ಳಿ", "malavalli")),
            TalukRecord("PANDAVAPURA", "ಪಾಂಡವಪುರ", "Pandavapura", ("ಪಾಂಡವಪುರ", "pandavapura")),
            TalukRecord("SRIRANGAPATNA", "ಶ್ರೀರಂಗಪಟ್ಟಣ", "Srirangapatna", ("ಶ್ರೀರಂಗಪಟ್ಟಣ", "srirangapatna")),
            TalukRecord("KRISHNARAJPET", "ಕೃಷ್ಣರಾಜಪೇಟೆ", "Krishnarajpet", ("ಕೃಷ್ಣರಾಜಪೇಟೆ", "ಕೆ ಆರ್ ಪೇಟೆ", "krishnarajpet", "kr pet")),
            TalukRecord("NAGAMANGALA", "ನಾಗಮಂಗಲ", "Nagamangala", ("ನಾಗಮಂಗಲ", "nagamangala")),
        ),
    ),
    DistrictRecord(
        district_id="MYSURU",
        kannada_name="ಮೈಸೂರು",
        english_name="Mysuru",
        aliases=("ಮೈಸೂರು", "mysuru", "mysore"),
        taluks=(
            TalukRecord("MYSURU", "ಮೈಸೂರು", "Mysuru", ("ಮೈಸೂರು", "mysuru", "mysore")),
            TalukRecord("HURSOOR", "ಹುಣಸೂರು", "Hunsur", ("ಹುಣಸೂರು", "hunsur")),
            TalukRecord("KRISHNARAJANAGARA", "ಕೃಷ್ಣರಾಜನಗರ", "Krishnarajanagara", ("ಕೃಷ್ಣರಾಜನಗರ", "ಕೆ ಆರ್ ನಗರ", "kr nagar")),
            TalukRecord("NANJANGUD", "ನಂಜನಗೂಡು", "Nanjangud", ("ನಂಜನಗೂಡು", "nanjangud")),
            TalukRecord("HEGGADADEVANAKOTE", "ಹೆಗ್ಗಡದೇವನಕೋಟೆ", "Heggadadevanakote", ("ಹೆಗ್ಗಡದೇವನಕೋಟೆ", "ಎಚ್ ಡಿ ಕೋಟೆ", "hd kote")),
            TalukRecord("PIRIYAPATNA", "ಪಿರಿಯಾಪಟ್ಟಣ", "Piriyapatna", ("ಪಿರಿಯಾಪಟ್ಟಣ", "piriyapatna")),
            TalukRecord("T_NARASIPURA", "ಟಿ ನರಸೀಪುರ", "Tirumakudalu Narasipura", ("ಟಿ ನರಸೀಪುರ", "ನರಸೀಪುರ", "t narasipura")),
            TalukRecord("SARAGUR", "ಸರಗೂರು", "Saragur", ("ಸರಗೂರು", "saragur")),
            TalukRecord("SALIGRAMA", "ಸಾಲಿಗ್ರಾಮ", "Saligrama", ("ಸಾಲಿಗ್ರಾಮ", "saligrama")),
        ),
    ),
    DistrictRecord(
        district_id="BAGALKOTE",
        kannada_name="ಬಾಗಲಕೋಟೆ",
        english_name="Bagalkote",
        aliases=("ಬಾಗಲಕೋಟೆ", "ಬಾಗಲಕೋಟಿ", "bagalkote", "bagalkot"),
        taluks=(
            TalukRecord("BAGALKOTE", "ಬಾಗಲಕೋಟೆ", "Bagalkote", ("ಬಾಗಲಕೋಟೆ", "bagalkote")),
            TalukRecord("BADAMI", "ಬಾದಾಮಿ", "Badami", ("ಬಾದಾಮಿ", "badami")),
            TalukRecord("BILAGI", "ಬೀಳಗಿ", "Bilagi", ("ಬೀಳಗಿ", "bilagi")),
            TalukRecord("HUNGUND", "ಹುನಗುಂದ", "Hungund", ("ಹುನಗುಂದ", "hungund")),
            TalukRecord("JAMKHANDI", "ಜಮಖಂಡಿ", "Jamkhandi", ("ಜಮಖಂಡಿ", "jamkhandi")),
            TalukRecord("MUDHOL", "ಮುಧೋಳ", "Mudhol", ("ಮುಧೋಳ", "mudhol")),
            TalukRecord("ILKAL", "ಇಲಕಲ್", "Ilkal", ("ಇಲಕಲ್", "ilkal")),
            TalukRecord("RABKAVI_BANHATTI", "ರಬಕವಿ ಬನಹಟ್ಟಿ", "Rabkavi Banhatti", ("ರಬಕವಿ ಬನಹಟ್ಟಿ", "rabkavi banhatti")),
            TalukRecord("GULEDAGUDDA", "ಗುಳೇದಗುಡ್ಡ", "Guledagudda", ("ಗುಳೇದಗುಡ್ಡ", "guledagudda")),
        ),
    ),
    DistrictRecord(
        district_id="VIJAYAPURA",
        kannada_name="ವಿಜಯಪುರ",
        english_name="Vijayapura",
        aliases=("ವಿಜಯಪುರ", "ವಿಜಾಪುರ", "ಬಿಜಾಪುರ", "vijayapura", "bijapur"),
        taluks=(
            TalukRecord("VIJAYAPURA", "ವಿಜಯಪುರ", "Vijayapura", ("ವಿಜಯಪುರ", "ವಿಜಾಪುರ", "vijayapura", "bijapur")),
            TalukRecord("BASAVANA_BAGEWADI", "ಬಸವನ ಬಾಗೇವಾಡಿ", "Basavana Bagewadi", ("ಬಸವನ ಬಾಗೇವಾಡಿ", "ಬಾಗೇವಾಡಿ", "basavana bagewadi")),
            TalukRecord("INDI", "ಇಂಡಿ", "Indi", ("ಇಂಡಿ", "indi")),
            TalukRecord("MUDDEBIHAL", "ಮುದ್ದೇಬಿಹಾಳ", "Muddebihal", ("ಮುದ್ದೇಬಿಹಾಳ", "muddebihal")),
            TalukRecord("SINDAGI", "ಸಿಂದಗಿ", "Sindagi", ("ಸಿಂದಗಿ", "sindagi")),
            TalukRecord("BABALESHWAR", "ಬಬಲೇಶ್ವರ", "Babaleshwar", ("ಬಬಲೇಶ್ವರ", "babaleshwar")),
            TalukRecord("TIKOTA", "ತಿಕೋಟಾ", "Tikota", ("ತಿಕೋಟಾ", "tikota")),
            TalukRecord("CHADCHAN", "ಚಡಚಣ", "Chadchan", ("ಚಡಚಣ", "chadchan")),
            TalukRecord("KOLHAR", "ಕೊಲ್ಹಾರ", "Kolhar", ("ಕೊಲ್ಹಾರ", "kolhar")),
            TalukRecord("NIDAGUNDI", "ನಿಡಗುಂದಿ", "Nidagundi", ("ನಿಡಗುಂದಿ", "nidagundi")),
            TalukRecord("DEVAR_HIPPARGI", "ದೇವರ ಹಿಪ್ಪರಗಿ", "Devar Hippargi", ("ದೇವರ ಹಿಪ್ಪರಗಿ", "devar hippargi")),
            TalukRecord("ALMEL", "ಆಲಮೇಲ", "Almel", ("ಆಲಮೇಲ", "almel")),
        ),
    ),
    DistrictRecord(
        district_id="RAICHUR",
        kannada_name="ರಾಯಚೂರು",
        english_name="Raichur",
        aliases=("ರಾಯಚೂರು", "ರಾಯಚುರು", "raichur"),
        taluks=(
            TalukRecord("RAICHUR", "ರಾಯಚೂರು", "Raichur", ("ರಾಯಚೂರು", "raichur")),
            TalukRecord("MANVI", "ಮಾನ್ವಿ", "Manvi", ("ಮಾನ್ವಿ", "manvi")),
            TalukRecord("SINDHANUR", "ಸಿಂಧನೂರು", "Sindhanur", ("ಸಿಂಧನೂರು", "sindhanur")),
            TalukRecord("DEVADURGA", "ದೇವದುರ್ಗ", "Devadurga", ("ದೇವದುರ್ಗ", "devadurga")),
            TalukRecord("LINGASUGUR", "ಲಿಂಗಸುಗೂರು", "Lingasugur", ("ಲಿಂಗಸುಗೂರು", "ಲಿಂಗಸೂಗೂರು", "lingasugur")),
            TalukRecord("MASKI", "ಮಸ್ಕಿ", "Maski", ("ಮಸ್ಕಿ", "maski")),
            TalukRecord("SIRWAR", "ಸಿರವಾರ", "Sirwar", ("ಸಿರವಾರ", "sirwar")),
        ),
    ),
    DistrictRecord(
        district_id="SHIVAMOGGA",
        kannada_name="ಶಿವಮೊಗ್ಗ",
        english_name="Shivamogga",
        aliases=("ಶಿವಮೊಗ್ಗ", "ಶಿವಮೊಗ್ಗ ಜಿಲ್ಲೆ", "shivamogga", "shimoga"),
        taluks=(
            TalukRecord("SHIVAMOGGA", "ಶಿವಮೊಗ್ಗ", "Shivamogga", ("ಶಿವಮೊಗ್ಗ", "shivamogga", "shimoga")),
            TalukRecord("BHADRAVATI", "ಭದ್ರಾವತಿ", "Bhadravati", ("ಭದ್ರಾವತಿ", "bhadravati")),
            TalukRecord("SAGAR", "ಸಾಗರ", "Sagar", ("ಸಾಗರ", "sagar")),
            TalukRecord("SHIKARIPURA", "ಶಿಕಾರಿಪುರ", "Shikaripura", ("ಶಿಕಾರಿಪುರ", "shikaripura")),
            TalukRecord("SORABA", "ಸೊರಬ", "Soraba", ("ಸೊರಬ", "soraba")),
            TalukRecord("TIRTHAHALLI", "ತೀರ್ಥಹಳ್ಳಿ", "Tirthahalli", ("ತೀರ್ಥಹಳ್ಳಿ", "tirthahalli")),
            TalukRecord("HOSANAGARA", "ಹೊಸನಗರ", "Hosanagara", ("ಹೊಸನಗರ", "hosanagara")),
        ),
    ),
    DistrictRecord(
        district_id="CHAMARAJANAGARA",
        kannada_name="ಚಾಮರಾಜನಗರ",
        english_name="Chamarajanagara",
        aliases=("ಚಾಮರಾಜನಗರ", "ಚಾಮರಾಜನಗರ ಜಿಲ್ಲೆ", "chamarajanagara", "chamarajanagar"),
        taluks=(
            TalukRecord("CHAMARAJANAGARA", "ಚಾಮರಾಜನಗರ", "Chamarajanagara", ("ಚಾಮರಾಜನಗರ", "chamarajanagar")),
            TalukRecord("GUNDLUPETE", "ಗುಂಡ್ಲುಪೇಟೆ", "Gundlupete", ("ಗುಂಡ್ಲುಪೇಟೆ", "gundlupet", "gundlupete")),
            TalukRecord("KOLLEGALA", "ಕೊಳ್ಳೇಗಾಲ", "Kollegala", ("ಕೊಳ್ಳೇಗಾಲ", "kollegal", "kollegala")),
            TalukRecord("YELANDUR", "ಯಳಂದೂರು", "Yelandur", ("ಯಳಂದೂರು", "yelandur")),
            TalukRecord("HANUR", "ಹನೂರು", "Hanur", ("ಹನೂರು", "hanur")),
        ),
    ),
    DistrictRecord(
        district_id="BALLARI",
        kannada_name="ಬಳ್ಳಾರಿ",
        english_name="Ballari",
        aliases=("ಬಳ್ಳಾರಿ", "ballari", "bellary"),
        taluks=(
            TalukRecord("BALLARI", "ಬಳ್ಳಾರಿ", "Ballari", ("ಬಳ್ಳಾರಿ", "ballari", "bellary")),
            TalukRecord("SANDUR", "ಸಂಡೂರು", "Sandur", ("ಸಂಡೂರು", "sandur")),
            TalukRecord("SIRUGUPPA", "ಸಿರಗುಪ್ಪ", "Siruguppa", ("ಸಿರಗುಪ್ಪ", "siruguppa")),
            TalukRecord("KAMPLI", "ಕಂಪ್ಲಿ", "Kampli", ("ಕಂಪ್ಲಿ", "kampli")),
            TalukRecord("KURUGODU", "ಕುರುಗೋಡು", "Kurugodu", ("ಕುರುಗೋಡು", "kurugodu")),
        ),
    ),
    DistrictRecord(
        district_id="VIJAYANAGARA",
        kannada_name="ವಿಜಯನಗರ",
        english_name="Vijayanagara",
        aliases=("ವಿಜಯನಗರ", "ವಿಜಯನಗರ ಜಿಲ್ಲೆ", "vijayanagara"),
        taluks=(
            TalukRecord("HOSAPETE", "ಹೊಸಪೇಟೆ", "Hosapete", ("ಹೊಸಪೇಟೆ", "hospet", "hosapete")),
            TalukRecord("HARAPANAHALLI", "ಹರಪನಹಳ್ಳಿ", "Harapanahalli", ("ಹರಪನಹಳ್ಳಿ", "harapanahalli")),
            TalukRecord("HOOVINA_HADAGALI", "ಹೂವಿನ ಹಡಗಲಿ", "Hoovina Hadagali", ("ಹೂವಿನ ಹಡಗಲಿ", "hadagali")),
            TalukRecord("HAGARIBOMMANAHALLI", "ಹಗರಿಬೊಮ್ಮನಹಳ್ಳಿ", "Hagaribommanahalli", ("ಹಗರಿಬೊಮ್ಮನಹಳ್ಳಿ", "hagaribommanahalli")),
            TalukRecord("KUDLIGI", "ಕೂಡ್ಲಿಗಿ", "Kudligi", ("ಕೂಡ್ಲಿಗಿ", "kudligi")),
            TalukRecord("KOTTURU", "ಕೊಟ್ಟೂರು", "Kotturu", ("ಕೊಟ್ಟೂರು", "kotturu")),
        ),
    ),
    DistrictRecord(
        district_id="BENGALURU_URBAN",
        kannada_name="ಬೆಂಗಳೂರು ನಗರ",
        english_name="Bengaluru Urban",
        aliases=("ಬೆಂಗಳೂರು", "ಬೆಂಗಳೂರು ನಗರ", "bangalore", "bengaluru", "bangalore urban"),
        taluks=(
            TalukRecord("BENGALURU_NORTH", "ಬೆಂಗಳೂರು ಉತ್ತರ", "Bengaluru North", ("ಬೆಂಗಳೂರು ಉತ್ತರ", "bengaluru north")),
            TalukRecord("BENGALURU_SOUTH", "ಬೆಂಗಳೂರು ದಕ್ಷಿಣ", "Bengaluru South", ("ಬೆಂಗಳೂರು ದಕ್ಷಿಣ", "bengaluru south")),
            TalukRecord("BENGALURU_EAST", "ಬೆಂಗಳೂರು ಪೂರ್ವ", "Bengaluru East", ("ಬೆಂಗಳೂರು ಪೂರ್ವ", "bengaluru east")),
            TalukRecord("ANEKAL", "ಆನೇಕಲ್", "Anekal", ("ಆನೇಕಲ್", "anekal")),
            TalukRecord("YELAHANKA", "ಯಲಹಂಕ", "Yelahanka", ("ಯಲಹಂಕ", "yelahanka")),
        ),
    ),
    DistrictRecord(
        district_id="BENGALURU_RURAL",
        kannada_name="ಬೆಂಗಳೂರು ಗ್ರಾಮಾಂತರ",
        english_name="Bengaluru Rural",
        aliases=("ಬೆಂಗಳೂರು ಗ್ರಾಮಾಂತರ", "bangalore rural", "bengaluru rural"),
        taluks=(
            TalukRecord("DEVANAHALLI", "ದೇವನಹಳ್ಳಿ", "Devanahalli", ("ದೇವನಹಳ್ಳಿ", "devanahalli")),
            TalukRecord("DODDABALLAPURA", "ದೊಡ್ಡಬಳ್ಳಾಪುರ", "Doddaballapura", ("ದೊಡ್ಡಬಳ್ಳಾಪುರ", "doddaballapur")),
            TalukRecord("HOSAKOTE", "ಹೊಸಕೋಟೆ", "Hosakote", ("ಹೊಸಕೋಟೆ", "hoskote", "hosakote")),
            TalukRecord("NELAMANGALA", "ನೆಲಮಂಗಲ", "Nelamangala", ("ನೆಲಮಂಗಲ", "nelamangala")),
        ),
    ),
    DistrictRecord(
        district_id="RAMANAGARA",
        kannada_name="ರಾಮನಗರ",
        english_name="Ramanagara",
        aliases=("ರಾಮನಗರ", "ramanagara", "ramanagar"),
        taluks=(
            TalukRecord("RAMANAGARA", "ರಾಮನಗರ", "Ramanagara", ("ರಾಮನಗರ", "ramanagara")),
            TalukRecord("CHANNAPATNA", "ಚನ್ನಪಟ್ಟಣ", "Channapatna", ("ಚನ್ನಪಟ್ಟಣ", "channapatna")),
            TalukRecord("KANAKAPURA", "ಕನಕಪುರ", "Kanakapura", ("ಕನಕಪುರ", "kanakapura")),
            TalukRecord("MAGADI", "ಮಾಗಡಿ", "Magadi", ("ಮಾಗಡಿ", "magadi")),
            TalukRecord("HAROHALLI", "ಹಾರೋಹಳ್ಳಿ", "Harohalli", ("ಹಾರೋಹಳ್ಳಿ", "harohalli")),
        ),
    ),
    DistrictRecord(
        district_id="HASSAN",
        kannada_name="ಹಾಸನ",
        english_name="Hassan",
        aliases=("ಹಾಸನ", "hassan"),
        taluks=(
            TalukRecord("HASSAN", "ಹಾಸನ", "Hassan", ("ಹಾಸನ", "hassan")),
            TalukRecord("ALUR", "ಆಲೂರು", "Alur", ("ಆಲೂರು", "alur")),
            TalukRecord("ARAKALGUD", "ಅರಕಲಗೂಡು", "Arakalgud", ("ಅರಕಲಗೂಡು", "arakalgud")),
            TalukRecord("ARASIKERE", "ಅರಸೀಕೆರೆ", "Arasikere", ("ಅರಸೀಕೆರೆ", "ಅರಸಿಕೆರೆ", "arasikere")),
            TalukRecord("BELUR", "ಬೇಲೂರು", "Belur", ("ಬೇಲೂರು", "belur")),
            TalukRecord("CHANNARAYAPATNA", "ಚನ್ನರಾಯಪಟ್ಟಣ", "Channarayapatna", ("ಚನ್ನರಾಯಪಟ್ಟಣ", "channarayapatna")),
            TalukRecord("HOLENARASIPURA", "ಹೊಳೆನರಸೀಪುರ", "Holenarasipura", ("ಹೊಳೆನರಸೀಪುರ", "holenarasipura")),
            TalukRecord("SAKLESHPURA", "ಸಕಲೇಶಪುರ", "Sakleshpura", ("ಸಕಲೇಶಪುರ", "sakleshpur")),
        ),
    ),
    DistrictRecord(
        district_id="CHIKKAMAGALURU",
        kannada_name="ಚಿಕ್ಕಮಗಳೂರು",
        english_name="Chikkamagaluru",
        aliases=("ಚಿಕ್ಕಮಗಳೂರು", "chikkamagaluru", "chikmagalur"),
        taluks=(
            TalukRecord("CHIKKAMAGALURU", "ಚಿಕ್ಕಮಗಳೂರು", "Chikkamagaluru", ("ಚಿಕ್ಕಮಗಳೂರು", "chikkamagaluru")),
            TalukRecord("KADUR", "ಕಡೂರು", "Kadur", ("ಕಡೂರು", "kadur")),
            TalukRecord("KOPPA", "ಕೊಪ್ಪ", "Koppa", ("ಕೊಪ್ಪ", "koppa")),
            TalukRecord("MUDIGERE", "ಮೂಡಿಗೆರೆ", "Mudigere", ("ಮೂಡಿಗೆರೆ", "mudigere")),
            TalukRecord("NARASIMHARAJAPURA", "ನರಸಿಂಹರಾಜಪುರ", "Narasimharajapura", ("ನರಸಿಂಹರಾಜಪುರ", "ಎನ್ ಆರ್ ಪುರ", "nr pura")),
            TalukRecord("SRINGERI", "ಶೃಂಗೇರಿ", "Sringeri", ("ಶೃಂಗೇರಿ", "sringeri")),
            TalukRecord("TARIKERE", "ತರೀಕೆರೆ", "Tarikere", ("ತರೀಕೆರೆ", "tarikere")),
            TalukRecord("AJJAMPURA", "ಅಜ್ಜಂಪುರ", "Ajjampura", ("ಅಜ್ಜಂಪುರ", "ajjampura")),
            TalukRecord("KALASA", "ಕಳಸ", "Kalasa", ("ಕಳಸ", "kalasa")),
        ),
    ),
    DistrictRecord(
        district_id="TUMAKURU",
        kannada_name="ತುಮಕೂರು",
        english_name="Tumakuru",
        aliases=("ತುಮಕೂರು", "tumakuru", "tumkur"),
        taluks=(
            TalukRecord("TUMAKURU", "ತುಮಕೂರು", "Tumakuru", ("ತುಮಕೂರು", "tumakuru")),
            TalukRecord("CHIKKANAYAKANAHALLI", "ಚಿಕ್ಕನಾಯಕನಹಳ್ಳಿ", "Chikkanayakanahalli", ("ಚಿಕ್ಕನಾಯಕನಹಳ್ಳಿ", "ಸಿ ಎನ್ ಹಳ್ಳಿ", "cn halli")),
            TalukRecord("GUBBI", "ಗುಬ್ಬಿ", "Gubbi", ("ಗುಬ್ಬಿ", "gubbi")),
            TalukRecord("KORATAGERE", "ಕೊರಟಗೆರೆ", "Koratagere", ("ಕೊರಟಗೆರೆ", "koratagere")),
            TalukRecord("KUNIGAL", "ಕುಣಿಗಲ್", "Kunigal", ("ಕುಣಿಗಲ್", "kunigal")),
            TalukRecord("MADHUGIRI", "ಮಧುಗಿರಿ", "Madhugiri", ("ಮಧುಗಿರಿ", "madhugiri")),
            TalukRecord("PAVAGADA", "ಪಾವಗಡ", "Pavagada", ("ಪಾವಗಡ", "pavagada")),
            TalukRecord("SIRA", "ಶಿರಾ", "Sira", ("ಶಿರಾ", "sira")),
            TalukRecord("TIPTUR", "ತಿಪಟೂರು", "Tiptur", ("ತಿಪಟೂರು", "tiptur")),
            TalukRecord("TURUVEKERE", "ತುರುವೇಕೆರೆ", "Turuvekere", ("ತುರುವೇಕೆರೆ", "turuvekere")),
        ),
    ),
    DistrictRecord(
        district_id="KOLAR",
        kannada_name="ಕೋಲಾರ",
        english_name="Kolar",
        aliases=("ಕೋಲಾರ", "kolar"),
        taluks=(
            TalukRecord("KOLAR", "ಕೋಲಾರ", "Kolar", ("ಕೋಲಾರ", "kolar")),
            TalukRecord("BANGARAPETE", "ಬಂಗಾರಪೇಟೆ", "Bangarapete", ("ಬಂಗಾರಪೇಟೆ", "bangarapet")),
            TalukRecord("MALUR", "ಮಾಲೂರು", "Malur", ("ಮಾಲೂರು", "malur")),
            TalukRecord("MULBAGAL", "ಮುಳಬಾಗಿಲು", "Mulbagal", ("ಮುಳಬಾಗಿಲು", "mulbagal")),
            TalukRecord("SRINIVASAPURA", "ಶ್ರೀನಿವಾಸಪುರ", "Srinivasapura", ("ಶ್ರೀನಿವಾಸಪುರ", "srinivasapur")),
            TalukRecord("KGF", "ಕೆ ಜಿ ಎಫ್", "Kolar Gold Fields", ("ಕೆ ಜಿ ಎಫ್", "ರಾಬರ್ಟ್‌ಸನ್‌ಪೇಟೆ", "kgf")),
        ),
    ),
    DistrictRecord(
        district_id="CHIKKABALLAPURA",
        kannada_name="ಚಿಕ್ಕಬಳ್ಳಾಪುರ",
        english_name="Chikkaballapura",
        aliases=("ಚಿಕ್ಕಬಳ್ಳಾಪುರ", "chikkaballapura", "chikkaballapur"),
        taluks=(
            TalukRecord("CHIKKABALLAPURA", "ಚಿಕ್ಕಬಳ್ಳಾಪುರ", "Chikkaballapura", ("ಚಿಕ್ಕಬಳ್ಳಾಪುರ", "chikkaballapur")),
            TalukRecord("BAGEPALLI", "ಬಾಗೇಪಲ್ಲಿ", "Bagepalli", ("ಬಾಗೇಪಲ್ಲಿ", "bagepalli")),
            TalukRecord("CHINTAMANI", "ಚಿಂತಾಮಣಿ", "Chintamani", ("ಚಿಂತಾಮಣಿ", "chintamani")),
            TalukRecord("GAURIBIDANUR", "ಗೌರಿಬಿದನೂರು", "Gauribidanur", ("ಗೌರಿಬಿದನೂರು", "gauribidanur")),
            TalukRecord("GUDIBANDE", "ಗುಡಿಬಂಡೆ", "Gudibande", ("ಗುಡಿಬಂಡೆ", "gudibande")),
            TalukRecord("SIDLAGHATTA", "ಶಿಡ್ಲಘಟ್ಟ", "Sidlaghatta", ("ಶಿಡ್ಲಘಟ್ಟ", "sidlaghatta")),
            TalukRecord("CHELUR", "ಚೇಳೂರು", "Chelur", ("ಚೇಳೂರು", "chelur")),
        ),
    ),
    DistrictRecord(
        district_id="CHITRADURGA",
        kannada_name="ಚಿತ್ರದುರ್ಗ",
        english_name="Chitradurga",
        aliases=("ಚಿತ್ರದುರ್ಗ", "chitradurga"),
        taluks=(
            TalukRecord("CHITRADURGA", "ಚಿತ್ರದುರ್ಗ", "Chitradurga", ("ಚಿತ್ರದುರ್ಗ", "chitradurga")),
            TalukRecord("CHALLAKERE", "ಚಳ್ಳಕೆರೆ", "Challakere", ("ಚಳ್ಳಕೆರೆ", "challakere")),
            TalukRecord("HIRIYUR", "ಹಿರಿಯೂರು", "Hiriyur", ("ಹಿರಿಯೂರು", "hiriyur")),
            TalukRecord("HOLALKERE", "ಹೊಳಲ್ಕೆರೆ", "Holalkere", ("ಹೊಳಲ್ಕೆರೆ", "holalkere")),
            TalukRecord("HOSADURGA", "ಹೊಸದುರ್ಗ", "Hosadurga", ("ಹೊಸದುರ್ಗ", "hosadurga")),
            TalukRecord("MOLAKALMURU", "ಮೊಳಕಾಲ್ಮೂರು", "Molakalmuru", ("ಮೊಳಕಾಲ್ಮೂರು", "molakalmuru")),
        ),
    ),
    DistrictRecord(
        district_id="DAVANAGERE",
        kannada_name="ದಾವಣಗೆರೆ",
        english_name="Davanagere",
        aliases=("ದಾವಣಗೆರೆ", "davanagere", "davangere"),
        taluks=(
            TalukRecord("DAVANAGERE", "ದಾವಣಗೆರೆ", "Davanagere", ("ದಾವಣಗೆರೆ", "davanagere")),
            TalukRecord("HARIHARA", "ಹರಿಹರ", "Harihara", ("ಹರಿಹರ", "harihar")),
            TalukRecord("HONNALI", "ಹೊನ್ನಾಳಿ", "Honnali", ("ಹೊನ್ನಾಳಿ", "honnali")),
            TalukRecord("CHANNAGIRI", "ಚನ್ನಗಿರಿ", "Channagiri", ("ಚನ್ನಗಿರಿ", "channagiri")),
            TalukRecord("JAGALUR", "ಜಗಳೂರು", "Jagalur", ("ಜಗಳೂರು", "jagalur")),
            TalukRecord("NYAMATHI", "ನ್ಯಾಮತಿ", "Nyamathi", ("ನ್ಯಾಮತಿ", "nyamathi")),
        ),
    ),
    DistrictRecord(
        district_id="GADAG",
        kannada_name="ಗದಗ",
        english_name="Gadag",
        aliases=("ಗದಗ", "gadag"),
        taluks=(
            TalukRecord("GADAG", "ಗದಗ", "Gadag", ("ಗದಗ", "gadag")),
            TalukRecord("NARAGUND", "ನರಗುಂದ", "Naragund", ("ನರಗುಂದ", "naragund")),
            TalukRecord("RONA", "ರೋಣ", "Rona", ("ರೋಣ", "ron")),
            TalukRecord("SHIRAHATTI", "ಶಿರಹಟ್ಟಿ", "Shirahatti", ("ಶಿರಹಟ್ಟಿ", "shirahatti")),
            TalukRecord("MUNDARGI", "ಮುಂಡರಗಿ", "Mundargi", ("ಮುಂಡರಗಿ", "mundargi")),
            TalukRecord("GAJENDRAGAD", "ಗಜೇಂದ್ರಗಡ", "Gajendragad", ("ಗಜೇಂದ್ರಗಡ", "gajendragad")),
            TalukRecord("LAKSHMESHWAR", "ಲಕ್ಷ್ಮೇಶ್ವರ", "Lakshmeshwar", ("ಲಕ್ಷ್ಮೇಶ್ವರ", "lakshmeshwar")),
        ),
    ),
    DistrictRecord(
        district_id="HAVERI",
        kannada_name="ಹಾವೇರಿ",
        english_name="Haveri",
        aliases=("ಹಾವೇರಿ", "haveri"),
        taluks=(
            TalukRecord("HAVERI", "ಹಾವೇರಿ", "Haveri", ("ಹಾವೇರಿ", "haveri")),
            TalukRecord("BYADGI", "ಬ್ಯಾಡಗಿ", "Byadgi", ("ಬ್ಯಾಡಗಿ", "byadgi")),
            TalukRecord("HANGAL", "ಹಾನಗಲ್", "Hangal", ("ಹಾನಗಲ್", "hangal")),
            TalukRecord("HIREKERUR", "ಹಿರೇಕೆರೂರು", "Hirekerur", ("ಹಿರೇಕೆರೂರು", "hirekerur")),
            TalukRecord("RANEEBENNUR", "ರಾಣೇಬೆನ್ನೂರು", "Ranebennur", ("ರಾಣೇಬೆನ್ನೂರು", "ranebennur")),
            TalukRecord("SAVANUR", "ಸವಣೂರು", "Savanur", ("ಸವಣೂರು", "savanur")),
            TalukRecord("SHIGGAON", "ಶಿಗ್ಗಾಂವ", "Shiggaon", ("ಶಿಗ್ಗಾಂವ", "shiggaon")),
            TalukRecord("RATTIHALLI", "ರಟ್ಟಿಹಳ್ಳಿ", "Rattihalli", ("ರಟ್ಟಿಹಳ್ಳಿ", "rattihalli")),
        ),
    ),
    DistrictRecord(
        district_id="KOPPAL",
        kannada_name="ಕೊಪ್ಪಳ",
        english_name="Koppal",
        aliases=("ಕೊಪ್ಪಳ", "koppal"),
        taluks=(
            TalukRecord("KOPPAL", "ಕೊಪ್ಪಳ", "Koppal", ("ಕೊಪ್ಪಳ", "koppal")),
            TalukRecord("GANGAVATHI", "ಗಂಗಾವತಿ", "Gangavathi", ("ಗಂಗಾವತಿ", "gangavathi")),
            TalukRecord("KUSHTAGI", "ಕುಷ್ಟಗಿ", "Kushtagi", ("ಕುಷ್ಟಗಿ", "kushtagi")),
            TalukRecord("YELBURGA", "ಯಲಬುರ್ಗಾ", "Yelburga", ("ಯಲಬುರ್ಗಾ", "yelburga")),
            TalukRecord("KANAKAGIRI", "ಕನಕಗಿರಿ", "Kanakagiri", ("ಕನಕಗಿರಿ", "kanakagiri")),
            TalukRecord("KARATAGI", "ಕಾರಟಗಿ", "Karatagi", ("ಕಾರಟಗಿ", "karatagi")),
            TalukRecord("KUKANOOR", "ಕುಕನೂರು", "Kukanoor", ("ಕುಕನೂರು", "kukanoor")),
        ),
    ),
    DistrictRecord(
        district_id="BIDAR",
        kannada_name="ಬೀದರ್",
        english_name="Bidar",
        aliases=("ಬೀದರ್", "ಬೀದರ", "bidar"),
        taluks=(
            TalukRecord("BIDAR", "ಬೀದರ್", "Bidar", ("ಬೀದರ್", "bidar")),
            TalukRecord("BASAVAKALYAN", "ಬಸವಕಲ್ಯಾಣ", "Basavakalyan", ("ಬಸವಕಲ್ಯಾಣ", "basavakalyan")),
            TalukRecord("BHALKI", "ಭಾಲ್ಕಿ", "Bhalki", ("ಭಾಲ್ಕಿ", "bhalki")),
            TalukRecord("HOMNABAD", "ಹುಮನಾಬಾದ್", "Homnabad", ("ಹುಮನಾಬಾದ್", "homnabad")),
            TalukRecord("AURAD", "ಔರಾದ್", "Aurad", ("ಔರಾದ್", "aurad")),
            TalukRecord("HULSOOR", "ಹುಲಸೂರು", "Hulsoor", ("ಹುಲಸೂರು", "hulsoor")),
            TalukRecord("CHITGOOPPA", "ಚಿಟಗುಪ್ಪ", "Chitgooppa", ("ಚಿಟಗುಪ್ಪ", "chitgooppa")),
            TalukRecord("KAMALNAGAR", "ಕಮಲನಗರ", "Kamalnagar", ("ಕಮಲನಗರ", "kamalnagar")),
        ),
    ),
    DistrictRecord(
        district_id="YADGIR",
        kannada_name="ಯಾದಗಿರಿ",
        english_name="Yadgir",
        aliases=("ಯಾದಗಿರಿ", "ಯಾದಗೀರ್", "yadgir"),
        taluks=(
            TalukRecord("YADGIR", "ಯಾದಗಿರಿ", "Yadgir", ("ಯಾದಗಿರಿ", "yadgir")),
            TalukRecord("SHAHAPUR", "ಶಹಾಪುರ", "Shahapur", ("ಶಹಾಪುರ", "shahapur")),
            TalukRecord("SHORAPUR", "ಶೋರಾಪುರ", "Shorapur", ("ಶೋರಾಪುರ", "ಸುರಪುರ", "shorapur", "surapur")),
            TalukRecord("GURMITKAL", "ಗುರುಮಿಟ್ಕಲ್", "Gurmitkal", ("ಗುರುಮಿಟ್ಕಲ್", "gurmitkal")),
            TalukRecord("WADAGERA", "ವಡಗೇರಾ", "Wadagera", ("ವಡಗೇರಾ", "wadagera")),
            TalukRecord("HUNASAGI", "ಹುಣಸಗಿ", "Hunasagi", ("ಹುಣಸಗಿ", "hunasagi")),
        ),
    ),
    DistrictRecord(
        district_id="DAKSHINA_KANNADA",
        kannada_name="ದಕ್ಷಿಣ ಕನ್ನಡ",
        english_name="Dakshina Kannada",
        aliases=("ದಕ್ಷಿಣ ಕನ್ನಡ", "ಮಂಗಳೂರು", "dakshina kannada", "mangalore", "south canara"),
        taluks=(
            TalukRecord("MANGALURU", "ಮಂಗಳೂರು", "Mangaluru", ("ಮಂಗಳೂರು", "mangaluru", "mangalore")),
            TalukRecord("BANTWAL", "ಬಂಟ್ವಾಳ", "Bantwal", ("ಬಂಟ್ವಾಳ", "bantwal")),
            TalukRecord("BELTHANGADY", "ಬೆಳ್ತಂಗಡಿ", "Belthangady", ("ಬೆಳ್ತಂಗಡಿ", "belthangady")),
            TalukRecord("PUTTUR", "ಪುತ್ತೂರು", "Puttur", ("ಪುತ್ತೂರು", "puttur")),
            TalukRecord("SULLIA", "ಸುಳ್ಯ", "Sullia", ("ಸುಳ್ಯ", "sullia")),
            TalukRecord("MOODABIDRI", "ಮೂಡುಬಿದಿರೆ", "Moodabidri", ("ಮೂಡುಬಿದಿರೆ", "moodabidri")),
            TalukRecord("KADABA", "ಕಡಬ", "Kadaba", ("ಕಡಬ", "kadaba")),
        ),
    ),
    DistrictRecord(
        district_id="UDUPI",
        kannada_name="ಉಡುಪಿ",
        english_name="Udupi",
        aliases=("ಉಡುಪಿ", "udupi"),
        taluks=(
            TalukRecord("UDUPI", "ಉಡುಪಿ", "Udupi", ("ಉಡುಪಿ", "udupi")),
            TalukRecord("KUNDAPURA", "ಕುಂದಾಪುರ", "Kundapura", ("ಕುಂದಾಪುರ", "kundapura", "kundapur")),
            TalukRecord("KARKALA", "ಕಾರ್ಕಳ", "Karkala", ("ಕಾರ್ಕಳ", "karkala")),
            TalukRecord("BRAHMAVARA", "ಬ್ರಹ್ಮಾವರ", "Brahmavara", ("ಬ್ರಹ್ಮಾವರ", "brahmavara")),
            TalukRecord("BYNDOOR", "ಬೈಂದೂರು", "Byndoor", ("ಬೈಂದೂರು", "byndoor")),
            TalukRecord("HEBRI", "ಹೆಬ್ರಿ", "Hebri", ("ಹೆಬ್ರಿ", "hebri")),
            TalukRecord("KAUP", "ಕಾಪು", "Kaup", ("ಕಾಪು", "kaup")),
        ),
    ),
    DistrictRecord(
        district_id="UTTARA_KANNADA",
        kannada_name="ಉತ್ತರ ಕನ್ನಡ",
        english_name="Uttara Kannada",
        aliases=("ಉತ್ತರ ಕನ್ನಡ", "ಕಾರವಾರ", "uttara kannada", "karwar", "north canara"),
        taluks=(
            TalukRecord("KARWAR", "ಕಾರವಾರ", "Karwar", ("ಕಾರವಾರ", "karwar")),
            TalukRecord("ANKOLA", "ಅಂಕೋಲಾ", "Ankola", ("ಅಂಕೋಲಾ", "ankola")),
            TalukRecord("KUMTA", "ಕುಮಟಾ", "Kumta", ("ಕುಮಟಾ", "kumta")),
            TalukRecord("HONNAVAR", "ಹೊನ್ನಾವರ", "Honnavar", ("ಹೊನ್ನಾವರ", "honnavar")),
            TalukRecord("BHATKAL", "ಭಟ್ಕಳ", "Bhatkal", ("ಭಟ್ಕಳ", "bhatkal")),
            TalukRecord("SIRSI", "ಶಿರಸಿ", "Sirsi", ("ಶಿರಸಿ", "sirsi")),
            TalukRecord("SIDDAPUR", "ಸಿದ್ದಾಪುರ", "Siddapur", ("ಸಿದ್ದಾಪುರ", "siddapur")),
            TalukRecord("YELLAPUR", "ಯಲ್ಲಾಪುರ", "Yellapur", ("ಯಲ್ಲಾಪುರ", "yellapur")),
            TalukRecord("HALIYAL", "ಹಳಿಯಾಳ", "Haliyal", ("ಹಳಿಯಾಳ", "haliyal")),
            TalukRecord("JOIDA", "ಜೋಯಿಡಾ", "Joida", ("ಜೋಯಿಡಾ", "joida")),
            TalukRecord("MUNDGOD", "ಮುಂಡಗೋಡ", "Mundgod", ("ಮುಂಡಗೋಡ", "mundgod")),
            TalukRecord("DANDELI", "ದಾಂಡೇಲಿ", "Dandeli", ("ದಾಂಡೇಲಿ", "dandeli")),
        ),
    ),
    DistrictRecord(
        district_id="KODAGU",
        kannada_name="ಕೊಡಗು",
        english_name="Kodagu",
        aliases=("ಕೊಡಗು", "ಮಡಿಕೇರಿ", "kodagu", "coorg", "madikeri"),
        taluks=(
            TalukRecord("MADIKERI", "ಮಡಿಕೇರಿ", "Madikeri", ("ಮಡಿಕೇರಿ", "madikeri")),
            TalukRecord("SOMWARPET", "ಸೋಮವಾರಪೇಟೆ", "Somwarpet", ("ಸೋಮವಾರಪೇಟೆ", "somwarpet")),
            TalukRecord("VIRAJPET", "ವಿರಾಜಪೇಟೆ", "Virajpet", ("ವಿರಾಜಪೇಟೆ", "virajpet")),
            TalukRecord("PONNAMPET", "ಪೊನ್ನಂಪೇಟೆ", "Ponnampet", ("ಪೊನ್ನಂಪೇಟೆ", "ponnampet")),
            TalukRecord("KUSHALNAGAR", "ಕುಶಾಲನಗರ", "Kushalnagar", ("ಕುಶಾಲನಗರ", "kushalnagar")),
        ),
    ),
]


# Compile District Lookup Tables
def _build_district_index() -> List[Tuple[re.Pattern, DistrictRecord, str]]:
    pairs: List[Tuple[str, DistrictRecord]] = []
    for d in KARNATAKA_DISTRICTS:
        for alias in d.aliases:
            pairs.append((alias.strip(), d))
    pairs.sort(key=lambda p: len(p[0]), reverse=True)

    compiled: List[Tuple[re.Pattern, DistrictRecord, str]] = []
    for alias, d in pairs:
        pat = re.compile(
            rf"(?<![\w\u0C80-\u0CFF]){re.escape(alias)}(?:ದಲ್ಲಿ|ನಲ್ಲಿ|ಯಿಂದ|ದಿಂದ|ಯವನು|ದವರು|ಯವರು|ಯ|ದ|ಗೆ|ಕ್ಕೆ)?(?![\w\u0C80-\u0CFF])",
            re.IGNORECASE,
        )
        compiled.append((pat, d, alias))
    return compiled


# Compile Taluk Lookup Tables
def _build_taluk_index() -> List[Tuple[re.Pattern, TalukRecord, DistrictRecord, str]]:
    pairs: List[Tuple[str, TalukRecord, DistrictRecord]] = []
    for d in KARNATAKA_DISTRICTS:
        for t in d.taluks:
            for alias in t.aliases:
                pairs.append((alias.strip(), t, d))
    pairs.sort(key=lambda p: len(p[0]), reverse=True)

    compiled: List[Tuple[re.Pattern, TalukRecord, DistrictRecord, str]] = []
    for alias, t, d in pairs:
        pat = re.compile(
            rf"(?<![\w\u0C80-\u0CFF]){re.escape(alias)}(?:ದಲ್ಲಿ|ನಲ್ಲಿ|ಯಿಂದ|ದಿಂದ|ಯವನು|ದವರು|ಯವರು|ಯ|ದ|ಗೆ|ಕ್ಕೆ)?(?![\w\u0C80-\u0CFF])",
            re.IGNORECASE,
        )
        compiled.append((pat, t, d, alias))
    return compiled


_DISTRICT_INDEX = _build_district_index()
_TALUK_INDEX = _build_taluk_index()


def get_district_by_id(district_id: str) -> Optional[DistrictInfo]:
    """Retrieve canonical DistrictInfo by district_id."""
    did = district_id.upper().strip()
    for d in KARNATAKA_DISTRICTS:
        if d.district_id == did:
            return DistrictInfo(
                district_id=d.district_id,
                kannada_name=d.kannada_name,
                english_name=d.english_name,
                matched_alias=d.kannada_name,
            )
    return None


def normalize_district(text: str) -> Optional[DistrictInfo]:
    """Find and normalize a Karnataka district from utterance text.

    Returns DistrictInfo if matched, None if no known district found.
    Never invents fictitious districts.
    """
    if not text or not text.strip():
        return None

    for pattern, district, alias in _DISTRICT_INDEX:
        if pattern.search(text):
            return DistrictInfo(
                district_id=district.district_id,
                kannada_name=district.kannada_name,
                english_name=district.english_name,
                matched_alias=alias,
            )
    return None


def normalize_taluk(text: str, district_id: Optional[str] = None) -> Optional[TalukInfo]:
    """Find and normalize a Karnataka taluk from utterance text.

    If district_id is provided, enforces that the taluk belongs to that district.
    Disambiguates words sharing names with districts (e.g. 'ಬೆಳಗಾವಿ ಜಿಲ್ಲೆ ಅಥಣಿ ತಾಲೂಕು').
    """
    if not text or not text.strip():
        return None

    clean = text.strip()
    candidates: List[Tuple[int, TalukRecord, DistrictRecord, str]] = []

    for pattern, taluk, district, alias in _TALUK_INDEX:
        if district_id and district.district_id != district_id.upper():
            continue

        match = pattern.search(clean)
        if match:
            # Check context following the match
            post_text = clean[match.end() : match.end() + 25].strip().lower()

            # If immediately followed by 'ಜಿಲ್ಲೆ' / 'district', it is specifying the district
            is_district_marker = bool(re.match(r"^(?:ಜಿಲ್ಲೆ|ಜಿಲ್ಲೆಯ|ಜಿಲ್ಲೆಯವನು|district)", post_text))
            if is_district_marker:
                continue

            # If followed by 'ತಾಲೂಕು' / 'ತಾಲೂಕಿನಲ್ಲಿ' / 'taluk', prioritize as explicit taluk
            is_taluk_marker = bool(re.match(r"^(?:ತಾಲೂಕು|ತಾಲೂಕಿನಲ್ಲಿ|ತಾಲೂಕಿನ|ತಾಲೂಕ|taluk)", post_text))

            score = 2 if is_taluk_marker else 1
            candidates.append((score, taluk, district, alias))

    if not candidates:
        return None

    # Sort by priority score descending, then alias length descending
    candidates.sort(key=lambda c: (c[0], len(c[3])), reverse=True)
    best = candidates[0]
    return TalukInfo(
        taluk_id=best[1].taluk_id,
        parent_district_id=best[2].district_id,
        kannada_name=best[1].kannada_name,
        english_name=best[1].english_name,
        matched_alias=best[3],
    )


def validate_taluk_in_district(taluk_id: str, district_id: str) -> bool:
    """Validate that a taluk legitimately belongs to the declared district."""
    tid = taluk_id.upper().strip()
    did = district_id.upper().strip()

    for d in KARNATAKA_DISTRICTS:
        if d.district_id == did:
            for t in d.taluks:
                if t.taluk_id == tid:
                    return True
            return False
    return False


def get_taluks_for_district(district_id: str) -> List[TalukInfo]:
    """Retrieve all official taluks for a given district."""
    did = district_id.upper().strip()
    for d in KARNATAKA_DISTRICTS:
        if d.district_id == did:
            return [
                TalukInfo(
                    taluk_id=t.taluk_id,
                    parent_district_id=d.district_id,
                    kannada_name=t.kannada_name,
                    english_name=t.english_name,
                    matched_alias=t.kannada_name,
                )
                for t in d.taluks
            ]
    return []
