from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from backend.app.agents.director_agent import Scene


class SchedulerConstraintsInput(BaseModel):
    """
    Scheduling preferences entered by the user on the Schedule page.
    """

    target_shoot_days: int = Field(
        gt=0,
        description="Desired number of shoot days, treated as a soft goal",
    )

    additional_constraints: str = Field(
        default="",
        max_length=500,
        description=(
            "Free-text actor/crew availability, blackout dates, or "
            "weather notes entered by the user"
        ),
    )


class SchedulerGenerateRequest(BaseModel):
    """
    Complete input received by the Scheduler endpoint.

    scenes:
        The full scene list previously produced by the Director Agent.

    constraints:
        Scheduling preferences entered by the user.
    """

    scenes: List[Scene]

    constraints: SchedulerConstraintsInput

    user_id: str = Field(
        default="web_user",
        min_length=1,
    )


class ScheduleBlock(BaseModel):
    scene_number: int = Field(
        ge=1,
        description="Scene number assigned by the Director Agent",
    )

    scene_heading: str = Field(
        description="Original scene heading produced by the Director Agent",
    )

    shoot_day: int = Field(
        ge=1,
        description="Sequential shoot day this scene is assigned to",
    )

    call_time: str = Field(
        description=(
            "Call time for this scene in 24-hour HH:MM format, "
            "for example 07:00 or 19:00"
        ),
    )

    interior_exterior: Literal[
        "Interior",
        "Exterior",
        "Interior/Exterior",
        "Unspecified",
    ] = Field(
        description="Copied from the Director Agent's scene analysis",
    )

    time_of_day: Optional[str] = Field(
        default=None,
        description="Copied from the Director Agent's scene analysis",
    )

    location_name: Optional[str] = Field(
        default=None,
        description=(
            "The scene's location_setting from the Director Agent; "
            "null when not established. Never a scouted venue name — "
            "that is the Location Agent's responsibility."
        ),
    )

    cast_needed: List[str] = Field(
        default_factory=list,
        description="Characters required for this scene",
    )

    has_conflict: bool = Field(
        default=False,
        description="Whether this scene has a flagged scheduling conflict",
    )

    conflict_reason: Optional[str] = Field(
        default=None,
        description="Explanation of the flagged conflict; null when none",
    )


class SchedulingConstraint(BaseModel):
    kind: Literal["actor", "crew", "weather"] = Field(
        description="Category of the scheduling constraint",
    )

    description: str = Field(
        description="Concise, evidence-based explanation of the constraint",
    )

    severity: Literal["low", "medium", "high"] = Field(
        description="Impact of the constraint on the schedule",
    )

    affected_scene_numbers: List[int] = Field(
        default_factory=list,
        description="Scene numbers this constraint affects",
    )


class SchedulerAgentOutput(BaseModel):
    schedule: List[ScheduleBlock] = Field(
        default_factory=list,
        description="One entry per supplied scene, in scheduled order",
    )

    constraints: List[SchedulingConstraint] = Field(
        default_factory=list,
        description="Scheduling constraints and flagged conflicts",
    )

    total_shoot_days: int = Field(
        ge=0,
        description="Highest shoot_day used across the schedule",
    )

    night_block_count: int = Field(
        ge=0,
        description="Number of distinct shoot days containing a night scene",
    )
