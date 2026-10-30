"""Integration tests for database models, relationships, and constraints."""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.farmer import Farmer, FarmerProfile, ConsentRecord
from app.models.conversation import Conversation, ConversationTurn, ConversationSlot
from app.models.scheme import Scheme, SchemeRuleVersion, RecommendationRun
from app.models.job import Job
from app.models.audit import AuditEvent, DeletionRequest


@pytest.mark.asyncio
async def test_create_farmer_and_profile(db_session: AsyncSession):
    """Verify farmer creation with cascaded profile and consent record."""
    farmer_id = uuid.uuid4()
    farmer = Farmer(
        id=farmer_id,
        phone_number_encrypted="enc_token_12345",
        phone_number_hash="hash_abc123",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$fakehash",
        preferred_language="kn",
        account_status="ACTIVE",
    )
    profile = FarmerProfile(
        farmer_id=farmer_id,
        profile_data={"district": "DHARWAD", "crop": "SORGHUM"},
        profile_version=1,
    )
    consent = ConsentRecord(
        farmer_id=farmer_id,
        purpose="VOICE_PROCESSING",
        notice_version="v1.0",
        status="GRANTED",
        evidence_metadata={"ip": "127.0.0.1"},
    )

    db_session.add_all([farmer, profile, consent])
    await db_session.flush()

    # Query back
    stmt = select(Farmer).where(Farmer.id == farmer_id)
    result = await db_session.execute(stmt)
    saved_farmer = result.scalar_one()

    assert saved_farmer is not None
    assert saved_farmer.preferred_language == "kn"
    assert saved_farmer.account_status == "ACTIVE"


@pytest.mark.asyncio
async def test_conversation_turns_and_slots(db_session: AsyncSession):
    """Verify conversation, turn, and slot creation with unique constraint enforcement."""
    farmer_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    turn_id = uuid.uuid4()

    farmer = Farmer(
        id=farmer_id,
        phone_number_encrypted="enc_xyz",
        phone_number_hash="hash_xyz",
        password_hash="pwd_hash",
    )
    conv = Conversation(
        id=conv_id,
        farmer_id=farmer_id,
        state="COLLECTING_PROFILE",
    )
    turn = ConversationTurn(
        id=turn_id,
        conversation_id=conv_id,
        farmer_id=farmer_id,
        turn_number=1,
        role="FARMER",
        input_mode="VOICE",
        transcript_text="ನಾಲ್ಕು ಎಕರೆ ಜಮೀನಿದೆ",
    )
    slot = ConversationSlot(
        conversation_id=conv_id,
        farmer_id=farmer_id,
        slot_key="land_area",
        raw_value="ನಾಲ್ಕು ಎಕರೆ",
        canonical_value={"value": 4.0, "unit": "acre"},
        canonical_unit="acre",
        slot_status="CONFIRMED",
        provenance="USER_STATED",
        source_turn_id=turn_id,
        slot_version=1,
    )

    db_session.add_all([farmer, conv, turn, slot])
    await db_session.flush()

    # Verify duplicate turn number on same conversation triggers IntegrityError
    duplicate_turn = ConversationTurn(
        id=uuid.uuid4(),
        conversation_id=conv_id,
        farmer_id=farmer_id,
        turn_number=1,  # Duplicate
        role="ASSISTANT",
    )
    db_session.add(duplicate_turn)
    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_scheme_and_rule_version_model(db_session: AsyncSession):
    """Verify scheme and immutable rule version models."""
    scheme_id = uuid.uuid4()
    rule_ver_id = uuid.uuid4()

    scheme = Scheme(
        id=scheme_id,
        scheme_id="PM_KISAN",
        classification="REAL_GOVERNMENT",
        display_name="PM-KISAN",
        assistance_category="INCOME_SUPPORT",
        government_level="CENTRAL",
        active=True,
    )
    rule_version = SchemeRuleVersion(
        id=rule_ver_id,
        scheme_id=scheme_id,
        rule_version="0.0.0",
        definition={"official_source_urls": ["https://pmkisan.gov.in/"]},
        definition_hash="sha256hash123",
        verification_status="INCOMPLETE",
    )

    db_session.add_all([scheme, rule_version])
    await db_session.flush()

    stmt = select(Scheme).where(Scheme.scheme_id == "PM_KISAN")
    res = await db_session.execute(stmt)
    saved = res.scalar_one()

    assert saved.classification == "REAL_GOVERNMENT"
    assert saved.display_name == "PM-KISAN"


@pytest.mark.asyncio
async def test_job_and_audit_event_models(db_session: AsyncSession):
    """Verify job and audit event models."""
    farmer_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    job_id = uuid.uuid4()

    farmer = Farmer(
        id=farmer_id,
        phone_number_encrypted="enc_1",
        phone_number_hash="hash_1",
        password_hash="pwd_1",
    )
    conv = Conversation(id=conv_id, farmer_id=farmer_id)
    job = Job(
        id=job_id,
        farmer_id=farmer_id,
        conversation_id=conv_id,
        idempotency_key_hash="idem_hash_123",
        payload_hash="payload_hash_456",
        status="QUEUED",
        worker_type="TURN_ORCHESTRATOR",
    )
    audit = AuditEvent(
        actor_type="FARMER",
        actor_id=farmer_id,
        event_type="CONVERSATION_CREATED",
        resource_type="CONVERSATION",
        resource_id=conv_id,
        metadata_={"ip": "127.0.0.1"},
    )

    db_session.add_all([farmer, conv, job, audit])
    await db_session.flush()

    stmt = select(Job).where(Job.id == job_id)
    res = await db_session.execute(stmt)
    saved_job = res.scalar_one()

    assert saved_job.status == "QUEUED"
    assert saved_job.idempotency_key_hash == "idem_hash_123"
