"""
app/services/pipeline_service.py
=================================
PipelineService – orchestrates a full LangGraph pipeline run for a project.

Responsibility
--------------
1. Reads the project and its stored ``script_draft``.
2. Creates an ``AgentSession`` row (status=``running``) for audit / polling.
3. Calls ``WorkflowRunner.run()`` to execute the 5-node graph.
4. Persists the resulting ``production_plan`` back to the ``AgentSession``
   (status=``completed`` or ``failed``).
5. Returns a structured response the router can serialise directly.

The service does **not** write ``Budget``, ``Schedule``, or ``RiskReport`` rows
from the plan — those are created by the agent nodes themselves inside the graph.
This keeps a clean separation: the service owns the session lifecycle; the graph
nodes own domain data writes.

All DB writes use ``session.flush()`` — ``get_db()`` owns the commit.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph import workflow_runner
from app.models.agent_session import AgentSession
from app.services.agent_session_service import AgentSessionService
from app.services.project_service import ProjectService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PipelineService:
    """Manages end-to-end execution of the production planning pipeline."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._project_svc = ProjectService(db)
        self._session_svc = AgentSessionService(db)

    async def run(
        self,
        project_id: uuid.UUID,
        input_overrides: dict | None = None,
    ) -> AgentSession:
        """
        Execute the full multi-agent pipeline for the given project.

        Steps
        -----
        1. Fetch the project and guard against missing ``script_draft``.
        2. Create an ``AgentSession`` row with status ``running``.
        3. Invoke ``WorkflowRunner.run()`` (async, may take 20–60 s).
        4. Persist the returned ``production_plan`` into ``state_snapshot``.
        5. Mark the session ``completed`` (or ``failed`` on exception).
        6. Return the session ORM instance.

        Parameters
        ----------
        project_id:
            UUID of the project to run the pipeline for.
        input_overrides:
            Optional per-run configuration forwarded to the Director node.

        Returns
        -------
        AgentSession
            The refreshed session row; its ``state_snapshot`` contains the
            full ``production_plan`` dict.

        Raises
        ------
        HTTPException 404
            When the project does not exist.
        HTTPException 422
            When ``script_draft`` is empty — the pipeline cannot run without
            a screenplay.
        """
        # 1. Load project and validate screenplay is present
        project = await self._project_svc.get_or_404(project_id)

        if not project.script_draft or not project.script_draft.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Project has no screenplay. "
                    "Upload a script first via POST /script/upload-script."
                ),
            )

        # 2. Create the session tracking row
        agent_session = await self._session_svc.create(
            project_id=project_id,
            agent_type="production_planning",
        )

        logger.info(
            "PipelineService: starting run",
            extra={
                "project_id": str(project_id),
                "session_id": str(agent_session.id),
            },
        )

        # 3. Execute the graph
        try:
            production_plan = await workflow_runner.run(
                project_id=str(project_id),
                screenplay=project.script_draft,
                input_data=input_overrides or {},
            )
        except Exception as exc:
            # 4a. Persist failure state
            logger.error(
                "PipelineService: run failed",
                extra={
                    "project_id": str(project_id),
                    "session_id": str(agent_session.id),
                    "error": str(exc),
                },
            )
            agent_session.status = "failed"
            agent_session.error_message = str(exc)
            agent_session.completed_at = datetime.now(timezone.utc)
            agent_session.state_snapshot = {"status": "failed", "error": str(exc)}
            agent_session.messages = []
            await self.db.flush()
            await self.db.refresh(agent_session)
            return agent_session

        # 4b. Persist the successful plan
        plan_status = production_plan.get("status", "failed")
        session_status = "completed" if plan_status in ("complete", "partial") else "failed"

        agent_session.status = session_status
        agent_session.state_snapshot = production_plan
        agent_session.messages = production_plan.get("messages", [])
        agent_session.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(agent_session)

        logger.info(
            "PipelineService: run complete",
            extra={
                "project_id": str(project_id),
                "session_id": str(agent_session.id),
                "plan_status": plan_status,
            },
        )

        return agent_session
