from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.agents.director_agent import Scene


class LocationRequirements(BaseModel):
    """
    Requirements entered by the user on the Location page.
    """

    preferred_region: str = Field(
        min_length=1,
        description=(
            "Preferred city, region, or country in which to search "
            "for filming locations"
        ),
    )

    maximum_day_rate: float = Field(
        gt=0,
        description="Maximum location fee per filming day",
    )

    currency: str = Field(
        default="EUR",
        min_length=3,
        max_length=3,
        description="Three-letter currency code, such as EUR or USD",
    )

    maximum_distance_km: float = Field(
        default=50,
        gt=0,
        le=500,
        description="Maximum search distance from the preferred region",
    )

    environment: Literal[
        "Interior",
        "Exterior",
        "Interior/Exterior",
        "Either",
    ] = Field(
        default="Either",
        description="Required filming environment",
    )

    permit_preference: Literal[
        "any",
        "permit-free-preferred",
        "permit-free-required",
    ] = Field(
        default="any",
        description="User preference concerning filming permits",
    )

    location_type: Literal[
        "either",
        "practical",
        "studio",
    ] = Field(
        default="either",
        description="Whether the user wants a practical location or studio",
    )

    filming_date: date | None = Field(
        default=None,
        description="Preferred filming date, if one has been selected",
    )

    additional_requirements: str = Field(
        default="",
        max_length=500,
        description="Any additional requirements entered by the user",
    )


class LocationSearchRequest(BaseModel):
    """
    Complete input received by the Location endpoint.

    scene:
        A selected scene previously produced by the Director Agent.

    user_requirements:
        Location preferences entered by the user.
    """

    scene: Scene

    user_requirements: LocationRequirements

    user_id: str = Field(
        default="web_user",
        min_length=1,
    )


class LocationRequestConfirmation(BaseModel):
    """
    Temporary response used to confirm that the backend received
    both the Director scene and the user requirements.
    """

    status: Literal["received"]

    scene_number: int

    preferred_region: str

    message: str