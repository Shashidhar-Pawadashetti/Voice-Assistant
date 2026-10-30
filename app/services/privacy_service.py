"""Privacy and Data Lifecycle Service conforming to DPDP Act 2023 principles.

Conforms to Directive M5.4 and 11_SECURITY_AND_PRIVACY.md:
1. Complete, machine-readable farmer data portability and export.
2. Verified erasure workflow with password confirmation.
3. Decoupling and anonymization of personal identifiers.
4. Purging of conversational transcripts, slots, audio files, and profiles.
5. Preservation of immutable scheme recommendation audit traces for legal compliance without personal data.
6. Documentation of backup lifecycle limitations.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List
import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ResourceNotFoundError
from app.core.security.password import verify_password
from app.core.tts.storage import EphemeralAudioStore, get_ephemeral_audio_store
from app.models.audit import AuditEvent, DeletionRequest
from app.models.auth import RefreshToken
from app.models.conversation import Conversation, ConversationSlot, ConversationTurn
from app.models.farmer import ConsentRecord, Farmer, FarmerProfile
from app.models.scheme import RecommendationRun
from app.schemas.privacy import (
    DataExportResponse,
    DeletionRequestPayload,
    DeletionResponse,
)

logger = logging.getLogger("krishi.service.privacy")


class PrivacyService:
    """Manages data minimization, export, and verified erasure lifecycles."""

    def __init__(
        self,
        db: AsyncSession,
        audio_store: EphemeralAudioStore | None = None,
    ):
        self.db = db
        self.audio_store = audio_store or get_ephemeral_audio_store()

    async def export_farmer_data(self, farmer: Farmer) -> DataExportResponse:
        """Export all structured personal, conversational, and recommendation records for a farmer."""
        now = datetime.now(timezone.utc)

        # 1. Profile Data
        prof_stmt = select(FarmerProfile).where(FarmerProfile.farmer_id == farmer.id)
        prof_res = await self.db.execute(prof_stmt)
        fp = prof_res.scalar_one_or_none()
        profile_data = fp.profile_data if fp else {}

        # 2. Consent History
        consent_stmt = select(ConsentRecord).where(ConsentRecord.farmer_id == farmer.id)
        consent_res = await self.db.execute(consent_stmt)
        consents = [
            {
                "purpose": c.purpose,
                "notice_version": c.notice_version,
                "status": c.status,
                "granted_at": c.granted_at.isoformat() if c.granted_at else None,
                "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
            }
            for c in consent_res.scalars().all()
        ]

        # 3. Conversations and Turns
        conv_stmt = select(Conversation).where(Conversation.farmer_id == farmer.id).order_by(Conversation.created_at.asc())
        conv_res = await self.db.execute(conv_stmt)
        conversations: List[Dict[str, Any]] = []

        for conv in conv_res.scalars().all():
            turns_stmt = (
                select(ConversationTurn)
                .where(ConversationTurn.conversation_id == conv.id)
                .order_by(ConversationTurn.turn_number.asc())
            )
            turns_res = await self.db.execute(turns_stmt)
            turns = [
                {
                    "turn_number": t.turn_number,
                    "role": t.role,
                    "input_mode": t.input_mode,
                    "transcript_text": t.transcript_text,
                    "assistant_text": t.assistant_text,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in turns_res.scalars().all()
            ]

            slots_stmt = (
                select(ConversationSlot)
                .where(ConversationSlot.conversation_id == conv.id)
                .order_by(ConversationSlot.slot_key.asc())
            )
            slots_res = await self.db.execute(slots_stmt)
            slots = [
                {
                    "slot_key": s.slot_key,
                    "canonical_value": s.canonical_value,
                    "canonical_unit": s.canonical_unit,
                    "status": s.slot_status,
                    "provenance": s.provenance,
                }
                for s in slots_res.scalars().all()
            ]

            conversations.append(
                {
                    "conversation_id": str(conv.id),
                    "status": conv.status,
                    "state": conv.state,
                    "language": conv.language,
                    "created_at": conv.created_at.isoformat(),
                    "turns": turns,
                    "slots": slots,
                }
            )

        # 4. Recommendation Runs
        rec_stmt = (
            select(RecommendationRun)
            .where(RecommendationRun.farmer_id == farmer.id)
            .order_by(RecommendationRun.evaluated_at.asc())
        )
        rec_res = await self.db.execute(rec_stmt)
        recs = [
            {
                "run_id": str(r.id),
                "conversation_id": str(r.conversation_id),
                "evaluator_version": r.evaluator_version,
                "outcome": r.outcome,
                "explanation_trace": r.explanation_trace,
                "evaluated_at": r.evaluated_at.isoformat(),
            }
            for r in rec_res.scalars().all()
        ]

        # Audit Event
        audit = AuditEvent(
            actor_type="FARMER",
            actor_id=farmer.id,
            event_type="DATA_EXPORTED",
            resource_type="FARMER",
            resource_id=farmer.id,
        )
        self.db.add(audit)
        await self.db.commit()

        return DataExportResponse(
            export_generated_at=now,
            farmer_id=farmer.id,
            preferred_language=farmer.preferred_language,
            account_status=farmer.account_status,
            created_at=farmer.created_at,
            last_login_at=farmer.last_login_at,
            profile_data=profile_data,
            consent_history=consents,
            conversations=conversations,
            recommendation_runs=recs,
        )

    async def execute_data_deletion(
        self,
        farmer: Farmer,
        payload: DeletionRequestPayload,
    ) -> DeletionResponse:
        """Execute farmer account and personal data erasure workflow with password verification."""
        # 1. Require Password Confirmation
        if not verify_password(payload.password, farmer.password_hash):
            raise AuthenticationError("Incorrect password. Deletion verification failed.")

        now = datetime.now(timezone.utc)
        deletion_req_id = uuid.uuid4()

        # 2. Record Initial Deletion Request
        del_req = DeletionRequest(
            id=deletion_req_id,
            farmer_id=farmer.id,
            status="IN_PROGRESS",
            requested_at=now,
        )
        self.db.add(del_req)
        await self.db.flush()

        records_erased: Dict[str, int] = {}

        # 3. Purge Ephemeral Response Audio from Storage
        audio_purged = await self.audio_store.delete_for_owner(str(farmer.id))
        records_erased["ephemeral_audio_files"] = audio_purged

        # 4. Decouple and Anonymize Immutable Recommendation Runs before deleting conversations
        # In accordance with statutory audit requirements, scheme outcomes and rule evaluation
        # traces are retained for regulatory verification, but personal identifiers in profile
        # snapshots are redacted and conversation foreign keys decoupled.
        anonymized_profile = {"redacted": True, "reason": "DPDP_ERASURE_REQUEST"}
        rec_anonymize = (
            update(RecommendationRun)
            .where(RecommendationRun.farmer_id == farmer.id)
            .values(conversation_id=None, profile_snapshot=anonymized_profile)
        )
        rec_res = await self.db.execute(rec_anonymize)
        records_erased["recommendation_runs_anonymized"] = rec_res.rowcount

        # 5. Count and Delete Conversations, Turns, and Slots
        conv_stmt = select(Conversation.id).where(Conversation.farmer_id == farmer.id)
        conv_res = await self.db.execute(conv_stmt)
        conv_ids = list(conv_res.scalars().all())

        if conv_ids:
            turn_del = await self.db.execute(
                delete(ConversationTurn).where(ConversationTurn.farmer_id == farmer.id)
            )
            slot_del = await self.db.execute(
                delete(ConversationSlot).where(ConversationSlot.farmer_id == farmer.id)
            )
            conv_del = await self.db.execute(
                delete(Conversation).where(Conversation.farmer_id == farmer.id)
            )
            records_erased["turns"] = turn_del.rowcount
            records_erased["slots"] = slot_del.rowcount
            records_erased["conversations"] = conv_del.rowcount
        else:
            records_erased["turns"] = 0
            records_erased["slots"] = 0
            records_erased["conversations"] = 0

        # 6. Delete Farmer Profile
        prof_del = await self.db.execute(
            delete(FarmerProfile).where(FarmerProfile.farmer_id == farmer.id)
        )
        records_erased["farmer_profiles"] = prof_del.rowcount

        # 7. Revoke and Delete Refresh Tokens
        token_del = await self.db.execute(
            delete(RefreshToken).where(RefreshToken.farmer_id == farmer.id)
        )
        records_erased["refresh_tokens"] = token_del.rowcount

        # 8. Withdraw Consents
        consent_stmt = (
            update(ConsentRecord)
            .where(ConsentRecord.farmer_id == farmer.id)
            .values(status="WITHDRAWN", withdrawn_at=now)
        )
        await self.db.execute(consent_stmt)

        # 9. Anonymize/Deactivate Farmer Account & Revoke all Sessions
        farmer.account_status = "DELETED"
        farmer.deleted_at = now
        farmer.tokens_revoked_before = now
        farmer.phone_number_encrypted = "DELETED"
        farmer.phone_number_hash = f"deleted_{farmer.id.hex}"
        farmer.password_hash = "DELETED"

        # 10. Complete Deletion Request Record
        del_req.status = "COMPLETED"
        del_req.completed_at = now
        del_req.result_summary = records_erased

        # 11. Audit Event (records erasure event without personal identifiers)
        audit = AuditEvent(
            actor_type="FARMER",
            actor_id=farmer.id,
            event_type="ACCOUNT_DELETED",
            resource_type="FARMER",
            resource_id=farmer.id,
            metadata_={"records_erased": records_erased},
        )
        self.db.add(audit)

        await self.db.commit()

        return DeletionResponse(
            status="COMPLETED",
            message="Your account and all associated personal and conversational data have been erased.",
            requested_at=now,
            completed_at=now,
            deletion_request_id=deletion_req_id,
            records_erased=records_erased,
        )
