"""Integration tests for Government Scheme Catalog and Recommendation Endpoints.

Conforms to Directive M4.1 - M4.7, 07_SCHEME_ENGINE_AND_GOVERNANCE.md, and 09_API_CONTRACT.md.
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.conversations import get_conversation_service
from app.core.asr.mock import MockSpeechRecognizer
from app.core.llm.extractor import SchemeExtractor
from app.core.scheme.enums import RecommendationStatus, SchemeClassification
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore
from app.database import get_db_session
from app.main import create_app
from app.models.farmer import Farmer
from app.services.conversation_service import ConversationService
from tests.integration.test_voice_pipeline import DummyLanguageModel


DEV_FARMER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_FARMER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def seeded_farmer(db_session: AsyncSession) -> Farmer:
    """Create and seed default test farmer."""
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
async def test_list_schemes_endpoint():
    """Verify listing schemes returns official and synthetic demonstration schemes with correct metadata."""
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/schemes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 5

        scheme_ids = [s["scheme_id"] for s in data]
        assert "PM_KISAN" in scheme_ids
        assert "PMFBY" in scheme_ids
        assert "DEMO_MICRO_IRRIGATION" in scheme_ids

        # Verify classifications
        pm_kisan = next(s for s in data if s["scheme_id"] == "PM_KISAN")
        assert pm_kisan["classification"] == SchemeClassification.REAL_GOVERNMENT.value
        assert pm_kisan["demo_only"] is False

        demo_irr = next(s for s in data if s["scheme_id"] == "DEMO_MICRO_IRRIGATION")
        assert demo_irr["classification"] == SchemeClassification.SYNTHETIC_DEMO.value
        assert demo_irr["demo_only"] is True


@pytest.mark.asyncio
async def test_get_scheme_detail_pm_kisan():
    """Verify detailed PM-KISAN definition contains official citations and exclusions."""
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/schemes/PM_KISAN")
        assert resp.status_code == 200
        data = resp.json()

        assert data["scheme_id"] == "PM_KISAN"
        assert "ಪಿಎಂ-ಕಿಸಾನ್" in data["display_name_kn"]
        assert len(data["evidence_references"]) >= 1
        assert "https://pmkisan.gov.in/" in data["application_portal"]
        assert data["official_verification_required"] is True

        # Check exclusions list contains income tax and government employee
        excl_keys = [e["slot_key"] for e in data["exclusions"]]
        assert "income_tax_payer" in excl_keys
        assert "govt_employee" in excl_keys


@pytest.mark.asyncio
async def test_get_scheme_detail_not_found():
    """Verify 404 for non-existent scheme ID."""
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/schemes/NON_EXISTENT_SCHEME")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_evaluate_conversation_recommendations_flow(
    db_session: AsyncSession,
    seeded_farmer: Farmer,
    mock_conversation_service: ConversationService,
):
    """Full end-to-end evaluation: create conversation, collect facts, evaluate schemes, verify traces."""
    app = create_app()
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    app.dependency_overrides[get_db_session] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create conversation
        create_resp = await client.post(
            "/api/v1/conversations",
            json={"language": "kn", "initial_intent": "INCOME_SUPPORT"},
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert create_resp.status_code == 201
        conv_id = create_resp.json()["conversation_id"]

        # 2. Add turn with location, land area and ownership
        turn1_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/turns/text",
            json={"text": "ನನ್ನ ಹೆಸರು ರಮೇಶ್, ಧಾರವಾಡ ಜಿಲ್ಲೆ, 3 ಎಕರೆ ಸ್ವಂತ ಜಮೀನಿದೆ. ಪಿಎಂ ಕಿಸಾನ್ ನೆರವು ಬೇಕು."},
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert turn1_resp.status_code == 200

        # 3. Trigger Scheme Recommendation Evaluation Endpoint
        rec_resp = await client.post(
            f"/api/v1/conversations/{conv_id}/recommendations",
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert rec_resp.status_code == 200
        rec_data = rec_resp.json()

        assert rec_data["conversation_id"] == conv_id
        assert rec_data["total_evaluated"] >= 1
        recs = rec_data["recommendations"]

        pm_kisan_rec = next((r for r in recs if r["scheme_id"] == "PM_KISAN"), None)
        assert pm_kisan_rec is not None
        # User stated ownership requires official verification
        assert pm_kisan_rec["recommendation_status"] in (
            RecommendationStatus.VERIFICATION_REQUIRED.value,
            RecommendationStatus.POTENTIALLY_MATCHED.value,
        )
        assert pm_kisan_rec["official_verification_required"] is True

        # 4. Verify Recommendation Trace in History
        hist_resp = await client.get(
            f"/api/v1/conversations/{conv_id}/recommendations",
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert len(hist_data) >= 1

        first_run = hist_data[0]
        assert first_run["conversation_id"] == conv_id
        assert first_run["farmer_id"] == str(DEV_FARMER_ID)
        assert "explanation_trace" in first_run


@pytest.mark.asyncio
async def test_recommendation_ownership_bola_protection(
    db_session: AsyncSession,
    seeded_farmer: Farmer,
    mock_conversation_service: ConversationService,
):
    """Verify BOLA protection: unauthorized farmer cannot evaluate or view another farmer's recommendations."""
    app = create_app()
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    app.dependency_overrides[get_db_session] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create conversation for DEV_FARMER_ID
        create_resp = await client.post(
            "/api/v1/conversations",
            json={"language": "kn", "initial_intent": "INCOME_SUPPORT"},
            headers={"X-Farmer-ID": str(DEV_FARMER_ID)},
        )
        conv_id = create_resp.json()["conversation_id"]

        # Attempt to evaluate recommendations using OTHER_FARMER_ID
        unauth_eval = await client.post(
            f"/api/v1/conversations/{conv_id}/recommendations",
            headers={"X-Farmer-ID": str(OTHER_FARMER_ID)},
        )
        assert unauth_eval.status_code in (403, 404)

        # Attempt to read recommendation history using OTHER_FARMER_ID
        unauth_hist = await client.get(
            f"/api/v1/conversations/{conv_id}/recommendations",
            headers={"X-Farmer-ID": str(OTHER_FARMER_ID)},
        )
        assert unauth_hist.status_code in (403, 404)
