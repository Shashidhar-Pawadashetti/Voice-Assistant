"""Integration tests for Farmer Ownership Boundaries and BOLA Protection (M3.1)."""

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
async def seeded_farmers(db_session: AsyncSession) -> tuple[Farmer, Farmer]:
    farmer_a = Farmer(
        id=FARMER_A_ID,
        phone_number_encrypted="enc_a",
        phone_number_hash="hash_a",
        password_hash="pwd_a",
        preferred_language="kn",
        account_status="ACTIVE",
    )
    farmer_b = Farmer(
        id=FARMER_B_ID,
        phone_number_encrypted="enc_b",
        phone_number_hash="hash_b",
        password_hash="pwd_b",
        preferred_language="kn",
        account_status="ACTIVE",
    )
    db_session.add_all([farmer_a, farmer_b])
    await db_session.flush()
    return farmer_a, farmer_b


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
async def test_farmer_ownership_isolation(
    db_session: AsyncSession,
    seeded_farmers: tuple[Farmer, Farmer],
    mock_conversation_service: ConversationService,
):
    app = create_app()
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    app.dependency_overrides[get_db_session] = lambda: db_session

    headers_a = {"Authorization": f"Bearer {create_access_token(FARMER_A_ID)}"}
    headers_b = {"Authorization": f"Bearer {create_access_token(FARMER_B_ID)}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Farmer A creates a conversation
        create_resp = await client.post(
            "/api/v1/conversations",
            json={"language": "kn"},
            headers=headers_a,
        )
        assert create_resp.status_code == 201
        conv_id = create_resp.json()["conversation_id"]

        # Farmer B attempts to retrieve Farmer A's conversation -> 403 FORBIDDEN
        get_b_resp = await client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=headers_b,
        )
        assert get_b_resp.status_code == 403
        assert get_b_resp.json()["error"]["code"] == "FORBIDDEN"

        # Farmer B attempts to submit a turn to Farmer A's conversation -> 403 FORBIDDEN
        turn_b_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನಾನು ಇತರ ರೈತನ ಸಂಭಾಷಣೆಗೆ ಪ್ರವೇಶಿಸುತ್ತಿದ್ದೇನೆ"},
            headers=headers_b,
        )
        assert turn_b_resp.status_code == 403
        assert turn_b_resp.json()["error"]["code"] == "FORBIDDEN"

        # Farmer B attempts to complete Farmer A's conversation -> 403 FORBIDDEN
        comp_b_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/complete",
            headers=headers_b,
        )
        assert comp_b_resp.status_code == 403
        assert comp_b_resp.json()["error"]["code"] == "FORBIDDEN"
