"""Integration tests for DPDP Privacy Lifecycles: Data Portability and Erasure (M5.4)."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.conversations import get_conversation_service
from app.core.asr.mock import MockSpeechRecognizer
from app.core.llm.extractor import SchemeExtractor
from app.core.security.jwt import create_access_token
from app.core.security.password import hash_password
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore
from app.database import get_db_session
from app.main import create_app
from app.models.farmer import ConsentRecord, Farmer, FarmerProfile
from app.services.conversation_service import ConversationService
from tests.integration.test_voice_pipeline import DummyLanguageModel

FARMER_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


@pytest.fixture
async def seeded_farmer_with_history(db_session: AsyncSession, tmp_path) -> tuple[Farmer, EphemeralAudioStore]:
    audio_store = EphemeralAudioStore(storage_dir=tmp_path / "tts_responses")
    farmer = Farmer(
        id=FARMER_ID,
        phone_number_encrypted="enc_phone_val",
        phone_number_hash="phone_hash_val",
        password_hash=hash_password("FarmerSecretPwd!2026"),
        preferred_language="kn",
        account_status="ACTIVE",
    )
    profile = FarmerProfile(
        farmer_id=FARMER_ID,
        profile_data={"primary_crop": "RAGI", "district": "MANDYA"},
        profile_version=1,
    )
    consent = ConsentRecord(
        farmer_id=FARMER_ID,
        purpose="ACCOUNT",
        notice_version="2026.1",
        status="GRANTED",
        evidence_metadata={"initial": True},
    )
    db_session.add_all([farmer, profile, consent])
    await db_session.flush()

    # Save an audio file owned by farmer
    await audio_store.save(b"ephemeral audio payload", owner_id=str(FARMER_ID))

    return farmer, audio_store


@pytest.mark.asyncio
async def test_data_export_endpoint(
    db_session: AsyncSession,
    seeded_farmer_with_history: tuple[Farmer, EphemeralAudioStore],
):
    farmer, _ = seeded_farmer_with_history
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    token = create_access_token(farmer.id)
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/privacy/export", headers=headers)
        assert res.status_code == 200
        data = res.json()

        assert data["farmer_id"] == str(FARMER_ID)
        assert data["preferred_language"] == "kn"
        assert data["profile_data"]["primary_crop"] == "RAGI"
        assert len(data["consent_history"]) >= 1

        # Invariant: Never export password hash or symmetric encryption keys
        assert "password_hash" not in str(data)
        assert "enc_phone_val" not in str(data)


@pytest.mark.asyncio
async def test_data_deletion_workflow(
    db_session: AsyncSession,
    seeded_farmer_with_history: tuple[Farmer, EphemeralAudioStore],
):
    farmer, audio_store = seeded_farmer_with_history
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    from app.core.tts.storage import get_ephemeral_audio_store
    app.dependency_overrides[get_ephemeral_audio_store] = lambda: audio_store

    token = create_access_token(farmer.id)
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Invalid Password Confirmation Fails
        bad_pwd_res = await client.post(
            "/api/v1/privacy/delete",
            json={"password": "WrongPassword!"},
            headers=headers,
        )
        assert bad_pwd_res.status_code == 401

        # 2. Correct Password Confirmation Executes Deletion
        del_res = await client.post(
            "/api/v1/privacy/delete",
            json={"password": "FarmerSecretPwd!2026", "reason": "No longer farming"},
            headers=headers,
        )
        assert del_res.status_code == 200
        del_data = del_res.json()
        assert del_data["status"] == "COMPLETED"
        assert "records_erased" in del_data

        # 3. Subsequent attempts to use the access token fail because account is DELETED
        res_after = await client.get("/api/v1/auth/me", headers=headers)
        assert res_after.status_code == 401

        # 4. Check that audio files were purged
        assert await audio_store.delete_for_owner(str(FARMER_ID)) == 0
