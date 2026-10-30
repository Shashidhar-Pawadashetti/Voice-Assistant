"""Integration tests for Multi-Turn Conversation, Correction, and Persistent Memory (M3.4 - M3.7)."""

from decimal import Decimal
import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.conversations import DEV_FARMER_ID, get_conversation_service
from app.core.asr.mock import MockSpeechRecognizer
from app.core.dialogue.state_machine import DialogueState
from app.core.llm.extractor import SchemeExtractor
from app.core.security.jwt import create_access_token
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore
from app.database import get_db_session
from app.main import create_app
from app.models.farmer import Farmer
from app.services.conversation_service import ConversationService
from tests.fixtures.audio_generator import make_test_wav
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
async def test_multi_turn_dialogue_with_corrections_and_confirmation(
    db_session: AsyncSession,
    seeded_farmer: Farmer,
    mock_conversation_service: ConversationService,
):
    app = create_app()
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    app.dependency_overrides[get_db_session] = lambda: db_session
    auth_headers = {"Authorization": f"Bearer {create_access_token(DEV_FARMER_ID)}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create conversation for INCOME_SUPPORT
        create_resp = await client.post(
            "/api/v1/conversations",
            json={"language": "kn", "initial_intent": "INCOME_SUPPORT"},
            headers=auth_headers,
        )
        conv_id = create_resp.json()["conversation_id"]

        # Turn 1: Farmer mentions District
        turn1_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನಾನು ಧಾರವಾಡ ಜಿಲ್ಲೆಯ ರೈತ"},
            headers=auth_headers,
        )
        assert turn1_resp.status_code == 200
        t1 = turn1_resp.json()
        assert t1["turn_number"] == 1
        assert "district" not in t1["missing_slots"]
        assert t1["dialogue_state"] == DialogueState.COLLECTING_SLOTS.value

        # Turn 2: Farmer mentions Crop and initial Land Area (4 acres)
        turn2_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನನ್ನ ಬಳಿ ನಾಲ್ಕು ಎಕರೆ ಜಮೀನಿದೆ, ಜೋಳ ಬೆಳೆಯುತ್ತಿದ್ದೇನೆ"},
            headers=auth_headers,
        )
        assert turn2_resp.status_code == 200
        t2 = turn2_resp.json()
        assert t2["turn_number"] == 2
        assert "land_area" not in t2["missing_slots"]

        # Turn 3: Farmer makes a Spoken Correction: 'ನಾಲ್ಕು ಎಕರೆ ಅಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ'
        turn3_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನಾಲ್ಕು ಎಕರೆ ಅಲ್ಲ, ಮೂರೂವರೆ ಎಕರೆ"},
            headers=auth_headers,
        )
        assert turn3_resp.status_code == 200
        t3 = turn3_resp.json()
        assert t3["turn_number"] == 3

        # Verify profile has updated land area to 3.5 acres
        conv_status = await client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
        )
        prof_data = conv_status.json()["profile"]
        assert prof_data["land_area"]["canonical_acres"] == "3.5000"

        # Turn 4: Farmer provides Land Ownership statement -> Triggers CONFIRMING state
        turn4_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ಇದು ನನ್ನ ಸ್ವಂತ ಜಮೀನು"},
            headers=auth_headers,
        )
        assert turn4_resp.status_code == 200
        t4 = turn4_resp.json()
        assert t4["dialogue_state"] == DialogueState.CONFIRMING.value
        assert "ಸರಿಯೇ" in t4["assistant_text"]

        # Turn 5: Farmer Affirms Confirmation: 'ಹೌದು, ಸರಿಯಾಗಿದೆ' -> Advances to EVALUATION_READY
        turn5_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ಹೌದು, ಸರಿಯಾಗಿದೆ"},
            headers=auth_headers,
        )
        assert turn5_resp.status_code == 200
        t5 = turn5_resp.json()
        assert t5["dialogue_state"] == DialogueState.EVALUATION_READY.value
        assert t5["is_ready_for_evaluation"] is True
        assert len(t5["missing_slots"]) == 0

        # Turn 6: Retrieve Bounded Conversation Turn History
        history_resp = await client.get(
            f"/api/v1/conversations/{conv_id}/turns",
            headers=auth_headers,
        )
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert history["total_turns"] == 5
        assert len(history["turns"]) == 5
        assert history["turns"][0]["turn_number"] == 1


@pytest.mark.asyncio
async def test_voice_turn_submission(
    db_session: AsyncSession,
    seeded_farmer: Farmer,
    mock_conversation_service: ConversationService,
):
    app = create_app()
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    app.dependency_overrides[get_db_session] = lambda: db_session
    auth_headers = {"Authorization": f"Bearer {create_access_token(DEV_FARMER_ID)}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create conversation
        create_resp = await client.post(
            "/api/v1/conversations",
            json={"language": "kn"},
            headers=auth_headers,
        )
        conv_id = create_resp.json()["conversation_id"]

        # Submit audio turn
        wav_bytes = make_test_wav(duration_seconds=1.0)
        files = {"file": ("turn.wav", io.BytesIO(wav_bytes), "audio/wav")}
        data = {"language": "kn"}

        voice_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/voice",
            files=files,
            data=data,
            headers=auth_headers,
        )
        assert voice_resp.status_code == 200
        vdata = voice_resp.json()
        assert vdata["turn_number"] == 1
        assert vdata["conversation_id"] == conv_id
        assert vdata["speech_available"] is True
        assert vdata["audio_url"] is not None
