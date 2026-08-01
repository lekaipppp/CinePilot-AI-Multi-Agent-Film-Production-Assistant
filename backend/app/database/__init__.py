"""
app/database/__init__.py
========================
Public surface of the database layer.

Import from here rather than from the sub-modules directly so internal
refactors (e.g. moving code between session.py and database.py) don't
ripple through the rest of the codebase.
"""

from app.database.session import (
    AsyncSessionFactory,
    engine,
    get_connection,
    get_db,
    get_db_context,
)
from app.database.database import db_manager
from app.database.repository import BaseRepository

__all__ = [
    "engine",
    "AsyncSessionFactory",
    "get_db",
    "get_db_context",
    "get_connection",
    "db_manager",
    "BaseRepository",
]
