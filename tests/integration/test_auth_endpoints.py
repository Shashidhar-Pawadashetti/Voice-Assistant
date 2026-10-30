"""Integration tests for Farmer Authentication, Tokens, Rotation, Lockout, and Rate Limiting (M5.1)."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.main import create_app
from app.models.farmer import Farmer


@pytest.mark.asyncio
async def test_farmer_registration_and_duplicate_prevention(db_session: AsyncSession):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Successful Registration
        reg_payload = {
            "phone_number": "9876543210",
            "password": "StrongPassword!2026",
            "preferred_language": "kn",
            "consent_given": True,
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert "farmer" in data
        assert "tokens" in data
        assert data["farmer"]["preferred_language"] == "kn"
        assert "9876543210" not in data["farmer"]["phone_number_masked"]  # Masked!
        assert data["tokens"]["access_token"]
        assert data["tokens"]["refresh_token"]

        # 2. Duplicate Registration with formatting variation (+91)
        res_dup = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "+91 98765 43210",
                "password": "AnotherPassword!2026",
                "consent_given": True,
            },
        )
        assert res_dup.status_code == 409
        assert res_dup.json()["error"]["code"] == "ACCOUNT_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_login_flow_and_generic_error_enumeration_prevention(db_session: AsyncSession):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register an account
        await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "9123456780",
                "password": "ValidPassword!2026",
                "consent_given": True,
            },
        )

        # 1. Login with Valid Credentials
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "9123456780", "password": "ValidPassword!2026"},
        )
        assert login_res.status_code == 200
        tokens = login_res.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        # 2. Login with Invalid Password -> Generic 401
        bad_pwd_res = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "9123456780", "password": "WrongPassword!"},
        )
        assert bad_pwd_res.status_code == 401
        assert bad_pwd_res.json()["error"]["code"] == "UNAUTHORIZED"
        bad_pwd_msg = bad_pwd_res.json()["error"]["message"]

        # 3. Login with Non-Existent Account -> Generic 401 with IDENTICAL message
        bad_user_res = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "9999999999", "password": "AnyPassword!"},
        )
        assert bad_user_res.status_code == 401
        assert bad_user_res.json()["error"]["code"] == "UNAUTHORIZED"
        assert bad_user_res.json()["error"]["message"] == bad_pwd_msg  # Invariant: No user enumeration!


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_family_reuse_revocation(db_session: AsyncSession):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register and obtain initial tokens
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "9811122233",
                "password": "RotationPassword!2026",
                "consent_given": True,
            },
        )
        refresh_token_1 = reg_res.json()["tokens"]["refresh_token"]

        # 1. Legitimate Refresh -> Token Rotation
        ref_res_1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_1},
        )
        assert ref_res_1.status_code == 200
        new_tokens = ref_res_1.json()
        refresh_token_2 = new_tokens["refresh_token"]
        assert refresh_token_2 != refresh_token_1  # Rotated!

        # 2. Token Family Reuse Detection:
        # An attacker attempts to reuse refresh_token_1 which was already rotated
        reuse_res = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_1},
        )
        assert reuse_res.status_code == 401
        assert "reuse detected" in reuse_res.json()["error"]["message"].lower()

        # 3. Invariant: The entire token family is now revoked, so even refresh_token_2 fails!
        ref_res_2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_2},
        )
        assert ref_res_2.status_code == 401


@pytest.mark.asyncio
async def test_logout_and_password_change(db_session: AsyncSession):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "9777888999",
                "password": "OriginalPassword!2026",
                "consent_given": True,
            },
        )
        access_token = reg_res.json()["tokens"]["access_token"]
        refresh_token = reg_res.json()["tokens"]["refresh_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 1. /auth/me returns current farmer
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["account_status"] == "ACTIVE"

        # 2. Change password
        change_res = await client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "OriginalPassword!2026",
                "new_password": "NewChangedPassword!2026",
            },
            headers=headers,
        )
        assert change_res.status_code == 200

        # Invariant: Refresh token was revoked upon password change
        ref_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert ref_res.status_code == 401

        # Login with new password succeeds
        new_login = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "9777888999", "password": "NewChangedPassword!2026"},
        )
        assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_account_lockout_after_multiple_failed_logins(db_session: AsyncSession):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        phone = "9666555444"
        await client.post(
            "/api/v1/auth/register",
            json={"phone_number": phone, "password": "CorrectPassword!2026", "consent_given": True},
        )

        # 5 failed attempts
        for _ in range(5):
            await client.post(
                "/api/v1/auth/login",
                json={"phone_number": phone, "password": "WrongPassword!"},
            )

        # 6th attempt even with correct password is locked
        locked_res = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": phone, "password": "CorrectPassword!2026"},
        )
        assert locked_res.status_code == 401
        assert "locked" in locked_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_concurrent_refresh_token_rotation_safety(db_session: AsyncSession):
    """Verify that parallel concurrent refresh calls with the same token do not trigger false family revocation."""
    import asyncio

    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "9555444333",
                "password": "ConcurrentPass!2026",
                "consent_given": True,
            },
        )
        refresh_token = reg_res.json()["tokens"]["refresh_token"]

        # Fire two concurrent refresh requests with the exact same initial refresh token
        req1 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        req2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        res1, res2 = await asyncio.gather(req1, req2)

        # Both must succeed! (One performs rotation, second receives coordinated result without family revocation)
        assert res1.status_code == 200
        assert res2.status_code == 200
        tokens1 = res1.json()
        tokens2 = res2.json()
        assert "access_token" in tokens1
        assert "access_token" in tokens2


@pytest.mark.asyncio
async def test_immediate_access_token_revocation_on_logout(db_session: AsyncSession):
    """Verify that an access token is immediately revoked upon logout (JTI denylist)."""
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "9444333222",
                "password": "RevokeTestPass!2026",
                "consent_given": True,
            },
        )
        access_token = reg_res.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Active token works
        me_res1 = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res1.status_code == 200

        # Logout with access token
        logout_res = await client.post("/api/v1/auth/logout", headers=headers)
        assert logout_res.status_code == 200

        # Now access token must be immediately rejected (401 revoked)
        me_res2 = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res2.status_code == 401
        assert "revoked" in me_res2.json()["error"]["message"].lower()
