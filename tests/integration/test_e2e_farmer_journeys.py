"""End-to-End Validation of Farmer Journeys A through E (Directive M7.3).

Journeys:
- Journey A: Registration, Consent, Login/Session Restoration, Logout.
- Journey B: Voice Conversation, Transcript, Assistant Audio, Fact Correction, History.
- Journey C: Scheme Recommendations, Verified Rules, PMFBY claim verification protection, DEMO_ONLY tagging, and Latest Run Ordering.
- Journey D: Cross-Farmer BOLA/IDOR Authorization, ID tampering, Audio Protection.
- Journey E: Data Portability Export, Verified DPDP Erasure, Anonymized Regulatory Retention.
"""

import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.conversations import get_conversation_service
from app.core.asr.mock import MockSpeechRecognizer
from app.core.llm.extractor import SchemeExtractor
from app.core.scheme.catalog import PM_KISAN_SCHEME, PMFBY_SCHEME
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore, get_ephemeral_audio_store
from app.database import get_db_session
from app.main import create_app
from app.models.conversation import Conversation
from app.models.farmer import ConsentRecord, Farmer, FarmerProfile
from app.models.scheme import RecommendationRun
from app.services.conversation_service import ConversationService
from tests.fixtures.audio_generator import make_test_wav
from tests.integration.test_voice_pipeline import DummyLanguageModel


@pytest.fixture
def e2e_conversation_service(db_session: AsyncSession, tmp_path):
    audio_store = EphemeralAudioStore(storage_dir=tmp_path / "tts_responses")
    asr = MockSpeechRecognizer()
    extractor = SchemeExtractor(llm=DummyLanguageModel())
    tts = MockSpeechSynthesizer()

    return ConversationService(
        db=db_session,
        speech_recognizer=asr,
        extractor=extractor,
        speech_synthesizer=tts,
        audio_store=audio_store,
    )


@pytest.mark.asyncio
async def test_journey_a_registration_session_restoration_and_logout(db_session: AsyncSession):
    """Journey A: Registration, session restoration, and logout."""
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        phone = "9888777666"
        pwd = "FarmerSecretPassword!2026"

        # 1. Register with valid farmer details and consent
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": phone,
                "password": pwd,
                "preferred_language": "kn",
                "consent_given": True,
            },
        )
        assert reg_res.status_code == 201
        reg_body = reg_res.json()
        assert "farmer" in reg_body
        assert "tokens" in reg_body
        access_token = reg_body["tokens"]["access_token"]
        refresh_token = reg_body["tokens"]["refresh_token"]

        # 2. Verify login/session via /me endpoint
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_res.status_code == 200
        assert me_res.json()["account_status"] == "ACTIVE"

        # 3. Simulate page reload and session restoration using refresh token
        restore_res = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert restore_res.status_code == 200
        new_tokens = restore_res.json()
        restored_access_token = new_tokens["access_token"]
        assert restored_access_token != access_token

        # Verify restored session is active
        restored_me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {restored_access_token}"},
        )
        assert restored_me.status_code == 200

        # 4. Logout
        logout_res = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {restored_access_token}"},
            json={"refresh_token": new_tokens["refresh_token"]},
        )
        assert logout_res.status_code == 200

        # 5. Verify session is invalidated
        invalid_me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {restored_access_token}"},
        )
        assert invalid_me.status_code == 401


@pytest.mark.asyncio
async def test_journey_b_voice_conversation_fact_correction_and_persistence(
    db_session: AsyncSession,
    e2e_conversation_service: ConversationService,
):
    """Journey B: Voice conversation, assistant audio, fact correction, and history persistence."""
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_conversation_service] = lambda: e2e_conversation_service
    app.dependency_overrides[get_ephemeral_audio_store] = lambda: e2e_conversation_service.audio_store

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register and login
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "9777666555",
                "password": "VoiceConversation!2026",
                "consent_given": True,
            },
        )
        access_token = reg_res.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 1. Start a conversation
        create_res = await client.post("/api/v1/conversations", json={"language": "kn"}, headers=headers)
        assert create_res.status_code == 201
        conv_id = create_res.json()["conversation_id"]

        # 2. Submit a Kannada voice recording
        audio_wav = make_test_wav(duration_seconds=2.0)
        files = {"file": ("recording.wav", io.BytesIO(audio_wav), "audio/wav")}
        data = {"language": "kn", "client_turn_id": "turn_voice_1", "expected_version": 1}

        voice_res = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/voice",
            files=files,
            data=data,
            headers=headers,
        )
        assert voice_res.status_code == 200
        voice_body = voice_res.json()
        assert "transcript_text" in voice_body
        assert "assistant_text" in voice_body
        assert "audio_url" in voice_body
        audio_url = voice_body["audio_url"]
        assert audio_url.startswith("/api/v1/voice/audio/")

        # 3. Verify audio playback endpoint with authentication
        audio_res = await client.get(audio_url, headers=headers)
        assert audio_res.status_code == 200
        assert audio_res.headers["content-type"] == "audio/wav"
        assert len(audio_res.content) > 0

        # 4. Correct an agricultural fact via follow-up turn (e.g. land size corrected to 3 acres)
        correction_res = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನನ್ನ ಬಳಿ ೩ ಎಕರೆ ಜಮೀನು ಇದೆ", "expected_version": 2},
            headers=headers,
        )
        assert correction_res.status_code == 200

        # 5. Reload and verify turn history
        history_res = await client.get(f"/api/v1/conversations/{conv_id}/turns", headers=headers)
        assert history_res.status_code == 200
        history_turns = history_res.json()["turns"]
        assert len(history_turns) >= 2


@pytest.mark.asyncio
async def test_journey_c_scheme_recommendation_and_governance(
    db_session: AsyncSession,
    e2e_conversation_service: ConversationService,
):
    """Journey C: Scheme recommendations, verification status, DEMO_ONLY badges, and history ordering."""
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_conversation_service] = lambda: e2e_conversation_service
    app.dependency_overrides[get_ephemeral_audio_store] = lambda: e2e_conversation_service.audio_store

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register and login
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "9666444333",
                "password": "SchemeGovPass!2026",
                "consent_given": True,
            },
        )
        access_token = reg_res.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 1. Create conversation with crop insurance intent
        conv_res = await client.post(
            "/api/v1/conversations",
            json={"language": "kn", "initial_intent": "CROP_INSURANCE"},
            headers=headers,
        )
        conv_id = conv_res.json()["conversation_id"]

        # 2. Provide slots to complete profile
        await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನಾನು ಧಾರವಾಡ ಜಿಲ್ಲೆಯ ರೈತ, ೫ ಎಕರೆ ಜಮೀನಿನಲ್ಲಿ ಜೋಳ ಬೆಳೆದಿದ್ದೇನೆ", "expected_version": 1},
            headers=headers,
        )

        # 3. Trigger scheme evaluation
        eval_res = await client.post(
            f"/api/v1/conversations/{conv_id}/recommendations",
            headers=headers,
        )
        assert eval_res.status_code == 200
        recs = eval_res.json()["recommendations"]
        assert len(recs) > 0

        # 4. Verify PMFBY real-scheme governance invariants:
        pmfby_rec = next((r for r in recs if r["scheme_id"] == "PMFBY"), None)
        assert pmfby_rec is not None
        assert pmfby_rec["classification"] == "REAL_GOVERNMENT"
        assert pmfby_rec["demo_only"] is False
        assert pmfby_rec["official_verification_required"] is True
        # Invariant: PMFBY CANNOT present an unverified final entitlement claim without official verification
        assert pmfby_rec["recommendation_status"] in (
            "POTENTIALLY_MATCHED",
            "NEEDS_MORE_INFORMATION",
            "RULES_NOT_VERIFIED",
        )

        # 5. Verify every synthetic scheme has demo_only = True
        for r in recs:
            if r["classification"] == "SYNTHETIC_DEMO":
                assert r["demo_only"] is True

        # 6. Verify Recommendation History ordering (latest run first)
        hist_res = await client.get(
            f"/api/v1/conversations/{conv_id}/recommendations",
            headers=headers,
        )
        assert hist_res.status_code == 200
        hist_runs = hist_res.json()
        assert len(hist_runs) > 0
        # If multiple runs exist, ensure descending order by evaluated_at
        if len(hist_runs) > 1:
            for i in range(len(hist_runs) - 1):
                assert hist_runs[i]["evaluated_at"] >= hist_runs[i + 1]["evaluated_at"]


@pytest.mark.asyncio
async def test_journey_d_cross_farmer_authorization_and_audio_protection(
    db_session: AsyncSession,
    e2e_conversation_service: ConversationService,
):
    """Journey D: Cross-farmer BOLA/IDOR protection and audio security."""
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_conversation_service] = lambda: e2e_conversation_service
    app.dependency_overrides[get_ephemeral_audio_store] = lambda: e2e_conversation_service.audio_store

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Farmer A
        reg_a = await client.post(
            "/api/v1/auth/register",
            json={"phone_number": "9111111111", "password": "FarmerAPass!2026", "consent_given": True},
        )
        token_a = reg_a.json()["tokens"]["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Create Farmer B
        reg_b = await client.post(
            "/api/v1/auth/register",
            json={"phone_number": "9222222222", "password": "FarmerBPass!2026", "consent_given": True},
        )
        token_b = reg_b.json()["tokens"]["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Farmer A creates a conversation
        conv_a_res = await client.post("/api/v1/conversations", json={"language": "kn"}, headers=headers_a)
        conv_a_id = conv_a_res.json()["conversation_id"]

        # Farmer A creates a voice turn (generates audio)
        audio_wav = make_test_wav(duration_seconds=1.5)
        files = {"file": ("turn.wav", io.BytesIO(audio_wav), "audio/wav")}
        voice_res = await client.post(
            f"/api/v1/conversations/{conv_a_id}/turns/voice",
            files=files,
            data={"language": "kn", "expected_version": 1},
            headers=headers_a,
        )
        audio_url = voice_res.json()["audio_url"]

        # Farmer A can access own audio
        audio_a_res = await client.get(audio_url, headers=headers_a)
        assert audio_a_res.status_code == 200

        # ATTACK 1: Farmer B attempts to access Farmer A's conversation
        b_access_conv = await client.get(f"/api/v1/conversations/{conv_a_id}", headers=headers_b)
        assert b_access_conv.status_code in (403, 404)

        # ATTACK 2: Farmer B attempts to access Farmer A's protected audio
        b_access_audio = await client.get(audio_url, headers=headers_b)
        assert b_access_audio.status_code in (403, 404)

        # ATTACK 3: Unauthenticated caller attempts to access protected audio
        anon_access_audio = await client.get(audio_url)
        assert anon_access_audio.status_code == 401


@pytest.mark.asyncio
async def test_journey_e_privacy_export_and_verified_erasure(
    db_session: AsyncSession,
    e2e_conversation_service: ConversationService,
):
    """Journey E: DPDP Act 2023 data export, verified deletion, and anonymized regulatory retention."""
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_conversation_service] = lambda: e2e_conversation_service
    app.dependency_overrides[get_ephemeral_audio_store] = lambda: e2e_conversation_service.audio_store

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        phone = "9333333333"
        pwd = "DeleteTestPass!2026"

        reg_res = await client.post(
            "/api/v1/auth/register",
            json={"phone_number": phone, "password": pwd, "consent_given": True},
        )
        token = reg_res.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        farmer_id = reg_res.json()["farmer"]["id"]

        # Create conversation and turn
        conv_res = await client.post("/api/v1/conversations", json={"language": "kn"}, headers=headers)
        conv_id = conv_res.json()["conversation_id"]
        await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನನ್ನ ಹೆಸರು ರಮೇಶ್", "expected_version": 1},
            headers=headers,
        )

        # 1. Export Data: Verify machine-readable export belongs only to this farmer
        export_res = await client.get("/api/v1/privacy/export", headers=headers)
        assert export_res.status_code == 200
        export_data = export_res.json()
        assert export_data["farmer_id"] == farmer_id
        assert len(export_data["conversations"]) == 1

        # 2. Execute verified account deletion with password
        del_res = await client.post(
            "/api/v1/privacy/delete",
            json={"password": pwd, "confirmation": "DELETE_MY_ACCOUNT"},
            headers=headers,
        )
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "COMPLETED"

        # 3. Verify session is now revoked
        post_del_me = await client.get("/api/v1/auth/me", headers=headers)
        assert post_del_me.status_code == 401

        # 4. Verify in DB: Personal data and conversations are erased, but consent audit records are retained as WITHDRAWN
        farmer_uuid = uuid.UUID(farmer_id)
        farmer_row = await db_session.get(Farmer, farmer_uuid)
        assert farmer_row.account_status == "DELETED"
        assert farmer_row.phone_number_encrypted == "DELETED"
        assert farmer_row.password_hash == "DELETED"

        convs = await db_session.execute(select(Conversation).where(Conversation.farmer_id == farmer_uuid))
        assert len(list(convs.scalars().all())) == 0

        # Consents marked WITHDRAWN for legal compliance
        consents = await db_session.execute(select(ConsentRecord).where(ConsentRecord.farmer_id == farmer_uuid))
        consent_list = list(consents.scalars().all())
        assert len(consent_list) > 0
        for c in consent_list:
            assert c.status == "WITHDRAWN"
