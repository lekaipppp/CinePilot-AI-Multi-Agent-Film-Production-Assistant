from pydantic import Basemodel, Field 
#pydantic is a data validation library, it acts as a gatekeeper for my code.
#Ensuring any data entered into the system matches the exact structure
#Basemodel is the core building block of Pydanitc,
#=========================================================================
from typing import List, Optional 
#This imports Python type hints
#It tells Python what kind of data a variable should contain.
#Optional means one value may exist, or it may be None.
#=========================================================================
from google.adk.agents import Agent, LimAgent
#ADK stands for Agent Development Kit, it is a framework of building AI agents


class Scene(Basemodel):
# BaseModel is a class that comes from Pydantic,
# --- Auto validation
# --- JSON Exporting
    scene_number: str = Field(description="Sequential scene number as it appears in the script")

    location_setting: str = Field(description="Short Description of the location, e.g. 'urban alley'")

    indoor_or_not: str = Field(description="Indoor', 'Outdoor', or 'Unspecified'")

    time_of_day: str = Field(default="unspecified", description="Time of day for the scene")

    weather_of_scene: str = Field(default="unspecified", description="Weather conditions for the scene")

    characters_in_scene: List[str] = Field(description="List of characters present in the scene")

    props_in_scene: List[str] = Field(description="List all props that are present in the scene")

    shooting_requirements: Optional[List[str]] = Field(default=None, description="List of shooting requirements for the scene. e.g. 'weapon on set', 'stunt', 'night shoot', 'VFX', 'crowd scene', 'animal', 'minor on set")

    