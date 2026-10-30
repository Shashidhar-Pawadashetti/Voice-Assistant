"""Targeted tests for ConversationService and dialogue prompts to achieve >= 85% coverage."""

from decimal import Decimal
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.asr.mock import MockSpeechRecognizer
from app.core.dialogue.prompts import generate_dialogue_response
from app.core.dialogue.state_machine import DialogueState
from app.core.exceptions import (
    AudioValidationError,
    AuthorizationError,
    ConversationExpiredError,
    ResourceNotFoundError,
)
from app.core.llm.extractor import SchemeExtractor
from app.core.normalization.land_area import LandUnit, NormalizedLandArea
from app.core.profile.schemas import AgriculturalProfile
from app.core.tts.mock import MockSpeechSynthesizer
from app.core.tts.storage import EphemeralAudioStore
from app.models.farmer import Farmer
from app.schemas.extraction import Intent
from app.services.conversation_service import ConversationService
from tests.integration.test_voice_pipeline import DummyLanguageModel


TEST_FARMER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def setup_farmer(db_session: AsyncSession) -> Farmer:
    farmer = Farmer(
        id=TEST_FARMER_ID,
        phone_number_encrypted="enc_2",
        phone_number_hash="hash_2",
        password_hash="pwd_2",
        preferred_language="kn",
        account_status="ACTIVE",
    )
    db_session.add(farmer)
    await db_session.flush()
    return farmer


@pytest.fixture
def conv_service(db_session: AsyncSession, tmp_path):
    store = EphemeralAudioStore(storage_dir=tmp_path / "tts_cov")
    asr = MockSpeechRecognizer()
    extractor = SchemeExtractor(llm=DummyLanguageModel())
    tts = MockSpeechSynthesizer()

    return ConversationService(
        db=db_session,
        speech_recognizer=asr,
        extractor=extractor,
        speech_synthesizer=tts,
        audio_store=store,
    )


@pytest.mark.asyncio
async def test_conversation_service_edge_cases(
    db_session: AsyncSession,
    setup_farmer: Farmer,
    conv_service: ConversationService,
):
    # 1. Non-existent farmer on create
    with pytest.raises(ResourceNotFoundError):
        await conv_service.create_conversation(farmer_id=uuid.uuid4())

    # 2. Non-existent conversation on get
    with pytest.raises(ResourceNotFoundError):
        await conv_service.get_conversation(uuid.uuid4(), TEST_FARMER_ID)

    # 3. Create valid conversation
    conv = await conv_service.create_conversation(TEST_FARMER_ID, language="kn", initial_intent=Intent.FIND_SCHEMES)
    conv_id = uuid.UUID(conv.conversation_id)

    # 4. Turn with empty transcript falls back to "..."
    t_resp = await conv_service.process_turn(conv_id, TEST_FARMER_ID, input_mode="TEXT", text_input="")
    assert t_resp.turn_number == 1

    # 5. Turn with ambiguous land area triggers CLARIFYING
    t_amb = await conv_service.process_turn(conv_id, TEST_FARMER_ID, input_mode="TEXT", text_input="ನನ್ನ ಬಳಿ 4 ಜಮೀನಿದೆ")
    assert t_amb.dialogue_state == DialogueState.CLARIFYING

    # 6. Turn in CONFIRMING state with rejection
    # First set state to CONFIRMING manually or via ownership turn
    await conv_service.process_turn(conv_id, TEST_FARMER_ID, input_mode="TEXT", text_input="ಸ್ವಂತ ಜಮೀನು")
    # Now in CONFIRMING state, reject it: "ಇಲ್ಲ"
    t_rej = await conv_service.process_turn(conv_id, TEST_FARMER_ID, input_mode="TEXT", text_input="ಇಲ್ಲ")
    assert t_rej.dialogue_state == DialogueState.COLLECTING_SLOTS

    # 7. Turn in CONFIRMING state with unclear response
    await conv_service.process_turn(conv_id, TEST_FARMER_ID, input_mode="TEXT", text_input="ಸ್ವಂತ ಜಮೀನು")
    t_unc = await conv_service.process_turn(conv_id, TEST_FARMER_ID, input_mode="TEXT", text_input="ಗೊತ್ತಿಲ್ಲ")
    assert t_unc.dialogue_state == DialogueState.CLARIFYING

    # 8. Resume on active conversation (idempotent / keeps active)
    res_conv = await conv_service.resume_conversation(conv_id, TEST_FARMER_ID)
    assert res_conv.status == "ACTIVE"

    # 9. Voice turn without audio bytes raises AudioValidationError
    with pytest.raises(AudioValidationError):
        await conv_service.process_turn(conv_id, TEST_FARMER_ID, input_mode="VOICE", audio_bytes=None)

    # 10. Get active conversation
    act = await conv_service.get_active_conversation(TEST_FARMER_ID)
    assert act is not None
    assert act.conversation_id == str(conv_id)

    # 11. Complete conversation and verify double-complete
    comp = await conv_service.complete_conversation(conv_id, TEST_FARMER_ID)
    assert comp.status == "COMPLETED"
    comp2 = await conv_service.complete_conversation(conv_id, TEST_FARMER_ID)
    assert comp2.status == "COMPLETED"

    # 12. Process turn on completed conversation raises ConversationExpiredError
    with pytest.raises(ConversationExpiredError):
        await conv_service.process_turn(conv_id, TEST_FARMER_ID, input_mode="TEXT", text_input="ಹಲೋ")


def test_dialogue_prompts_all_branches():
    prof = AgriculturalProfile()

    # Paused
    p_paused = generate_dialogue_response(DialogueState.PAUSED, Intent.FIND_SCHEMES, prof)
    assert "ತಾತ್ಕಾಲಿಕವಾಗಿ" in p_paused

    # Completed
    p_comp = generate_dialogue_response(DialogueState.COMPLETED, Intent.FIND_SCHEMES, prof)
    assert "ಪೂರ್ಣಗೊಂಡಿದೆ" in p_comp

    # Clarifying without prompt
    p_clar = generate_dialogue_response(DialogueState.CLARIFYING, Intent.FIND_SCHEMES, prof)
    assert "ಸ್ಪಷ್ಟವಾಗಿ" in p_clar

    # Clarifying with prompt
    prof.land_area = NormalizedLandArea(
        original_utterance="4 ಜಮೀನು",
        original_value=Decimal("4"),
        original_unit=LandUnit.ACRE,
        canonical_acres=Decimal("4.0000"),
        canonical_guntas=Decimal("160.00"),
        canonical_hectares=Decimal("1.6187"),
        is_ambiguous=True,
        clarification_prompt="ದಯವಿಟ್ಟು ಎಕರೆ ತಿಳಿಸಿ",
    )
    p_clar2 = generate_dialogue_response(DialogueState.CLARIFYING, Intent.FIND_SCHEMES, prof)
    assert p_clar2 == "ದಯವಿಟ್ಟು ಎಕರೆ ತಿಳಿಸಿ"

    # Greeting
    p_greet = generate_dialogue_response(DialogueState.GREETING, Intent.GREETING, AgriculturalProfile())
    assert "ನಮಸ್ಕಾರ" in p_greet
