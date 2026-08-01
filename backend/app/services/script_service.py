"""
app/services/script_service.py
==============================
ScriptService – stores and retrieves screenplay text on the Project row.

Responsibility
--------------
The screenplay is persisted directly on ``Project.script_draft`` (a ``Text``
column).  There is no separate ``scripts`` table.  This service is the only
place in the codebase that writes to that column so the logic stays centralised.

All writes use ``session.flush()`` — the outer ``get_db()`` transaction context
owns the commit.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.services.project_service import ProjectService


class ScriptService:
    """Handles reading and writing the screenplay stored on the Project row."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._project_svc = ProjectService(db)

    async def upload(self, project_id: uuid.UUID, screenplay: str) -> Project:
        """
        Persist ``screenplay`` as the project's ``script_draft``.

        Overwrites any existing draft.  Returns the updated Project row so the
        router can build a response without a second query.

        Parameters
        ----------
        project_id:
            UUID of the project to attach the screenplay to.
        screenplay:
            Full plain-text or Fountain-formatted screenplay.  The caller is
            responsible for basic validation (e.g. minimum length) via the
            Pydantic schema before this method is invoked.

        Returns
        -------
        Project
            The refreshed Project ORM instance with ``script_draft`` populated.

        Raises
        ------
        HTTPException 404
            Propagated from ``ProjectService.get_or_404`` when the project does
            not exist.
        """
        project = await self._project_svc.get_or_404(project_id)
        project.script_draft = screenplay
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get_script(self, project_id: uuid.UUID) -> str | None:
        """
        Return the stored screenplay for a project, or ``None`` if not set.

        Parameters
        ----------
        project_id:
            UUID of the project.

        Returns
        -------
        str | None
            The raw screenplay text, or ``None`` if no draft has been uploaded.

        Raises
        ------
        HTTPException 404
            When the project does not exist.
        """
        project = await self._project_svc.get_or_404(project_id)
        return project.script_draft
