from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from backend.app.agents.director_agent import Scene
from backend.app.agents.location_agent import LocationCandidateSchema
from backend.app.schemas.budget import BudgetAgentOutput
from backend.app.schemas.scheduler import SchedulerAgentOutput


class RiskGenerateRequest(BaseModel):
    """
    Complete input received by the Risk endpoint.

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
    """

    scenes: List[Scene]

    selected_locations: List[LocationCandidateSchema] = Field(
        default_factory=list,
    )

    schedule: Optional[SchedulerAgentOutput] = Field(default=None)

    budget: Optional[BudgetAgentOutput] = Field(default=None)

    user_id: str = Field(
        default="web_user",
        min_length=1,
    )


class RiskItem(BaseModel):
    id: str = Field(
        default="",
        description=(
            "Always overwritten deterministically by the runner after "
            "generation; the model's own value is ignored."
        ),
    )

    title: str = Field(
        description="Short, specific risk title",
    )

    category: Literal[
        "Weather",
        "Permits",
        "Budget",
        "Scheduling",
        "Safety",
    ] = Field(
        description="Fixed risk category",
    )

    severity: Literal["low", "medium", "high"] = Field(
        description="Impact of this risk if it materializes",
    )

    scope: str = Field(
        description=(
            "Concrete part of the production affected, for example "
            "'Scene 3 · Day 6' or 'Whole production'"
        ),
    )

    likelihood: int = Field(
        ge=0,
        le=100,
        description="Reasoned likelihood estimate, grounded in the cited evidence",
    )

    impact: str = Field(
        description="What happens to the production if this risk occurs",
    )

    recommendation: str = Field(
        description="One concrete, actionable mitigation tied to the evidence cited",
    )


class RiskAgentOutput(BaseModel):
    risks: List[RiskItem] = Field(
        default_factory=list,
        description="Identified production risks, grounded in the supplied data",
    )
