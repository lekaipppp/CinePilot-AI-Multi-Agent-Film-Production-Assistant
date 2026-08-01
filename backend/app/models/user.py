"""
app/models/user.py
==================
ORM model for the ``users`` table.

A User represents an authenticated account that can own one or more
film production Projects.

Design decisions
----------------
``email``
    Normalised to lowercase in the application layer (service / schema
    validator) before storage.  A unique index enforces uniqueness at the
    database level.  We store the *original-case* display name separately
    in ``full_name`` so nothing is lost.

``hashed_password``
    Stores the Argon2 / bcrypt digest only — never the plaintext secret.
    Nullable so OAuth-only accounts (Google, GitHub) can exist without a
    password.

``is_active`` / ``is_verified``
    Soft-disable accounts without deleting them (audit trail stays intact).
    ``is_verified`` tracks whether the email address has been confirmed.

``is_superuser``
    Grants admin-level access (e.g. list all projects, impersonate users).
    Defaults False; set manually by a superuser or CLI script.

``avatar_url``
    Optional profile picture URL (e.g. from OAuth provider).

``last_login_at``
    Updated on every successful authentication — useful for security audits
    and "inactive account" cleanup jobs.

Indexes
-------
* ``ix_users_email`` (unique) — login lookup.
* ``ix_users_is_active_created_at`` — admin pagination of active users.

Relationships
-------------
``projects``    → one-to-many (User owns Projects; Projects FK → users.id).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    An authenticated user account.

    Lifecycle: active (is_active=True) ↔ deactivated (is_active=False)
    Email verification: unverified (is_verified=False) → verified (True)
    """

    __tablename__ = "users"

    __table_args__ = (
        # Fast, unique email lookup used on every login
        Index("ix_users_email", "email", unique=True),
        # Admin queries: list active users by join date
        Index("ix_users_is_active_created_at", "is_active", "created_at"),
    )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    email: Mapped[str] = mapped_column(
        String(320),    # RFC 5321 max address length
        nullable=False,
        comment="Normalised (lowercase) email address — used for login.",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Display name (free-form, preserves original capitalisation).",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Profile picture URL (set by OAuth provider or user upload).",
    )

    # ------------------------------------------------------------------
    # Credentials
    # ------------------------------------------------------------------
    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment=(
            "Argon2/bcrypt digest of the user's password.  "
            "NULL for OAuth-only accounts."
        ),
    )

    # ------------------------------------------------------------------
    # Access control
    # ------------------------------------------------------------------
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="False = soft-deleted / suspended account.",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True once the email address has been confirmed.",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Grants admin-level access across all resources.",
    )

    # ------------------------------------------------------------------
    # Activity tracking
    # ------------------------------------------------------------------
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the most recent successful login.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Project.created_at.desc()",
        doc="All projects owned by this user.",
    )
