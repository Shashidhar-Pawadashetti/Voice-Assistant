"""Conversation orchestration service implementing persistent memory, multi-turn dialogue, and lifecycle management.

Conforms to Directives M3.1 - M3.7, 06_DIALOGUE_AND_MEMORY.md, and 09_API_CONTRACT.md.
Rules:
1. Enforce farmer ownership at every database boundary (BOLA protection).
2. Optimistic locking on conversation version to prevent race conditions.
3. Deterministic dialogue state transitions governed by DialogueStateMachine.
4. Resilient TTS fallback (text response guaranteed on speech failure).
5. Immutable slot audit trail preservation.
6. Non-negotiable invariant: NEVER evaluate government scheme eligibility in LLM or conversation service.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.asr import SpeechRecognizer, get_speech_recognizer
from app.core.audio import normalize_to_wav_16k, transient_audio_file, validate_audio_file
from app.core.dialogue.confirmation import ConfirmationDecision, analyze_confirmation
from app.core.dialogue.intent_registry import IntentSlotResolver
from app.core.dialogue.prompts import generate_dialogue_response
from app.core.dialogue.state_machine import DialogueState, DialogueStateMachine
from app.core.exceptions import (
    AudioValidationError,
    AuthorizationError,
    ConversationExpiredError,
    OptimisticLockError,
    ResourceNotFoundError,
)
from app.core.llm.extractor import SchemeExtractor, get_scheme_extractor
from app.core.normalization.ownership import ProvenanceAssertion
from app.core.profile.assembler import AgriculturalProfileAssembler
from app.core.profile.schemas import AgriculturalProfile
from app.core.tts import EphemeralAudioStore, SpeechSynthesizer, get_ephemeral_audio_store, get_speech_synthesizer
from app.models.audit import AuditEvent
from app.models.conversation import Conversation, ConversationSlot, ConversationTurn
from app.models.farmer import Farmer, FarmerProfile
from app.schemas.conversation import (
    ConversationHistoryResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationTurnDTO,
    TurnResponse,
)
from app.schemas.extraction import Intent


logger = logging.getLogger("krishi.service.conversation")


class ConversationService:
    """Manages multi-turn conversation sessions, persistent memory, and deterministic dialogue flow."""

    def __init__(
        self,
        db: AsyncSession,
        speech_recognizer: Optional[SpeechRecognizer] = None,
        extractor: Optional[SchemeExtractor] = None,
        speech_synthesizer: Optional[SpeechSynthesizer] = None,
        audio_store: Optional[EphemeralAudioStore] = None,
        profile_assembler: Optional[AgriculturalProfileAssembler] = None,
    ):
        self.db = db
        self.speech_recognizer = speech_recognizer or get_speech_recognizer()
        self.extractor = extractor or get_scheme_extractor()
        self.speech_synthesizer = speech_synthesizer or get_speech_synthesizer()
        self.audio_store = audio_store or get_ephemeral_audio_store()
        self.profile_assembler = profile_assembler or AgriculturalProfileAssembler()
        self.settings = get_settings()

    # -------------------------------------------------------------------------
    # M3.1: Conversation Lifecycle Management
    # -------------------------------------------------------------------------

    async def create_conversation(
        self,
        farmer_id: uuid.UUID,
        language: str = "kn",
        initial_intent: Optional[Intent] = None,
    ) -> ConversationResponse:
        """Create a new conversation session for an authenticated farmer."""
        # Verify farmer exists
        farmer = await self.db.get(Farmer, farmer_id)
        if not farmer:
            raise ResourceNotFoundError(f"Farmer '{farmer_id}' does not exist")

        conversation = Conversation(
            farmer_id=farmer_id,
            status="ACTIVE",
            state=DialogueState.GREETING.value,
            language=language,
            summary=f"Initial intent: {initial_intent.value}" if initial_intent else None,
            version=1,
            last_activity_at=datetime.now(timezone.utc),
        )
        self.db.add(conversation)
        await self.db.flush()

        # Audit event
        audit = AuditEvent(
            actor_type="FARMER",
            actor_id=farmer_id,
            event_type="CONVERSATION_CREATED",
            resource_type="CONVERSATION",
            resource_id=conversation.id,
            metadata_={"language": language, "initial_intent": initial_intent.value if initial_intent else None},
        )
        self.db.add(audit)
        await self.db.flush()

        initial_greeting = generate_dialogue_response(
            state=DialogueState.GREETING,
            intent=initial_intent or Intent.GREETING,
            profile=AgriculturalProfile(),
        )

        return self._format_conversation_response(
            conversation=conversation,
            profile=AgriculturalProfile(),
            missing_slots=["district"],
            next_question=initial_greeting,
        )

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        farmer_id: uuid.UUID,
    ) -> ConversationResponse:
        """Retrieve conversation state while enforcing farmer ownership (BOLA)."""
        conv = await self._load_conversation_enforcing_ownership(conversation_id, farmer_id)
        profile = await self._load_or_assemble_profile(conv)

        current_intent = self._extract_intent_from_summary(conv.summary)
        missing_slots = IntentSlotResolver.get_missing_slots(current_intent, profile)
        next_slot = IntentSlotResolver.get_next_missing_slot(current_intent, profile)

        next_q = generate_dialogue_response(
            state=DialogueState(conv.state),
            intent=current_intent,
            profile=profile,
            next_missing_slot=next_slot,
        )

        return self._format_conversation_response(
            conversation=conv,
            profile=profile,
            missing_slots=missing_slots,
            next_question=next_q,
        )

    async def list_conversations(
        self,
        farmer_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> ConversationListResponse:
        """List conversations belonging to the authenticated farmer with pagination."""
        count_stmt = select(func.count(Conversation.id)).where(
            Conversation.farmer_id == farmer_id,
            Conversation.status != "DELETED",
        )
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = (
            select(Conversation)
            .where(Conversation.farmer_id == farmer_id, Conversation.status != "DELETED")
            .order_by(Conversation.last_activity_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        conversations = result.scalars().all()

        formatted: List[ConversationResponse] = []
        for conv in conversations:
            prof = await self._load_or_assemble_profile(conv)
            intent = self._extract_intent_from_summary(conv.summary)
            missing = IntentSlotResolver.get_missing_slots(intent, prof)
            formatted.append(
                self._format_conversation_response(
                    conversation=conv,
                    profile=prof,
                    missing_slots=missing,
                )
            )

        return ConversationListResponse(conversations=formatted, total=total)

    async def get_active_conversation(
        self,
        farmer_id: uuid.UUID,
    ) -> Optional[ConversationResponse]:
        """Retrieve the most recently active non-completed conversation for a farmer."""
        stmt = (
            select(Conversation)
            .where(Conversation.farmer_id == farmer_id, Conversation.status == "ACTIVE")
            .order_by(Conversation.last_activity_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if not conv:
            return None

        prof = await self._load_or_assemble_profile(conv)
        intent = self._extract_intent_from_summary(conv.summary)
        missing = IntentSlotResolver.get_missing_slots(intent, prof)
        next_slot = IntentSlotResolver.get_next_missing_slot(intent, prof)
        next_q = generate_dialogue_response(
            state=DialogueState(conv.state),
            intent=intent,
            profile=prof,
            next_missing_slot=next_slot,
        )

        return self._format_conversation_response(
            conversation=conv,
            profile=prof,
            missing_slots=missing,
            next_question=next_q,
        )

    async def resume_conversation(
        self,
        conversation_id: uuid.UUID,
        farmer_id: uuid.UUID,
    ) -> ConversationResponse:
        """Resume a paused conversation session."""
        conv = await self._load_conversation_enforcing_ownership(conversation_id, farmer_id)

        if conv.status == "COMPLETED":
            raise ConversationExpiredError("Cannot resume a completed conversation session")

        # Advance state machine from PAUSED -> COLLECTING_SLOTS (or resume previous)
        current_state = DialogueState(conv.state)
        new_state = (
            DialogueStateMachine.transition(current_state, DialogueState.COLLECTING_SLOTS)
            if current_state == DialogueState.PAUSED
            else current_state
        )

        conv.status = "ACTIVE"
        conv.state = new_state.value
        conv.last_activity_at = datetime.now(timezone.utc)
        conv.version += 1
        await self.db.flush()

        prof = await self._load_or_assemble_profile(conv)
        intent = self._extract_intent_from_summary(conv.summary)
        missing = IntentSlotResolver.get_missing_slots(intent, prof)
        next_slot = IntentSlotResolver.get_next_missing_slot(intent, prof)
        next_q = generate_dialogue_response(
            state=new_state,
            intent=intent,
            profile=prof,
            next_missing_slot=next_slot,
        )

        return self._format_conversation_response(
            conversation=conv,
            profile=prof,
            missing_slots=missing,
            next_question=next_q,
        )

    async def complete_conversation(
        self,
        conversation_id: uuid.UUID,
        farmer_id: uuid.UUID,
    ) -> ConversationResponse:
        """Gracefully complete and close a conversation session."""
        conv = await self._load_conversation_enforcing_ownership(conversation_id, farmer_id)
        current_state = DialogueState(conv.state)

        new_state = (
            DialogueStateMachine.transition(current_state, DialogueState.COMPLETED)
            if current_state != DialogueState.COMPLETED
            else current_state
        )

        conv.status = "COMPLETED"
        conv.state = new_state.value
        conv.last_activity_at = datetime.now(timezone.utc)
        conv.version += 1
        await self.db.flush()

        prof = await self._load_or_assemble_profile(conv)
        return self._format_conversation_response(
            conversation=conv,
            profile=prof,
            missing_slots=[],
            next_question="ಧನ್ಯವಾದಗಳು. ಸಂಭಾಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ.",
        )

    async def get_conversation_history(
        self,
        conversation_id: uuid.UUID,
        farmer_id: uuid.UUID,
        max_turns: int = 10,
    ) -> ConversationHistoryResponse:
        """Retrieve bounded recent conversation turns for context retrieval and UI rendering."""
        await self._load_conversation_enforcing_ownership(conversation_id, farmer_id)

        stmt = (
            select(ConversationTurn)
            .where(ConversationTurn.conversation_id == conversation_id)
            .order_by(ConversationTurn.turn_number.asc())
        )
        res = await self.db.execute(stmt)
        turns = res.scalars().all()
        total = len(turns)

        # Slice to bounded recent turns (default max 10, typically 6)
        recent_turns = turns[-max_turns:] if total > max_turns else turns

        dtos = [
            ConversationTurnDTO(
                turn_id=str(t.id),
                turn_number=t.turn_number,
                role=t.role,
                input_mode=t.input_mode,
                transcript_text=t.transcript_text,
                assistant_text=t.assistant_text,
                created_at=t.created_at,
            )
            for t in recent_turns
        ]

        return ConversationHistoryResponse(
            conversation_id=str(conversation_id),
            turns=dtos,
            total_turns=total,
        )

    # -------------------------------------------------------------------------
    # M3.4 - M3.7: Turn Processing (Voice & Text) with Memory Persistence
    # -------------------------------------------------------------------------

    async def process_turn(
        self,
        conversation_id: uuid.UUID,
        farmer_id: uuid.UUID,
        input_mode: str,
        text_input: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        client_turn_id: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> TurnResponse:
        """Process a conversation turn end-to-end with persistent memory and state machine updates."""
        conv = await self._load_conversation_enforcing_ownership(conversation_id, farmer_id)

        if conv.status == "COMPLETED":
            raise ConversationExpiredError("Cannot submit turns to a completed conversation")

        # Optimistic concurrency check
        if expected_version is not None and conv.version != expected_version:
            raise OptimisticLockError(
                f"Conversation version mismatch: expected {expected_version}, but conversation is at version {conv.version}."
            )

        current_version = conv.version

        # Step 1: Transcribe if VOICE turn
        transcript = ""
        asr_version = None
        if input_mode == "VOICE":
            if not audio_bytes:
                raise AudioValidationError("Audio data is required for voice turns")

            # Validate constraints
            meta = validate_audio_file(
                audio_bytes,
                max_bytes=self.settings.AUDIO_MAX_BYTES,
                max_seconds=self.settings.AUDIO_MAX_SECONDS,
            )

            async with transient_audio_file(audio_bytes, suffix=f".{meta.format}") as raw_path:
                norm_path = raw_path.with_name(f"norm_{raw_path.name}.wav")
                try:
                    await normalize_to_wav_16k(raw_path, norm_path)
                    asr_res = await self.speech_recognizer.transcribe(norm_path, language="kn")
                    transcript = asr_res.text.strip()
                    asr_version = asr_res.model_version
                finally:
                    norm_path.unlink(missing_ok=True)
        else:
            transcript = (text_input or "").strip()

        if not transcript:
            transcript = "..."

        # Step 2: Load current profile and state
        profile = await self._load_or_assemble_profile(conv)
        current_state = DialogueState(conv.state)
        current_intent = self._extract_intent_from_summary(conv.summary)

        # Step 3: Handle Confirmation State vs Discovery/Slot State
        next_state = current_state
        pending_confirmation_slot: Optional[str] = None
        missing: List[str] = IntentSlotResolver.get_missing_slots(current_intent, profile)

        if current_state == DialogueState.CONFIRMING:
            conf_analysis = analyze_confirmation(transcript)

            if conf_analysis.decision == ConfirmationDecision.AFFIRMED:
                # Mark pending critical slots as USER_CONFIRMED
                if profile.ownership and profile.ownership.requires_confirmation:
                    profile.ownership.assertion = ProvenanceAssertion.USER_CONFIRMED
                    profile.ownership.requires_confirmation = False

                missing = IntentSlotResolver.get_missing_slots(current_intent, profile)
                if not missing and not profile.conflicts:
                    next_state = DialogueStateMachine.transition(current_state, DialogueState.EVALUATION_READY)
                else:
                    next_state = DialogueStateMachine.transition(current_state, DialogueState.COLLECTING_SLOTS)

            elif conf_analysis.decision == ConfirmationDecision.CORRECTED:
                # Spoken correction: feed through M2 profile assembler
                profile = self.profile_assembler.assemble_turn(
                    current_profile=profile,
                    utterance=conf_analysis.corrected_part or transcript,
                )
                missing = IntentSlotResolver.get_missing_slots(current_intent, profile)
                next_state = DialogueStateMachine.transition(current_state, DialogueState.COLLECTING_SLOTS)

            elif conf_analysis.decision == ConfirmationDecision.REJECTED:
                # Rejection without new value: clear tenure or ambiguous slot and re-ask
                if profile.ownership:
                    profile.ownership = None
                missing = IntentSlotResolver.get_missing_slots(current_intent, profile)
                next_state = DialogueStateMachine.transition(current_state, DialogueState.COLLECTING_SLOTS)

            else:  # UNCLEAR
                missing = IntentSlotResolver.get_missing_slots(current_intent, profile)
                next_state = DialogueStateMachine.transition(current_state, DialogueState.CLARIFYING)

        else:
            # GREETING, COLLECTING_SLOTS, CLARIFYING, or RESPONDING
            # Extract intent and entities using SchemeExtractor
            extracted_intent = current_intent
            try:
                extraction_res = await self.extractor.extract(
                    utterance=transcript,
                )
                # Upgrade intent if non-generic
                if extraction_res.intent not in (Intent.GREETING, Intent.UNKNOWN):
                    extracted_intent = extraction_res.intent
                    current_intent = extracted_intent
            except Exception as e:
                logger.warning(f"NLU extraction fallback on turn: {e}")

            # Assemble profile facts using M2 normalization
            profile = self.profile_assembler.assemble_turn(
                current_profile=profile,
                utterance=transcript,
            )

            # Evaluate missing slots and conflicts
            missing = IntentSlotResolver.get_missing_slots(current_intent, profile)

            # Check if critical slot needs confirmation
            if profile.ownership and profile.ownership.requires_confirmation and profile.ownership.assertion == ProvenanceAssertion.USER_STATED:
                pending_confirmation_slot = "land_ownership"
                next_state = DialogueStateMachine.transition(current_state, DialogueState.CONFIRMING)
            elif profile.land_area and profile.land_area.is_ambiguous:
                next_state = DialogueStateMachine.transition(current_state, DialogueState.CLARIFYING)
            elif not missing and not profile.conflicts:
                next_state = DialogueStateMachine.transition(current_state, DialogueState.EVALUATION_READY)
            else:
                next_state = (
                    DialogueStateMachine.transition(current_state, DialogueState.COLLECTING_SLOTS)
                    if current_state != DialogueState.COLLECTING_SLOTS
                    else current_state
                )

        # Step 4: Determine next question and response
        next_missing_slot = IntentSlotResolver.get_next_missing_slot(current_intent, profile)
        recommendation_text: Optional[str] = None

        if next_state == DialogueState.EVALUATION_READY:
            try:
                from app.core.scheme.enums import RecommendationStatus
                from app.services.recommendation_service import RecommendationService
                rec_service = RecommendationService(self.db)
                rec_results = await rec_service.evaluate_for_farmer(
                    farmer_id=farmer_id,
                    conversation_id=conversation_id,
                    profile=profile,
                    intent=current_intent,
                )
                if rec_results:
                    matched_or_verif = [
                        r for r in rec_results
                        if r.recommendation_status in (
                            RecommendationStatus.POTENTIALLY_MATCHED,
                            RecommendationStatus.VERIFICATION_REQUIRED,
                        )
                    ]
                    top_rec = matched_or_verif[0] if matched_or_verif else rec_results[0]
                    recommendation_text = top_rec.explanation_trace.kannada_explanation
            except Exception as rec_err:
                logger.warning(f"Scheme recommendation evaluation fallback on turn: {rec_err}")

        assistant_text = generate_dialogue_response(
            state=next_state,
            intent=current_intent,
            profile=profile,
            next_missing_slot=next_missing_slot,
            pending_confirmation_slot=pending_confirmation_slot,
            recommendation_text=recommendation_text,
        )

        # Step 5: Synthesize TTS with graceful text fallback
        audio_url: Optional[str] = None
        speech_available = False
        try:
            tts_res = await self.speech_synthesizer.synthesize(
                text=assistant_text,
                language="kn",
            )
            audio_id = await self.audio_store.store(
                audio_bytes=tts_res.audio_bytes,
                owner_id=str(farmer_id),
            )
            audio_url = f"/api/v1/voice/audio/{audio_id}"
            speech_available = True
        except Exception as tts_err:
            logger.warning(f"TTS synthesis degraded gracefully on turn: {tts_err}")
            speech_available = False

        # Step 6: Persist Turn, Profile, Slots and Conversation state inside DB transaction
        turn_number = await self._get_next_turn_number(conversation_id)
        turn = ConversationTurn(
            conversation_id=conversation_id,
            farmer_id=farmer_id,
            turn_number=turn_number,
            role="FARMER",
            input_mode=input_mode,
            transcript_text=transcript,
            assistant_text=assistant_text,
            asr_model_version=asr_version,
            tts_model_version=self.settings.TTS_MODEL_VERSION if speech_available else None,
            status="COMPLETED",
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(turn)
        await self.db.flush()

        # Persist individual structured slot values
        await self._persist_slots(conversation_id, farmer_id, turn.id, profile)

        # Update FarmerProfile persistent record
        await self._persist_farmer_profile(farmer_id, profile)

        # Optimistic locking update on Conversation
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id, Conversation.version == current_version)
            .values(
                state=next_state.value,
                version=current_version + 1,
                summary=f"Intent: {current_intent.value} | Missing: {', '.join(missing)}",
                last_activity_at=datetime.now(timezone.utc),
            )
        )
        res = await self.db.execute(stmt)
        if res.rowcount == 0:
            raise OptimisticLockError("Concurrent modification on conversation session. Please retry.")

        await self.db.commit()

        return TurnResponse(
            turn_id=str(turn.id),
            turn_number=turn_number,
            conversation_id=str(conversation_id),
            dialogue_state=next_state,
            transcript_text=transcript,
            assistant_text=assistant_text,
            audio_url=audio_url,
            speech_available=speech_available,
            missing_slots=missing,
            next_required_slot=next_missing_slot,
            is_ready_for_evaluation=next_state == DialogueState.EVALUATION_READY,
            conflicts=profile.conflicts,
            extracted_intent=current_intent.value,
            version=current_version + 1,
        )

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    async def _load_conversation_enforcing_ownership(
        self,
        conversation_id: uuid.UUID,
        farmer_id: uuid.UUID,
    ) -> Conversation:
        """Load conversation ensuring BOLA ownership invariant."""
        conv = await self.db.get(Conversation, conversation_id)
        if not conv:
            raise ResourceNotFoundError(f"Conversation '{conversation_id}' not found")

        if conv.farmer_id != farmer_id:
            raise AuthorizationError("Access denied: You do not own this conversation")

        return conv

    async def _load_or_assemble_profile(self, conversation: Conversation) -> AgriculturalProfile:
        """Reconstruct the validated AgriculturalProfile from persistent slots or FarmerProfile."""
        farmer_profile = await self.db.execute(
            select(FarmerProfile).where(FarmerProfile.farmer_id == conversation.farmer_id)
        )
        fp = farmer_profile.scalar_one_or_none()
        if fp and fp.profile_data:
            try:
                return AgriculturalProfile.model_validate(fp.profile_data)
            except Exception:
                pass

        return AgriculturalProfile()

    async def _persist_farmer_profile(self, farmer_id: uuid.UUID, profile: AgriculturalProfile) -> None:
        """Save structured profile facts to the farmer_profiles table."""
        stmt = select(FarmerProfile).where(FarmerProfile.farmer_id == farmer_id)
        res = await self.db.execute(stmt)
        fp = res.scalar_one_or_none()

        prof_dict = profile.model_dump(mode="json")

        if fp:
            fp.profile_data = prof_dict
            fp.profile_version += 1
            fp.updated_at = datetime.now(timezone.utc)
        else:
            fp = FarmerProfile(
                farmer_id=farmer_id,
                profile_data=prof_dict,
                profile_version=1,
            )
            self.db.add(fp)

        await self.db.flush()

    async def _persist_slots(
        self,
        conversation_id: uuid.UUID,
        farmer_id: uuid.UUID,
        turn_id: uuid.UUID,
        profile: AgriculturalProfile,
    ) -> None:
        """Persist individual structured slot values with provenance."""
        slot_mappings: List[Tuple[str, Any, str, str]] = []

        if profile.district:
            slot_mappings.append(("district", profile.district.model_dump(), "CONFIRMED", "USER_STATED"))
        if profile.taluk:
            slot_mappings.append(("taluk", profile.taluk.model_dump(), "CONFIRMED", "USER_STATED"))
        if profile.primary_crop:
            slot_mappings.append(("crop", profile.primary_crop.model_dump(), "CONFIRMED", "USER_STATED"))
        if profile.land_area:
            status = "PROPOSED" if profile.land_area.is_ambiguous else "CONFIRMED"
            slot_mappings.append(("land_area", profile.land_area.model_dump(mode="json"), status, "USER_STATED"))
        if profile.ownership:
            prov = profile.ownership.assertion.value
            status = "PROPOSED" if profile.ownership.requires_confirmation else "CONFIRMED"
            slot_mappings.append(("land_ownership", profile.ownership.model_dump(), status, prov))
        if profile.irrigation_type:
            slot_mappings.append(("irrigation", profile.irrigation_type.model_dump(), "CONFIRMED", "USER_STATED"))
        if profile.season:
            slot_mappings.append(("season", profile.season.model_dump(), "CONFIRMED", "USER_STATED"))

        for key, val, status, prov in slot_mappings:
            # Query latest version
            stmt = (
                select(ConversationSlot)
                .where(ConversationSlot.conversation_id == conversation_id, ConversationSlot.slot_key == key)
                .order_by(ConversationSlot.slot_version.desc())
                .limit(1)
            )
            res = await self.db.execute(stmt)
            existing = res.scalar_one_or_none()
            next_ver = (existing.slot_version + 1) if existing else 1

            slot = ConversationSlot(
                conversation_id=conversation_id,
                farmer_id=farmer_id,
                slot_key=key,
                raw_value=str(val.get("matched_alias") or val.get("original_utterance") or val),
                canonical_value=val,
                slot_status=status,
                provenance=prov,
                source_turn_id=turn_id,
                slot_version=next_ver,
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(slot)

        await self.db.flush()

    async def _get_next_turn_number(self, conversation_id: uuid.UUID) -> int:
        """Compute the next incremental turn number for a conversation."""
        stmt = select(func.max(ConversationTurn.turn_number)).where(
            ConversationTurn.conversation_id == conversation_id
        )
        res = await self.db.execute(stmt)
        max_turn = res.scalar()
        return (max_turn or 0) + 1

    def _extract_intent_from_summary(self, summary: Optional[str]) -> Intent:
        """Parse the active intent from conversation metadata summary."""
        if not summary:
            return Intent.FIND_SCHEMES
        for item in Intent:
            if item.value in summary:
                return item
        return Intent.FIND_SCHEMES

    def _format_conversation_response(
        self,
        conversation: Conversation,
        profile: AgriculturalProfile,
        missing_slots: List[str],
        next_question: Optional[str] = None,
    ) -> ConversationResponse:
        """Format an internal Conversation entity into a public ConversationResponse."""
        intent = self._extract_intent_from_summary(conversation.summary)
        return ConversationResponse(
            conversation_id=str(conversation.id),
            farmer_id=str(conversation.farmer_id),
            status=conversation.status,
            state=DialogueState(conversation.state),
            language=conversation.language,
            current_intent=intent.value,
            summary=conversation.summary,
            profile=profile.model_dump(mode="json"),
            missing_slots=missing_slots,
            conflicts=profile.conflicts,
            next_question=next_question,
            version=conversation.version,
            last_activity_at=conversation.last_activity_at,
            created_at=conversation.created_at,
        )
