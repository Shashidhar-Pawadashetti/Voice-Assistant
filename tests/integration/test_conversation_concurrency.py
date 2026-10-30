"""Integration tests for Conversation Optimistic Concurrency Control (M3.5)."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.conversations import DEV_FARMER_ID, get_conversation_service
from app.core.asr.mock import MockSpeechRecognizer
from app.core.llm.extractor import SchemeExtractor
from app.core.security.jwt import create_access_token
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore
from app.database import get_db_session
from app.main import create_app
from app.models.conversation import Conversation
from app.models.farmer import Farmer
from app.services.conversation_service import ConversationService
from tests.integration.test_voice_pipeline import DummyLanguageModel


@pytest.fixture
async def seeded_farmer(db_session: AsyncSession) -> Farmer:
    farmer = Farmer(
        id=DEV_FARMER_ID,
        phone_number_encrypted="enc_phone_dev",
        phone_number_hash="hash_dev_farmer",
        password_hash="fakehash",
        preferred_language="kn",
        account_status="ACTIVE",
    )
    db_session.add(farmer)
    await db_session.flush()
    return farmer


@pytest.fixture
def mock_conversation_service(db_session: AsyncSession, tmp_path):
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
async def test_optimistic_concurrency_conflict(
    db_session: AsyncSession,
    seeded_farmer: Farmer,
    mock_conversation_service: ConversationService,
):
    app = create_app()
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    app.dependency_overrides[get_db_session] = lambda: db_session

    token = create_access_token(DEV_FARMER_ID)
    auth_headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create conversation
        create_resp = await client.post(
            "/api/v1/conversations",
            json={"language": "kn"},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        conv_id = create_resp.json()["conversation_id"]

        # Simulate concurrent external update incrementing version
        stmt = (
            update(Conversation)
            .where(Conversation.id == uuid.UUID(conv_id))
            .values(version=99)
        )
        await db_session.execute(stmt)
        await db_session.flush()

        # Attempt to submit turn: Client specifies expected_version 1, but DB is at 99 -> Triggers 409 CONCURRENCY_CONFLICT
        resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನಾನು ಧಾರವಾಡದ ರೈತ", "expected_version": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 409
        body = resp.json()
        assert body["error"]["code"] == "CONCURRENCY_CONFLICT"
