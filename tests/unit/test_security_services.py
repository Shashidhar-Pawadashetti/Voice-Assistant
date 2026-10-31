"""Unit tests for AuthService, PrivacyService, and Security Dependencies edge cases."""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, KrishiMitraError
from app.core.security.auth import (
    _ensure_utc,
    extract_bearer_token,
    get_current_farmer,
    get_current_farmer_id,
)
from app.core.security.jwt import create_access_token
from app.core.security.password import hash_password
from app.core.tts.storage import EphemeralAudioStore
from app.models.conversation import Conversation, ConversationSlot, ConversationTurn
from app.models.farmer import ConsentRecord, Farmer, FarmerProfile
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest
from app.schemas.privacy import DeletionRequestPayload
from app.services.auth_service import AuthService, mask_phone_number
from app.services.privacy_service import PrivacyService


def test_ensure_utc_helper():
    assert _ensure_utc(None) is None
    naive = datetime(2026, 1, 1, 12, 0, 0)
    aware = _ensure_utc(naive)
    assert aware.tzinfo == timezone.utc

    already_aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _ensure_utc(already_aware) == already_aware


def test_mask_phone_number_short():
    assert mask_phone_number("12345") == "******"
    assert mask_phone_number("+919876543210") == "+91 ******3210"


@pytest.mark.asyncio
async def test_auth_service_edge_cases(db_session: AsyncSession):
    service = AuthService(db_session)

    # 1. Registration rate limit exceeded
    rate_key = "reg_ip_192.0.2.1"
    for _ in range(service.settings.AUTH_RATE_LIMIT_REGISTER_MAX_ATTEMPTS):
        await service.rate_limiter.is_rate_limited(
            rate_key,
            max_attempts=service.settings.AUTH_RATE_LIMIT_REGISTER_MAX_ATTEMPTS,
            window_seconds=service.settings.AUTH_RATE_LIMIT_REGISTER_WINDOW_SECONDS,
        )

    with pytest.raises(KrishiMitraError) as exc_info:
        await service.register_farmer(
            RegisterRequest(
                phone_number="9988776655",
                password="SecurePassword!2026",
                consent_given=True,
            ),
            client_ip="192.0.2.1",
        )
    assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"

    # 2. Login rate limit exceeded
    login_rate_key = "login_ip_192.0.2.2"
    for _ in range(service.settings.AUTH_RATE_LIMIT_LOGIN_MAX_ATTEMPTS * 2):
        await service.rate_limiter.is_rate_limited(
            login_rate_key,
            max_attempts=service.settings.AUTH_RATE_LIMIT_LOGIN_MAX_ATTEMPTS * 2,
            window_seconds=service.settings.AUTH_RATE_LIMIT_LOGIN_WINDOW_SECONDS,
        )

    with pytest.raises(KrishiMitraError) as exc_info:
        await service.login_farmer(
            LoginRequest(phone_number="9988776655", password="Any"),
            client_ip="192.0.2.2",
        )
    assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"

    # 3. Create a farmer with expired lockout and verify automatic unlock
    past_lockout = datetime.now(timezone.utc) - timedelta(minutes=5)
    farmer_id = uuid.uuid4()
    locked_farmer = Farmer(
        id=farmer_id,
        phone_number_encrypted="enc",
        phone_number_hash="hash_expired_lockout",
        password_hash=hash_password("UnlockMe!2026"),
        account_status="LOCKED",
        failed_login_attempts=5,
        locked_until=past_lockout,
    )
    db_session.add(locked_farmer)
    await db_session.flush()

    from app.core.security.crypto import compute_phone_hash
    blind_key = service.settings.BLIND_INDEX_KEY or service.settings.APP_SECRET_KEY
    real_hash = compute_phone_hash("9876500001", blind_key)
    locked_farmer.phone_number_hash = real_hash
    await db_session.flush()

    tokens = await service.login_farmer(
        LoginRequest(phone_number="9876500001", password="UnlockMe!2026"),
        client_ip="192.0.2.3",
    )
    assert tokens.access_token
    assert locked_farmer.account_status == "ACTIVE"
    assert locked_farmer.failed_login_attempts == 0

    # 4. Login with DELETED status
    locked_farmer.account_status = "DELETED"
    await db_session.flush()
    with pytest.raises(AuthenticationError) as exc_info:
        await service.login_farmer(
            LoginRequest(phone_number="9876500001", password="UnlockMe!2026"),
            client_ip="192.0.2.4",
        )
    assert "Invalid phone number or password" in str(exc_info.value)
    locked_farmer.account_status = "ACTIVE"
    await db_session.flush()

    # 5. Refresh token non-existent
    with pytest.raises(AuthenticationError) as exc_info:
        await service.refresh_tokens("non_existent_token")
    assert "Invalid or expired" in str(exc_info.value)

    # 6. Change password edge cases
    with pytest.raises(AuthenticationError) as exc_info:
        await service.change_password(
            uuid.uuid4(),
            ChangePasswordRequest(old_password="old", new_password="NewSecurePwd!2026"),
        )
    assert "Farmer account not found" in str(exc_info.value)

    with pytest.raises(AuthenticationError) as exc_info:
        await service.change_password(
            farmer_id,
            ChangePasswordRequest(old_password="WrongOldPassword!", new_password="NewSecurePwd!2026"),
        )
    assert "Current password is incorrect" in str(exc_info.value)

    # 7. Logout with specific refresh token
    await service.logout_farmer(farmer_id, refresh_token_str=tokens.refresh_token)


@pytest.mark.asyncio
async def test_privacy_service_with_turns_and_slots(db_session: AsyncSession, tmp_path):
    audio_store = EphemeralAudioStore(storage_dir=tmp_path / "tts")
    service = PrivacyService(db_session, audio_store=audio_store)

    farmer_id = uuid.uuid4()
    farmer = Farmer(
        id=farmer_id,
        phone_number_encrypted="enc",
        phone_number_hash="hash_p",
        password_hash=hash_password("FarmerPass!2026"),
        preferred_language="kn",
        account_status="ACTIVE",
    )
    profile = FarmerProfile(
        farmer_id=farmer_id,
        profile_data={"district": "HAVERI"},
        profile_version=1,
    )
    consent = ConsentRecord(
        farmer_id=farmer_id,
        purpose="ACCOUNT",
        notice_version="2026.1",
        status="GRANTED",
    )
    db_session.add_all([farmer, profile, consent])

    conv = Conversation(
        id=uuid.uuid4(),
        farmer_id=farmer_id,
        status="ACTIVE",
        state="COLLECTING_SLOTS",
        language="kn",
    )
    db_session.add(conv)
    await db_session.flush()

    turn = ConversationTurn(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        farmer_id=farmer_id,
        turn_number=1,
        role="FARMER",
        input_mode="VOICE",
        transcript_text="ನಮಸ್ಕಾರ",
        assistant_text="ನಮಸ್ಕಾರ, ನಾನು ಕೃಷಿ ಮಿತ್ರ",
    )
    slot = ConversationSlot(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        farmer_id=farmer_id,
        slot_key="district",
        canonical_value="HAVERI",
        canonical_unit=None,
        slot_status="FILLED",
        provenance="USER_STATED",
    )
    db_session.add_all([turn, slot])
    await db_session.flush()

    # 1. Export farmer data with active conversations, turns, and slots
    export_data = await service.export_farmer_data(farmer)
    assert len(export_data.conversations) == 1
    assert len(export_data.conversations[0]["turns"]) == 1
    assert len(export_data.conversations[0]["slots"]) == 1
    assert export_data.conversations[0]["turns"][0]["transcript_text"] == "ನಮಸ್ಕಾರ"

    # 2. Deletion deletes conversations, turns, and slots
    del_res = await service.execute_data_deletion(
        farmer,
        DeletionRequestPayload(password="FarmerPass!2026"),
    )
    assert del_res.status == "COMPLETED"
    assert del_res.records_erased["conversations"] == 1
    assert del_res.records_erased["turns"] == 1
    assert del_res.records_erased["slots"] == 1
    assert farmer.account_status == "DELETED"


@pytest.mark.asyncio
async def test_auth_dependencies(db_session: AsyncSession):
    # 1. Missing Authorization header
    with pytest.raises(AuthenticationError):
        extract_bearer_token(authorization=None)

    # 2. Malformed Authorization scheme (Basic instead of Bearer)
    with pytest.raises(AuthenticationError):
        extract_bearer_token(authorization="Basic dXNlcjpwYXNz")

    with pytest.raises(AuthenticationError):
        extract_bearer_token(authorization="Bearer")

    # 3. Invalid token string
    with pytest.raises(AuthenticationError):
        await get_current_farmer("not.a.valid.jwt", db=db_session)

    # 4. Valid token for non-existent farmer
    missing_id = uuid.uuid4()
    token = create_access_token(missing_id)
    with pytest.raises(AuthenticationError):
        await get_current_farmer(token, db=db_session)

    # 5. Valid token for locked farmer with active lockout
    locked_farmer = Farmer(
        id=uuid.uuid4(),
        phone_number_encrypted="enc",
        phone_number_hash="h1",
        password_hash="pwd",
        account_status="LOCKED",
        locked_until=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db_session.add(locked_farmer)
    await db_session.flush()
    locked_token = create_access_token(locked_farmer.id)
    with pytest.raises(AuthenticationError) as exc_info:
        await get_current_farmer(locked_token, db=db_session)
    assert "locked" in str(exc_info.value).lower()

    # 6. Valid token for locked farmer with expired lockout (auto-unlock)
    locked_farmer.locked_until = datetime.now(timezone.utc) - timedelta(minutes=10)
    await db_session.flush()
    unlocked_farmer = await get_current_farmer(locked_token, db=db_session)
    assert unlocked_farmer.account_status == "ACTIVE"

    # 7. Valid token for deleted farmer
    deleted_farmer = Farmer(
        id=uuid.uuid4(),
        phone_number_encrypted="enc",
        phone_number_hash="h2",
        password_hash="pwd",
        account_status="DELETED",
    )
    db_session.add(deleted_farmer)
    await db_session.flush()
    deleted_token = create_access_token(deleted_farmer.id)
    with pytest.raises(AuthenticationError) as exc_info:
        await get_current_farmer(deleted_token, db=db_session)
    assert "inactive" in str(exc_info.value).lower()

    # 8. get_current_farmer_id convenience wrapper
    retrieved_id = await get_current_farmer_id(unlocked_farmer)
    assert retrieved_id == unlocked_farmer.id
