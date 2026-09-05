from typing import List, Optional

from pydantic import BaseModel, Field

from backend.app.agents.director_agent import Scene
from backend.app.agents.location_agent import LocationCandidateSchema
from backend.app.schemas.budget import BudgetAgentOutput
from backend.app.schemas.risk import RiskAgentOutput
from backend.app.schemas.scheduler import SchedulerAgentOutput


class ReportGenerateRequest(BaseModel):
    """
    Complete input received by the Report endpoint.

    scenes:
        The full scene list previously produced by the Director Agent.

    selected_locations:
        Location candidates the user has already confirmed, if any.

    schedule:
        The Scheduler Agent's full output, if a schedule has already
        been generated; null otherwise.

    budget:
        The Budget Agent's full output, if a budget has already been
        generated; null otherwise.

    risk:
        The Risk Agent's full output, if a risk assessment has already
        been generated; null otherwise.
    """

    scenes: List[Scene]

    selected_locations: List[LocationCandidateSchema] = Field(
        default_factory=list,
    )

    schedule: Optional[SchedulerAgentOutput] = Field(default=None)

    budget: Optional[BudgetAgentOutput] = Field(default=None)

    risk: Optional[RiskAgentOutput] = Field(default=None)

    user_id: str = Field(
        default="web_user",
        min_length=1,
    )


class ReportAgentOutput(BaseModel):
    executive_summary: str = Field(
        description=(
            "A 2-4 sentence overview of the production, grounded in the "
            "actual inputs supplied"
        ),
    )

    highlights: List[str] = Field(
        default_factory=list,
        description=(
            "3-6 cross-cutting observations connecting evidence across "
            "the supplied sources, each citing specific evidence"
        ),
    )
