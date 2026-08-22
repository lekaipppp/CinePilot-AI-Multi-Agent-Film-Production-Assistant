"""
app/schemas/auth.py
===================
Pydantic schemas for authentication endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """Payload for POST /auth/register."""

    full_name: str = Field(
        min_length=1,
        max_length=255,
        description="User's display name.",
        examples=["Alex Kessler"],
    )
    email: EmailStr = Field(
        description="Email address — used for login.",
        examples=["alex@cinepilot.ai"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Plain-text password (hashed server-side before storage).",
    )


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr = Field(
        description="Registered email address.",
        examples=["alex@cinepilot.ai"],
    )
    password: str = Field(
        description="Plain-text password.",
    )


# ---------------------------------------------------------------------------
# Response bodies
# ---------------------------------------------------------------------------

class UserRead(BaseModel):
    """Safe public representation of an authenticated user."""

    id: str
    email: str
    full_name: str | None
    avatar_url: str | None
    is_verified: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Returned after successful login or registration."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead


class MeResponse(BaseModel):
    """Returned by GET /auth/me."""

    user: UserRead
