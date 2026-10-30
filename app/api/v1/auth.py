"""REST API endpoints for Farmer Authentication, Token Management, and Identity.

Conforms to Directive M5.1, M5.2, and 09_API_CONTRACT.md.
"""

from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.auth import get_current_farmer
from app.database import get_db_session
from app.models.farmer import Farmer
from app.schemas.auth import (
    ChangePasswordRequest,
    FarmerResponse,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services.auth_service import AuthService, mask_phone_number

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from Forwarded headers or direct connection."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new farmer account",
)
async def register(
    request: RegisterRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    """Create a new farmer account, record consent, and return initial access tokens."""
    client_ip = get_client_ip(req)
    service = AuthService(db)
    return await service.register_farmer(request, client_ip=client_ip)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate farmer credentials",
)
async def login(
    request: LoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate phone and password, returning short-lived access and refresh tokens."""
    client_ip = get_client_ip(req)
    service = AuthService(db)
    return await service.login_farmer(request, client_ip=client_ip)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token",
)
async def refresh_tokens_endpoint(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Rotate refresh token and receive a fresh access token."""
    service = AuthService(db)
    return await service.refresh_tokens(request.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Invalidate active session",
)
async def logout(
    request: Optional[LogoutRequest] = None,
    authorization: Annotated[Optional[str], Header()] = None,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Revoke active refresh tokens and denylist calling access token for the authenticated farmer."""
    service = AuthService(db)
    token_str = request.refresh_token if request else None
    raw_token = None
    if authorization and authorization.lower().startswith("bearer "):
        parts = authorization.split()
        if len(parts) == 2:
            raw_token = parts[1]
    await service.logout_farmer(current_farmer.id, refresh_token_str=token_str, current_access_token=raw_token)
    return {"message": "Successfully logged out"}


@router.get(
    "/me",
    response_model=FarmerResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated farmer profile",
)
async def get_me(
    current_farmer: Farmer = Depends(get_current_farmer),
) -> FarmerResponse:
    """Retrieve identity and account metadata for the authenticated farmer."""
    # Mask phone from encrypted or fallback
    return FarmerResponse(
        id=current_farmer.id,
        phone_number_masked=mask_phone_number(current_farmer.phone_number_hash),
        preferred_language=current_farmer.preferred_language,
        account_status=current_farmer.account_status,
        created_at=current_farmer.created_at,
        last_login_at=current_farmer.last_login_at,
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change account password",
)
async def change_password_endpoint(
    request: ChangePasswordRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Change account password and revoke all active refresh tokens."""
    service = AuthService(db)
    await service.change_password(current_farmer.id, request)
    return {"message": "Password changed successfully. Please log in with your new password."}
