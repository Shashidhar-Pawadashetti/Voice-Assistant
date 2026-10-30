"""Machine-readable and grounded natural Kannada explainability formatter for scheme decisions.

Conforms to Directive M4.6, 06_DIALOGUE_AND_MEMORY.md Section 6, and 07_SCHEME_ENGINE_AND_GOVERNANCE.md.
"""

from typing import List
from app.core.scheme.enums import RecommendationStatus, SchemeClassification
from app.core.scheme.schemas import ConditionTrace, ExplanationTrace


def format_grounded_kannada_explanation(trace: ExplanationTrace) -> str:
    """Generate grounded, polite, native Kannada spoken response from an ExplanationTrace."""
    status = trace.recommendation_status
    scheme_name = trace.display_name_kn or trace.display_name
    is_demo = trace.classification == SchemeClassification.SYNTHETIC_DEMO

    demo_marker = " (ಗಮನಿಸಿ: ಇದು ತಂತ್ರಜ್ಞಾನ ಪ್ರಾತ್ಯಕ್ಷಿಕೆಗಾಗಿ ಇರುವ ಡೆಮೊ ಯೋಜನೆ - ನೈಜ ಸವಲತ್ತಲ್ಲ)" if is_demo else ""

    if status == RecommendationStatus.RULES_NOT_VERIFIED:
        return (
            f"'{scheme_name}' ಯೋಜನೆಯ ಪ್ರಸ್ತುತ ಸರ್ಕಾರದ ನಿಯಮಾವಳಿಗಳು ಪರಿಶೀಲನೆ ಹಂತದಲ್ಲಿವೆ.{demo_marker} "
            "ಅಧಿಕೃತ ಅಧಿಸೂಚನೆ ಇಲ್ಲದೆ ಅರ್ಹತೆಯನ್ನು ನಿರ್ಣಯಿಸಲಾಗುವುದಿಲ್ಲ. "
            "ದಯವಿಟ್ಟು ಸಂಬಂಧಪಟ್ಟ ಕೃಷಿ ಇಲಾಖೆ ಅಥವಾ ಅಧಿಕೃತ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ."
        )

    if status == RecommendationStatus.NOT_MATCHED:
        reasons_kn = []
        for f in trace.failed_conditions:
            if f.is_exclusion:
                reasons_kn.append(f"ಯೋಜನೆಯ ವಿನಾಯಿತಿ ಷರತ್ತು ಅನ್ವಯಿಸುತ್ತದೆ ({f.slot_key})")
            else:
                reasons_kn.append(f"{f.slot_key} ವಿವರವು ಯೋಜನೆಯ ಮಾನದಂಡಕ್ಕೆ ಸರಿಹೊಂದುತ್ತಿಲ್ಲ")

        reason_str = ", ".join(reasons_kn) if reasons_kn else "ಕೆಲವು ಮಾನದಂಡಗಳು ಪೂರ್ಣಗೊಂಡಿಲ್ಲ"
        return (
            f"ನೀವು ನೀಡಿರುವ ವಿವರಗಳ ಪ್ರಕಾರ '{scheme_name}' ಯೋಜನೆಗೆ ನೀವು ಸದ್ಯಕ್ಕೆ ಅರ್ಹರಾಗಿಲ್ಲ.{demo_marker} "
            f"ಕಾರಣ: {reason_str}."
        )

    if status == RecommendationStatus.INSUFFICIENT_INFORMATION:
        missing_names = {
            "district": "ಜಿಲ್ಲೆ",
            "taluk": "ತಾಲೂಕು",
            "crop": "ಬೆಳೆ",
            "land_area": "ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ",
            "land_ownership": "ಮಾಲೀಕತ್ವ",
            "irrigation": "ನೀರಾವರಿ",
            "season": "ಹಂಗಾಮು",
            "equipment": "ಯಂತ್ರೋಪಕರಣ",
            "soil_improvement": "ಮಣ್ಣು ಸುಧಾರಣೆ",
        }
        missing_kn = [missing_names.get(s, s) for s in trace.missing_slots]
        missing_str = ", ".join(missing_kn)
        return (
            f"'{scheme_name}' ಯೋಜನೆಯ ಅರ್ಹತೆಯನ್ನು ಪರಿಶೀಲಿಸಲು ನಿಮ್ಮ {missing_str} ವಿವರಗಳು ಇನ್ನೂ ಅಗತ್ಯವಿದೆ.{demo_marker} "
            "ದಯವಿಟ್ಟು ಈ ಮಾಹಿತಿಯನ್ನು ತಿಳಿಸಿ."
        )

    if status == RecommendationStatus.VERIFICATION_REQUIRED:
        return (
            f"ನೀವು ತಿಳಿಸಿರುವ ವಿವರಗಳ ಆಧಾರದ ಮೇಲೆ '{scheme_name}' ಯೋಜನೆಗೆ ನೀವು ಸಂಭಾವ್ಯವಾಗಿ ಸರಿಹೊಂದುತ್ತೀರಿ.{demo_marker} "
            "ಆದರೆ ಸರ್ಕಾರದ ಅಧಿಕೃತ ಜಮೀನು ದಾಖಲೆಗಳು (ಭೂಮಿ ಪಹಣಿ) ಮತ್ತು ಆಧಾರ್ ಇ-ಕೆವೈಸಿ (e-KYC) ಪರಿಶೀಲನೆ ಕಡ್ಡಾಯವಾಗಿದೆ. "
            "ಇದು ಅಧಿಕೃತ ಮಂಜೂರಾತಿಯಲ್ಲ, ಅರ್ಹತೆ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಲು ಅಧಿಕೃತ ಪೋರ್ಟಲ್ ಅಥವಾ ಕೃಷಿ ಅಧಿಕಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ."
        )

    if status == RecommendationStatus.POTENTIALLY_MATCHED:
        if is_demo:
            return (
                f"ನಿಮ್ಮ ಕೃಷಿ ವಿವರಗಳು '{scheme_name}' ಯೋಜನೆಗೆ ಹೊಂದಾಣಿಕೆಯಾಗಿವೆ.{demo_marker} "
                "ಇದು ಪರೀಕ್ಷಾ ಪ್ರಾತ್ಯಕ್ಷಿಕೆಯಾಗಿದ್ದು ಯಾವುದೇ ನೈಜ ಸರ್ಕಾರಿ ಧನಸಹಾಯವನ್ನು ಒಳಗೊಂಡಿರುವುದಿಲ್ಲ."
            )
        else:
            return (
                f"ನಿಮ್ಮ ವಿವರಗಳ ಆಧಾರದ ಮೇಲೆ ನೀವು '{scheme_name}' ಯೋಜನೆಗೆ ಸಂಭಾವ್ಯವಾಗಿ ಅರ್ಹರಾಗಿದ್ದೀರಿ.{demo_marker} "
                "ದಯವಿಟ್ಟು ಗಮನಿಸಿ, ಇದು ಸರ್ಕಾರದ ಅಂತಿಮ ಮಂಜೂರಾತಿ ಅಲ್ಲ. "
                "ಯೋಜನೆಯ ಸೌಲಭ್ಯ ಪಡೆಯಲು ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್ ಅಥವಾ ಸಮೀಪದ ರೈತ ಸಂಪರ್ಕ ಕೇಂದ್ರದಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಬೇಕು."
            )

    return f"'{scheme_name}' ಯೋಜನೆಯ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗಿದೆ."
