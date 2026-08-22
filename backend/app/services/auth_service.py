"""
app/services/auth_service.py
============================
Authentication business logic: registration, login, JWT creation and
verification.

Dependencies
------------
``passlib[bcrypt]`` is used for password hashing.  Add it to requirements.txt:
    passlib[bcrypt]>=1.7.4
``python-jose[cryptography]`` is used for JWT signing.  Add it to requirements.txt:
    python-jose[cryptography]>=3.3.0

These are industry-standard libraries and must be installed for auth to work.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserRead

# ---------------------------------------------------------------------------
# Optional: lazy-import crypto libs so the server boots even if they are not
# yet installed — endpoints will return 503 at call time.
# ---------------------------------------------------------------------------

def _get_pwd_context():
    try:
        from passlib.context import CryptContext  # type: ignore
        return CryptContext(schemes=["bcrypt"], deprecated="auto")
    except ImportError:
        return None

def _get_jwt():
    try:
        from jose import jwt, JWTError  # type: ignore
        return jwt, JWTError
    except ImportError:
        return None, None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_crypto():
    """Raise 503 when crypto libs are missing, with a clear install hint."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Authentication libraries are not installed. "
            "Run: pip install 'passlib[bcrypt]' 'python-jose[cryptography]'"
        ),
    )


def _hash_password(plain: str) -> str:
    ctx = _get_pwd_context()
    if ctx is None:
        _require_crypto()
    return ctx.hash(plain)  # type: ignore[union-attr]


def _verify_password(plain: str, hashed: str) -> bool:
    ctx = _get_pwd_context()
    if ctx is None:
        _require_crypto()
    return ctx.verify(plain, hashed)  # type: ignore[union-attr]


def _create_access_token(subject: str) -> str:
    jwt, JWTError = _get_jwt()
    if jwt is None:
        _require_crypto()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")  # type: ignore[union-attr]


def decode_access_token(token: str) -> str:
    """Decode a JWT and return the subject (user id string). Raises HTTPException on failure."""
    jwt, JWTError = _get_jwt()
    if jwt is None:
        _require_crypto()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])  # type: ignore[union-attr]
        sub: str | None = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return sub
    except JWTError:  # type: ignore[misc]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid or expired")


def _user_to_read(user: User) -> UserRead:
    return UserRead(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_verified=user.is_verified,
    )


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class AuthService:
    """Handles user registration, login, and JWT lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, req: RegisterRequest) -> TokenResponse:
        email_lc = req.email.lower().strip()

        # Check uniqueness
        existing = await self.db.scalar(select(User).where(User.email == email_lc))
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        user = User(
            email=email_lc,
            full_name=req.full_name.strip(),
            hashed_password=_hash_password(req.password),
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        token = _create_access_token(str(user.id))
        return TokenResponse(access_token=token, user=_user_to_read(user))

    async def login(self, req: LoginRequest) -> TokenResponse:
        email_lc = req.email.lower().strip()

        user: Optional[User] = await self.db.scalar(
            select(User).where(User.email == email_lc)
        )
        if user is None or user.hashed_password is None or not _verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email address or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated.",
            )

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        token = _create_access_token(str(user.id))
        return TokenResponse(access_token=token, user=_user_to_read(user))

    async def get_current_user(self, user_id: str) -> User:
        user = await self.db.get(User, uuid.UUID(user_id))
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
