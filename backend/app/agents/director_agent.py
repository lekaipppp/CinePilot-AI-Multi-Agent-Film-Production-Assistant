from pydantic import BaseModel, Field 
#pydantic is a data validation library, it acts as a gatekeeper for my code.
#Ensuring any data entered into the system matches the exact structure
#Basemodel is the core building block of Pydanitc,
#=========================================================================
from typing import List, Optional, Literal
#This imports Python type hints
#It tells Python what kind of data a variable should contain.
#Optional means one value may exist, or it may be None.
#=========================================================================
from google.adk.agents import LlmAgent
from dotenv import load_dotenv


'''
1. V2: Add a critique agent to review the extracted data.
2. script
3. Extract text from the PDf and put into the agent.
'''

load_dotenv()

class Scene(BaseModel):
    scene_number: int = Field(
        ge=1,
        #Stands for greater than or equal to 1. It is a pydantic constant from Field.
        description="Sequential scene number assigned according to script order",
    )

    scene_heading: str = Field(
        description="Original scene heading or slug line from the screenplay",
    )

    location_setting: Optional[str] = Field(
        default=None,
        description=(
            "Concise description of the primary location, "
            "for example 'urban alley' or 'hospital operating room'"
        ),
    )

    interior_exterior: Literal[
        "Interior",
        "Exterior",
        "Interior/Exterior",
        "Unspecified",
    ] = Field(
        description="Whether the scene is interior, exterior, mixed, or unspecified",
    )

    time_of_day: Optional[str] = Field(
        default=None,
        description="Explicitly established time of day; null if not established",
    )

    weather_of_scene: Optional[str] = Field(
        default=None,
        description=(
            "Weather explicitly occurring during or visibly/audibly affecting "
            "the scene; null if not established"
        ),
    )

    characters_in_scene: List[str] = Field(
        default_factory=list,
        description="Named characters who physically appear or speak in the scene",
    )

    props_in_scene: List[str] = Field(
        default_factory=list,
        description=(
            "Production-relevant movable objects that are handled, referenced, "
            "featured, or specially prepared. Exclude ordinary architecture "
            "and insignificant background objects."
        ),
    )

    shooting_requirements: List[str] = Field(
        default_factory=list,
        description=(
            "Special production requirements such as weapons, stunts, "
            "night shoots, crowds, animals, minors, VFX, SFX, vehicles, "
            "or unusual equipment"
        ),
    )

    source_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence from the source material supporting the scene details"
    )

    location_features: List[str] = Field(
        default_factory=list,
        description=(
            "Visible architectural and environmental features required "
            "when selecting a filming location, such as floor-to-ceiling "
            "windows, wooden booths, rooftop access, industrial walls, "
            "or a view of a busy street"
        ),
    )


class ScriptRubric(BaseModel):
    scenes: List[Scene] = Field(
        default_factory=list,
        description="All scenes extracted from the screenplay in their original order",
    )


EXTRACTION_INSTRUCTION = """
You are the Director Agent for a film pre-production assistant.

Analyze the screenplay provided by the user and break it down scene by scene.

Rules:

1. Create one Scene entry for every screenplay scene heading or slug line,
   including INT., EXT., INT./EXT., EXT./INT., and equivalent forms.
   Preserve the original order.

2. Assign sequential scene numbers beginning with 1.

3. Preserve each original scene heading in scene_heading.

4. List every named character who physically appears or speaks in the scene.
   Do not treat parenthetical labels such as V.O. or O.S. as part of the
   character's name.

5. Include only production-relevant props. Do not list ordinary architecture,
   fixed set elements, or insignificant background objects unless they have
   clear story or production importance.

6. Flag special shooting requirements such as stunts, weapons, night shoots,
   crowds, animals, minors, vehicles, practical effects, special effects,
   or VFX.

7. If the heading explicitly states NIGHT, include "night shoot" in
   shooting_requirements.

8. Infer time, weather, or production requirements only when there is clear
   textual evidence in that scene. Do not invent details.

9. Example:
   "Heavy rain falls outside" means weather may be recorded as rain.

10. Example:
    "John enters, rain-soaked" describes John's condition but does not confirm
    that it is currently raining. Leave weather null unless the scene provides
    additional evidence.

11. Use null for unknown optional scalar values and empty lists when no
    characters, props, or requirements are identified.

12. Every extracted character, prop, weather condition, and shooting
    requirement must be supported by the screenplay. Include short supporting
    excerpts in source_evidence. Never invent missing information.

13. Extract location-specific visual and architectural requirements into
location_features. Include features that materially affect location scouting,
such as floor-to-ceiling windows, booths, street views, staircases, rooftops,
large open spaces, period architecture, or waterfront access.

Do not include movable props in location_features.
Every feature must be supported by the screenplay.

Return structured output matching the required schema.
"""


director_agent = LlmAgent(
    name="director_agent",
    model="gemini-3.5-flash-lite",
    instruction=EXTRACTION_INSTRUCTION,
    output_schema=ScriptRubric,
    output_key="extracted_data",
)