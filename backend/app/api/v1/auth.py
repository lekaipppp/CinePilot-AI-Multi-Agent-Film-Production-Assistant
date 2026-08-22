"""
app/api/v1/auth.py
==================
Authentication endpoints:
  POST /auth/register  — create account + receive JWT
  POST /auth/login     — email/password login + receive JWT
  GET  /auth/me        — validate token, return current user
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse, UserRead
from app.services.auth_service import AuthService, decode_access_token

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Dependency: resolve current user from Bearer token
# ---------------------------------------------------------------------------

async def get_current_user_dep(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(credentials.credentials)
    service = AuthService(db)
    user = await service.get_current_user(user_id)
    return UserRead(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_verified=user.is_verified,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new CinePilot account",
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Register a new user.  Returns a JWT access token on success.

    Requires: ``passlib[bcrypt]`` and ``python-jose[cryptography]`` to be installed.
    Requires: a configured ``DATABASE_URL`` in the environment.
    """
    service = AuthService(db)
    return await service.register(body)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in with email and password",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email and password. Returns a JWT access token."""
    service = AuthService(db)
    return await service.login(body)


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Return the currently authenticated user",
)
async def me(
    current_user: UserRead = Depends(get_current_user_dep),
) -> MeResponse:
    """Validate the current Bearer token and return the user profile."""
    return MeResponse(user=current_user)
