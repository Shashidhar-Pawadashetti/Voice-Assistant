"""Agricultural profile assembler combining multi-turn normalized farmer data.

Conforms to 02_PRODUCT_REQUIREMENTS.md Section 3, 06_DIALOGUE_AND_MEMORY.md, and M2.6.
Enforces:
1. Canonical identifiers and Pydantic validation.
2. Explicit provenance and confirmation states.
3. Missing-critical-field tracking.
4. Cross-field geographic conflict detection.
5. Audit trail preservation for corrections.
6. Non-negotiable invariant: Does NOT calculate government scheme eligibility.
"""

import copy
import logging
from typing import List, Optional

from app.core.normalization.corrections import SlotAuditRecord, detect_correction
from app.core.normalization.land_area import normalize_land_area
from app.core.normalization.location import (
    normalize_district,
    normalize_taluk,
    validate_taluk_in_district,
)
from app.core.normalization.ownership import OwnershipType, normalize_ownership
from app.core.normalization.vocabulary import VocabularyCategory, normalize_term
from app.core.profile.schemas import CRITICAL_SLOT_KEYS, AgriculturalProfile
from app.schemas.extraction import ExtractedEntity


logger = logging.getLogger(__name__)


class AgriculturalProfileAssembler:
    """Assembles and maintains a validated agricultural profile across multiple conversational turns."""

    def assemble_turn(
        self,
        current_profile: Optional[AgriculturalProfile],
        utterance: str,
        extracted_entities: Optional[List[ExtractedEntity]] = None,
    ) -> AgriculturalProfile:
        """Process an utterance and update the profile state."""
        profile = (
            current_profile.model_copy(deep=True)
            if current_profile is not None
            else AgriculturalProfile()
        )

        clean_utterance = utterance.strip() if utterance else ""
        if not clean_utterance:
            return profile

        # Step 1: Detect explicit spoken corrections
        correction = detect_correction(clean_utterance)
        if correction.is_correction:
            self._handle_correction(profile, correction.corrected_part or clean_utterance, clean_utterance)
            self._recalculate_status(profile)
            return profile

        # Step 2: Extract & normalize location facts
        new_district = normalize_district(clean_utterance)
        if new_district is not None:
            # Check for conflict if different district was previously set
            if profile.district and profile.district.district_id != new_district.district_id:
                profile.audit_trail.append(
                    SlotAuditRecord(
                        slot="district",
                        previous_value=profile.district.district_id,
                        new_value=new_district.district_id,
                        raw_correction_utterance=clean_utterance,
                        reason="IMPLICIT_UPDATE",
                    )
                )
            profile.district = new_district

        new_taluk = normalize_taluk(clean_utterance)
        if new_taluk is not None:
            profile.taluk = new_taluk

        # Step 3: Extract & normalize land measurement
        new_land_area = normalize_land_area(clean_utterance)
        if new_land_area is not None:
            if profile.land_area and profile.land_area.canonical_acres != new_land_area.canonical_acres:
                profile.audit_trail.append(
                    SlotAuditRecord(
                        slot="land_area",
                        previous_value=str(profile.land_area.canonical_acres),
                        new_value=str(new_land_area.canonical_acres),
                        raw_correction_utterance=clean_utterance,
                        reason="IMPLICIT_UPDATE",
                    )
                )
            profile.land_area = new_land_area

        # Step 4: Extract & normalize crops
        crops = normalize_term(clean_utterance, category=VocabularyCategory.CROP)
        if crops:
            if profile.primary_crop is None:
                profile.primary_crop = crops[0]
                if len(crops) > 1:
                    for sc in crops[1:]:
                        if sc.canonical_id not in [x.canonical_id for x in profile.secondary_crops]:
                            profile.secondary_crops.append(sc)
            else:
                # Add additional crops as secondary crops
                for crop in crops:
                    if crop.canonical_id != profile.primary_crop.canonical_id:
                        if crop.canonical_id not in [x.canonical_id for x in profile.secondary_crops]:
                            profile.secondary_crops.append(crop)

        # Step 5: Extract & normalize irrigation
        irrigation_list = normalize_term(clean_utterance, category=VocabularyCategory.IRRIGATION)
        if irrigation_list:
            profile.irrigation_type = irrigation_list[0]

        # Step 6: Extract & normalize season
        season_list = normalize_term(clean_utterance, category=VocabularyCategory.SEASON)
        if season_list:
            profile.season = season_list[0]

        # Step 7: Extract & normalize assistance needs
        needs = normalize_term(clean_utterance, category=VocabularyCategory.ASSISTANCE_NEED)
        for need in needs:
            if need.canonical_id not in [x.canonical_id for x in profile.assistance_needs]:
                profile.assistance_needs.append(need)

        # Step 8: Extract & normalize equipment
        equip_list = normalize_term(clean_utterance, category=VocabularyCategory.EQUIPMENT)
        for eq in equip_list:
            if eq.canonical_id not in [x.canonical_id for x in profile.equipment]:
                profile.equipment.append(eq)

        # Step 9: Extract & normalize soil improvements
        soil_list = normalize_term(clean_utterance, category=VocabularyCategory.SOIL_IMPROVEMENT)
        for st in soil_list:
            if st.canonical_id not in [x.canonical_id for x in profile.soil_improvements]:
                profile.soil_improvements.append(st)

        # Step 10: Extract & normalize land ownership
        tenure = normalize_ownership(clean_utterance)
        if tenure.ownership_type != OwnershipType.UNKNOWN:
            profile.ownership = tenure

        self._recalculate_status(profile)
        return profile

    def _handle_correction(self, profile: AgriculturalProfile, corrected_text: str, full_utterance: str) -> None:
        """Surgically update corrected slots and append audit record."""
        # 1. Check if crop corrected
        corrected_crops = normalize_term(corrected_text, category=VocabularyCategory.CROP)
        if corrected_crops:
            old_crop = profile.primary_crop.canonical_id if profile.primary_crop else "None"
            profile.primary_crop = corrected_crops[0]
            profile.audit_trail.append(
                SlotAuditRecord(
                    slot="crop",
                    previous_value=old_crop,
                    new_value=corrected_crops[0].canonical_id,
                    raw_correction_utterance=full_utterance,
                    reason="EXPLICIT_CORRECTION",
                )
            )

        # 2. Check if land area corrected
        corrected_area = normalize_land_area(corrected_text)
        if corrected_area and not corrected_area.is_ambiguous:
            old_area = str(profile.land_area.canonical_acres) if profile.land_area else "None"
            profile.land_area = corrected_area
            profile.audit_trail.append(
                SlotAuditRecord(
                    slot="land_area",
                    previous_value=old_area,
                    new_value=str(corrected_area.canonical_acres),
                    raw_correction_utterance=full_utterance,
                    reason="EXPLICIT_CORRECTION",
                )
            )

        # 3. Check if district corrected
        corrected_dist = normalize_district(corrected_text)
        if corrected_dist:
            old_dist = profile.district.district_id if profile.district else "None"
            profile.district = corrected_dist
            # If previous taluk no longer matches new district, clear taluk to avoid contradiction
            if profile.taluk and not validate_taluk_in_district(profile.taluk.taluk_id, corrected_dist.district_id):
                profile.taluk = None
            profile.audit_trail.append(
                SlotAuditRecord(
                    slot="district",
                    previous_value=old_dist,
                    new_value=corrected_dist.district_id,
                    raw_correction_utterance=full_utterance,
                    reason="EXPLICIT_CORRECTION",
                )
            )

    def _recalculate_status(self, profile: AgriculturalProfile) -> None:
        """Recalculate missing critical slots, cross-field validation, and readiness."""
        missing: List[str] = []

        if profile.district is None:
            missing.append("district")

        if profile.primary_crop is None:
            missing.append("crop")

        if profile.land_area is None or profile.land_area.is_ambiguous:
            missing.append("land_area")

        if profile.ownership is None or profile.ownership.ownership_type == OwnershipType.UNKNOWN:
            missing.append("land_ownership")

        profile.missing_critical_slots = missing

        # Cross-field geographic validation
        profile.conflicts = []
        if profile.district and profile.taluk:
            if not validate_taluk_in_district(profile.taluk.taluk_id, profile.district.district_id):
                profile.conflicts.append(
                    f"ತಾಲೂಕು '{profile.taluk.kannada_name}' ಜಿಲ್ಲೆ '{profile.district.kannada_name}' ವ್ಯಾಪ್ತಿಗೆ ಬರುವುದಿಲ್ಲ"
                )

        profile.is_ready_for_evaluation = len(missing) == 0 and len(profile.conflicts) == 0
