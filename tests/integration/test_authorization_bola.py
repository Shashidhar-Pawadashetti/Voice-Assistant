"""Integration tests for Identity-Derived Authorization and BOLA/IDOR Defenses (M5.2)."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.conversations import get_conversation_service
from app.core.asr.mock import MockSpeechRecognizer
from app.core.llm.extractor import SchemeExtractor
from app.core.security.jwt import create_access_token
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore
from app.database import get_db_session
from app.main import create_app
from app.models.farmer import Farmer
from app.services.conversation_service import ConversationService
from tests.integration.test_voice_pipeline import DummyLanguageModel

FARMER_A_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
FARMER_B_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
async def two_seeded_farmers(db_session: AsyncSession) -> tuple[Farmer, Farmer]:
    fa = Farmer(
        id=FARMER_A_ID,
        phone_number_encrypted="enc_a",
        phone_number_hash="hash_a",
        password_hash="pwd_a",
        preferred_language="kn",
        account_status="ACTIVE",
    )
    fb = Farmer(
        id=FARMER_B_ID,
        phone_number_encrypted="enc_b",
        phone_number_hash="hash_b",
        password_hash="pwd_b",
        preferred_language="kn",
        account_status="ACTIVE",
    )
    db_session.add_all([fa, fb])
    await db_session.flush()
    return fa, fb


@pytest.fixture
def test_conversation_service(db_session: AsyncSession, tmp_path):
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
async def test_unauthenticated_requests_rejected_across_all_protected_routes(
    db_session: AsyncSession,
):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dummy_id = uuid.uuid4()

        # Conversations
        res1 = await client.post("/api/v1/conversations", json={"language": "kn"})
        assert res1.status_code == 401
        assert res1.json()["error"]["code"] == "UNAUTHORIZED"

        res2 = await client.get("/api/v1/conversations")
        assert res2.status_code == 401

        res3 = await client.get(f"/api/v1/conversations/{dummy_id}")
        assert res3.status_code == 401

        # Recommendations
        res4 = await client.post(f"/api/v1/conversations/{dummy_id}/recommendations")
        assert res4.status_code == 401

        res5 = await client.get(f"/api/v1/conversations/{dummy_id}/recommendations")
        assert res5.status_code == 401

        # Voice endpoints
        res6 = await client.post("/api/v1/voice/turn")
        assert res6.status_code == 401

        res7 = await client.get("/api/v1/voice/audio/11223344556677889900aabbccddeeff")
        assert res7.status_code == 401

        # Privacy endpoints
        res8 = await client.get("/api/v1/privacy/export")
        assert res8.status_code == 401

        res9 = await client.post("/api/v1/privacy/delete", json={"password": "any"})
        assert res9.status_code == 401


@pytest.mark.asyncio
async def test_cross_farmer_bola_isolation_and_header_spoofing_defense(
    db_session: AsyncSession,
    two_seeded_farmers: tuple[Farmer, Farmer],
    test_conversation_service: ConversationService,
):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_conversation_service] = lambda: test_conversation_service

    token_a = create_access_token(FARMER_A_ID)
    token_b = create_access_token(FARMER_B_ID)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Farmer A creates a conversation
        create_resp = await client.post(
            "/api/v1/conversations",
            json={"language": "kn"},
            headers=headers_a,
        )
        assert create_resp.status_code == 201
        conv_id = create_resp.json()["conversation_id"]

        # 2. Farmer B attempts to access Farmer A's conversation -> 403 Forbidden
        get_b_resp = await client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=headers_b,
        )
        assert get_b_resp.status_code == 403
        assert get_b_resp.json()["error"]["code"] == "FORBIDDEN"

        # 3. Farmer B attempts to submit a turn to Farmer A's conversation -> 403 Forbidden
        turn_b_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನಾನು ಇತರ ರೈತನ ಸಂಭಾಷಣೆಗೆ ಪ್ರವೇಶಿಸುತ್ತಿದ್ದೇನೆ"},
            headers=headers_b,
        )
        assert turn_b_resp.status_code == 403

        # 4. Header Spoofing Defense:
        # Farmer B passes token_b but attempts to spoof Farmer A via X-Farmer-ID header
        spoof_headers = {
            "Authorization": f"Bearer {token_b}",
            "X-Farmer-ID": str(FARMER_A_ID),
        }
        spoof_resp = await client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=spoof_headers,
        )
        # Invariant: Identity is derived strictly from validated token (Farmer B), NOT X-Farmer-ID!
        assert spoof_resp.status_code == 403

        # 5. Farmer B attempts to evaluate or list recommendations on Farmer A's conversation -> 403 Forbidden
        rec_eval_b = await client.post(
            f"/api/v1/conversations/{conv_id}/recommendations",
            headers=headers_b,
        )
        assert rec_eval_b.status_code == 403

        rec_list_b = await client.get(
            f"/api/v1/conversations/{conv_id}/recommendations",
            headers=headers_b,
        )
        assert rec_list_b.status_code == 403


@pytest.mark.asyncio
async def test_audio_retrieval_owner_binding_bola(
    db_session: AsyncSession,
    two_seeded_farmers: tuple[Farmer, Farmer],
    tmp_path,
):
    audio_store = EphemeralAudioStore(storage_dir=tmp_path / "tts_responses")
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    token_a = create_access_token(FARMER_A_ID)
    token_b = create_access_token(FARMER_B_ID)

    # Save audio owned by Farmer A
    audio_id = await audio_store.save(b"RIFF....test audio bytes", owner_id=str(FARMER_A_ID))

    from app.core.tts.storage import get_ephemeral_audio_store
    app.dependency_overrides[get_ephemeral_audio_store] = lambda: audio_store

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Farmer A retrieves own audio -> 200 OK
        resp_a = await client.get(
            f"/api/v1/voice/audio/{audio_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert resp_a.status_code == 200
        assert resp_a.content == b"RIFF....test audio bytes"

        # 2. Farmer B attempts to retrieve Farmer A's audio -> 404 (safe disclosure policy)
        resp_b = await client.get(
            f"/api/v1/voice/audio/{audio_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp_b.status_code == 404
