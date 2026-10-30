"""Integration tests for M4.7: M3 Dialogue and Persistent Memory integration with M4 Scheme Recommendations.

Verifies:
1. Multi-turn dialogue progresses to EVALUATION_READY.
2. Grounded native Kannada scheme recommendations are generated automatically in assistant_text.
3. Official verification caveats are spoken and preserved.
4. Immutable recommendation runs are saved in PostgreSQL.
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.conversations import get_conversation_service
from app.core.asr.mock import MockSpeechRecognizer
from app.core.dialogue.state_machine import DialogueState
from app.core.llm.extractor import SchemeExtractor
from app.core.scheme.enums import RecommendationStatus, SchemeClassification
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore
from app.database import get_db_session
from app.main import create_app
from app.models.farmer import Farmer
from app.models.scheme import RecommendationRun
from app.services.conversation_service import ConversationService
from tests.conftest import MockLanguageModel


DEV_FARMER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
async def seeded_farmer(db_session: AsyncSession) -> Farmer:
    """Seed dev farmer in test DB."""
    farmer = Farmer(
        id=DEV_FARMER_ID,
        phone_number_encrypted="enc_dev",
        phone_number_hash="hash_dev",
        password_hash="pwd_dev",
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
    extractor = SchemeExtractor(
        llm=MockLanguageModel(
            default_response={
                "intent": "INCOME_SUPPORT",
                "entities": [],
                "correction_target": None,
                "unresolved_phrases": [],
                "assistant_language": "kn",
            }
        )
    )
    tts = MockSpeechSynthesizer()

    return ConversationService(
        db=db_session,
        speech_recognizer=asr,
        extractor=extractor,
        speech_synthesizer=tts,
        audio_store=audio_store,
    )


@pytest.mark.asyncio
async def test_dialogue_scheme_recommendation_automatic_evaluation(
    db_session: AsyncSession,
    seeded_farmer: Farmer,
    mock_conversation_service: ConversationService,
):
    """When a conversation reaches EVALUATION_READY, M4 evaluates schemes and generates grounded Kannada text."""
    app = create_app()
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    app.dependency_overrides[get_db_session] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Step 1: Create conversation
        create_resp = await client.post(
            "/api/v1/conversations",
            json={"language": "kn", "initial_intent": "INCOME_SUPPORT"},
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert create_resp.status_code == 201
        conv_id = create_resp.json()["conversation_id"]

        # Step 2: Farmer states location, land area and unconfirmed ownership
        # Transitions to CONFIRMING state
        turn1_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನನ್ನ ಊರು ಧಾರವಾಡ ಜಿಲ್ಲೆ. 3 ಎಕರೆ ಸ್ವಂತ ಜಮೀನಿದೆ."},
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert turn1_resp.status_code == 200
        t1 = turn1_resp.json()
        assert t1["dialogue_state"] == DialogueState.CONFIRMING.value
        assert "ಸರಿಯೇ" in t1["assistant_text"]

        # Step 3: Farmer confirms ownership ("ಹೌದು, ಸರಿ")
        # Transitions to EVALUATION_READY state
        turn2_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ಹೌದು, ಸರಿ"},
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert turn2_resp.status_code == 200
        t2 = turn2_resp.json()
        assert t2["dialogue_state"] == DialogueState.EVALUATION_READY.value
        assert t2["is_ready_for_evaluation"] is True

        # Invariant: assistant_text must now contain grounded PM-KISAN recommendation
        assistant_text = t2["assistant_text"]
        assert "ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ" in assistant_text or "ಪಿಎಂ-ಕಿಸಾನ್" in assistant_text
        assert "ಪರಿಶೀಲನೆ" in assistant_text
        # Invariant: Must NOT make false claims of approved government money
        assert "ಮಂಜೂರಾಗಿದೆ" not in assistant_text
        assert "ನಿಮಗೆ ಹಣ ಬಂದಿದೆ" not in assistant_text

        # Verify TTS audio URL is generated
        assert t2["speech_available"] is True
        assert t2["audio_url"] is not None

        # Verify an immutable recommendation run was persisted in the database
        stmt = select(RecommendationRun).where(RecommendationRun.conversation_id == uuid.UUID(conv_id))
        rec_runs = (await db_session.execute(stmt)).scalars().all()
        assert len(rec_runs) >= 1
        assert rec_runs[0].evaluator_version == "v1.0.0"
        assert rec_runs[0].outcome in (
            RecommendationStatus.VERIFICATION_REQUIRED.value,
            RecommendationStatus.POTENTIALLY_MATCHED.value,
        )
