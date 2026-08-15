from typing import List, Optional, Literal

from pydantic import BaseModel, Field, HttpUrl
from google.adk.agents import LlmAgent


class LocationCandidateSchema(BaseModel):
    location_id: str = Field(
        description="Unique identifier for this location candidate"
    )

    place_name: str = Field(
        description="Public name or listing title of the location"
    )

    address: Optional[str] = Field(
        default=None,
        description="Public address or approximate area of the location"
    )

    latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        description="Verified or approximate latitude used by the frontend map"
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
        description="Verified or approximate longitude used by the frontend map"
    )

    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Publicly advertised price; null when unavailable"
    )

    currency: Optional[str] = Field(
        default=None,
        description="Currency code, for example EUR or USD"
    )

    price_unit: Optional[
        Literal["hour", "day", "week", "unknown"]
    ] = Field(
        default=None,
        description="Unit associated with the advertised price"
    )

    availability_status: Literal[
        "publicly_available",
        "publicly_unavailable",
        "requires_confirmation",
        "unknown",
    ] = Field(
        description=(
            "Availability status based only on retrieved public information"
        )
    )

    availability_note: Optional[str] = Field(
        default=None,
        description="Public availability information or confirmation warning"
    )

    image_urls: List[HttpUrl] = Field(
        default_factory=list,
        description="Image URLs retrieved from the public listing"
    )

    amenities: List[str] = Field(
        default_factory=list,
        description=(
            "Useful production features such as parking, electricity, "
            "bathrooms, vehicle access, or soundproofing"
        )
    )

    match_score: int = Field(
        ge=0,
        le=100,
        description="How well this candidate satisfies the scene requirements"
    )

    match_reason: str = Field(
        description="Short explanation of why the location suits the scene"
    )

    source_url: HttpUrl = Field(
        description="Original webpage found through Parallel Search"
    )

    source_excerpt: Optional[str] = Field(
        default=None,
        description="Relevant evidence retrieved from the source webpage"
    )


class SceneLocationRecommendation(BaseModel):
    scene_number: int = Field(
        ge=1,
        description="Scene number assigned by the Director Agent"
    )

    scene_heading: str = Field(
        description="Original scene heading produced by the Director Agent"
    )

    scene_setting: Optional[str] = Field(
        default=None,
        description="Short description of the location required by the scene"
    )

    candidates: List[LocationCandidateSchema] = Field(
        default_factory=list,
        description=(
            "Location candidates for this scene, ordered from the highest "
            "match score to the lowest"
        )
    )


class LocationAgentOutput(BaseModel):
    scene_recommendations: List[SceneLocationRecommendation] = Field(
        default_factory=list,
        description="Location recommendations grouped by scene"
    )


LOCATION_AGENT_INSTRUCTION = """
You are the Location Agent for CinePilot, an AI film pre-production
planning system.

You will receive:

1. Scene requirements extracted by the Director Agent.
2. Filming constraints provided by the user, such as region, budget,
   maximum travel distance, filming dates, and additional requirements.
3. Real public location information retrieved through Parallel Search.

Your task is to evaluate and rank the retrieved location candidates for
each screenplay scene.

Rules:

1. Create one SceneLocationRecommendation for every scene provided to you.

2. Preserve the scene_number and scene_heading exactly as supplied by the
   Director Agent.

3. Evaluate candidates using the scene setting, interior or exterior
   requirement, time of day, weather, props, shooting requirements, user
   budget, preferred region, maximum distance, and other user constraints.

4. Return no more than 5 candidates for each scene.

Only return a candidate when the retrieved evidence demonstrates that it is
reasonably compatible with the fundamental scene setting.

There is no minimum candidate count. Returning zero, one, or two candidates
is better than returning unsuitable locations merely to fill the list.

5. Order each scene's candidates from the highest match_score to the lowest.

6. A candidate may be recommended for multiple scenes when it genuinely
   satisfies the requirements of those scenes.

7. Only use location facts contained in the Parallel Search results.
   Never invent or assume a location, address, price, coordinate, amenity,
   availability statement, image URL, or source URL.

8. If the advertised price is missing, set price to null.

9. If the currency or price unit is missing, set the corresponding field
   to null or "unknown".

10. Do not claim that a location is available on the user's filming dates
    unless the retrieved evidence explicitly confirms it.

11. When exact availability is not confirmed, use
    "requires_confirmation" or "unknown".

12. If an exact public address or coordinate is unavailable, use null or
    an explicitly supplied approximate coordinate. Never manufacture an
    exact coordinate.

13. Every source_url must refer to the original public webpage from which
    the candidate information was retrieved.

14. Keep source_excerpt short and directly relevant to the candidate's
    price, location, amenities, or availability.

15. Assign match_score from 0 to 100 based on how well the candidate
    satisfies both the scene requirements and the user's constraints.

16. Explain the most important reasons for the score in match_reason.

17. If no suitable candidates were retrieved for a scene, return that
    scene with an empty candidates list. Do not create fictional results.

18. Treat every distinct named venue, property, studio, or rentable
    location supported by the retrieved results as a separate candidate.

19. A missing price, coordinate, image, or confirmed availability does
    not automatically disqualify an otherwise credible candidate. Use
    null, an empty list, or "unknown" for information that the source
    does not provide.

20. Do not collapse several distinct locations into one candidate. Each
    candidate must have its own location_id, place_name, evaluation, and
    source_url.

21. Include no more than 5 candidates for one scene.

22. Treat the fundamental venue type as a hard requirement unless the
candidate is explicitly suitable for conversion into that venue type.

Examples:
- A residential house is not automatically suitable for a cafe scene.
- An office is not automatically suitable for a hospital scene.
- An event venue is not automatically suitable for a nightclub scene.

23. Reject a candidate when its documented venue type clearly conflicts
with the scene and the evidence does not demonstrate a suitable matching area.

24. Do not recommend a candidate solely because it is in the correct region
and accepts film productions.

25. A candidate with the wrong fundamental venue type must not receive a
match_score above 40.

26. A candidate missing evidence for most important visual requirements
must not receive a match_score above 60.

27. A candidate known to exceed a required budget must not be recommended.

28. When the evidence is too vague to determine whether a candidate matches
the required venue type, omit it instead of assuming suitability.
Return structured output matching the required schema.
"""


location_agent = LlmAgent(
    name="location_agent",
    model="gemini-3.5-flash-lite",
    instruction=LOCATION_AGENT_INSTRUCTION,
    output_schema=LocationAgentOutput,
    output_key="location_data",
)