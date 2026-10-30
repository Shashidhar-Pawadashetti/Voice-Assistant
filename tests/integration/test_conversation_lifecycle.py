"""Integration tests for Conversation Lifecycle Management (M3.1)."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.conversations import DEV_FARMER_ID, get_conversation_service
from app.core.asr.mock import MockSpeechRecognizer
from app.core.dialogue.state_machine import DialogueState
from app.core.llm.extractor import SchemeExtractor
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore
from app.main import create_app
from app.models.farmer import Farmer
from app.services.conversation_service import ConversationService
from tests.integration.test_voice_pipeline import DummyLanguageModel


@pytest.fixture
async def seeded_farmer(db_session: AsyncSession) -> Farmer:
    """Create and seed the default test farmer."""
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
    """Instantiate ConversationService with deterministic test doubles."""
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
async def test_conversation_lifecycle_flow(db_session: AsyncSession, seeded_farmer: Farmer, mock_conversation_service):
    app = create_app()
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Conversation
        create_resp = await client.post(
            "/api/v1/conversations",
            json={"language": "kn", "initial_intent": "INCOME_SUPPORT"},
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert create_resp.status_code == 201
        data = create_resp.json()
        conv_id = data["conversation_id"]
        assert data["farmer_id"] == str(DEV_FARMER_ID)
        assert data["state"] == DialogueState.GREETING.value
        assert data["status"] == "ACTIVE"

        # 2. Get Active Conversation
        active_resp = await client.get(
            "/api/v1/conversations/active",
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert active_resp.status_code == 200
        assert active_resp.json()["conversation_id"] == conv_id

        # 3. Retrieve Conversation by ID
        get_resp = await client.get(
            f"/api/v1/conversations/{conv_id}",
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["conversation_id"] == conv_id

        # 4. List Farmer Conversations
        list_resp = await client.get(
            "/api/v1/conversations",
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total"] >= 1
        assert any(c["conversation_id"] == conv_id for c in list_data["conversations"])

        # 5. Complete Conversation
        comp_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/complete",
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert comp_resp.status_code == 200
        assert comp_resp.json()["status"] == "COMPLETED"
        assert comp_resp.json()["state"] == DialogueState.COMPLETED.value

        # 6. Cannot resume or submit turns to a completed conversation
        resume_fail = await client.post(
            f"/api/v1/conversations/{conv_id}/resume",
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert resume_fail.status_code == 410
