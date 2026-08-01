"""
app/models/__init__.py
======================
Re-exports every ORM model and the shared Base.

Why this file exists
--------------------
SQLAlchemy's ``Base.metadata`` only knows about a table if the model class
has been *imported* at least once (class-body execution registers the mapper).

Importing ``app.models`` anywhere before calling ``Base.metadata.create_all()``
or running ``alembic --autogenerate`` guarantees all tables are visible.

Rule: every new ``app/models/<name>.py`` file MUST be imported here AND
added to ``__all__``.

Import order follows the FK dependency graph (parent before child) so
that ``Base.metadata.sorted_tables`` returns a valid creation sequence:

  User
  └── Project  (owner_id → users.id)
       ├── Scene          (project_id → projects.id)
       ├── Location       (project_id → projects.id)
       │    └── Scene     (location_id → locations.id) ← same Scene class, 2nd FK
       ├── Schedule       (project_id → projects.id)
       │    └── ScheduleDay  (schedule_id → schedules.id,
       │                      location_id → locations.id)
       ├── Budget         (project_id → projects.id)
       │    └── BudgetItem   (budget_id → budgets.id)
       ├── RiskReport     (project_id → projects.id)
       │    └── RiskItem     (report_id → risk_reports.id)
       └── AgentSession   (project_id → projects.id)
"""

# ── Mixins & Base ─────────────────────────────────────────────────────────────
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin  # noqa: F401

# ── Independent (no FKs to app tables) ───────────────────────────────────────
from app.models.user import User  # noqa: F401

# ── Depends on User ───────────────────────────────────────────────────────────
from app.models.project import Project  # noqa: F401

# ── Depends on Project ────────────────────────────────────────────────────────
from app.models.location import Location  # noqa: F401  (must come before Scene)
from app.models.scene import Scene  # noqa: F401        (has FK → locations)
from app.models.schedule import Schedule, ScheduleDay  # noqa: F401
from app.models.budget import Budget, BudgetItem  # noqa: F401
from app.models.risk_report import RiskReport, RiskItem  # noqa: F401
from app.models.agent_session import AgentSession  # noqa: F401

__all__ = [
    # Base infrastructure
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    # Domain models
    "User",
    "Project",
    "Location",
    "Scene",
    "Schedule",
    "ScheduleDay",
    "Budget",
    "BudgetItem",
    "RiskReport",
    "RiskItem",
    "AgentSession",
]
