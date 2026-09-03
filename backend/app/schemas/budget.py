from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from backend.app.agents.director_agent import Scene
from backend.app.agents.location_agent import LocationCandidateSchema


class BudgetConstraintsInput(BaseModel):
    """
    Budget preferences entered by the user on the Budget page.
    """

    target_budget: float = Field(
        gt=0,
        description="Desired total production budget, treated as a soft goal",
    )

    currency: str = Field(
        default="EUR",
        min_length=3,
        max_length=3,
        description="Three-letter currency code, such as EUR or USD",
    )

    additional_constraints: str = Field(
        default="",
        max_length=500,
        description=(
            "Free-text known costs, discounts, or restrictions entered "
            "by the user"
        ),
    )


class BudgetGenerateRequest(BaseModel):
    """
    Complete input received by the Budget endpoint.

    scenes:
        The full scene list previously produced by the Director Agent.

    selected_locations:
        Location candidates the user has already confirmed, if any.

    total_shoot_days:
        The Scheduler Agent's total_shoot_days, if a schedule has
        already been generated; null otherwise.

    constraints:
        Budget preferences entered by the user.
    """

    scenes: List[Scene]

    selected_locations: List[LocationCandidateSchema] = Field(
        default_factory=list,
    )

    total_shoot_days: Optional[int] = Field(default=None)

    constraints: BudgetConstraintsInput

    user_id: str = Field(
        default="web_user",
        min_length=1,
    )


class BudgetLineItem(BaseModel):
    key: Literal[
        "locations",
        "equipment",
        "crew",
        "transportation",
        "contingency",
    ] = Field(
        description="Fixed budget category identifier",
    )

    label: str = Field(
        description="Human-readable category label",
    )

    estimated_amount: float = Field(
        ge=0,
        description="Estimated cost for this category",
    )

    note: str = Field(
        description=(
            "Concise explanation of the estimate, clearly distinguishing "
            "confirmed pricing from the agent's own estimate"
        ),
    )


class BudgetAgentOutput(BaseModel):
    line_items: List[BudgetLineItem] = Field(
        default_factory=list,
        description=(
            "Exactly one entry per fixed category: locations, equipment, "
            "crew, transportation, contingency"
        ),
    )

    total_estimated_amount: float = Field(
        ge=0,
        description="Sum of every line item's estimated_amount",
    )

    currency: str = Field(
        description="Three-letter currency code shared by every line item",
    )
