"""
app/agents/director/schemas.py
==============================
Pydantic v2 schemas for Director Agent input and output.

Architecture rule
-----------------
This module contains **only data shapes** — no I/O, no external imports
beyond the standard library and Pydantic.  Everything the agent produces
flows through these types, giving the rest of the application a single,
validated, type-safe contract to depend on.

Design decisions
----------------
``IntExt`` / ``TimeOfDay`` / ``PropCategory`` / ``CharacterRole``
    Literal string enums instead of Python ``enum.Enum`` so that:
    * JSON serialisation produces plain strings (no ".value" needed).
    * Values map 1-to-1 to the CHECK constraints on the ``scenes`` table.
    * Pydantic's error messages include the valid literals by default.

``page_count``
    A ``float`` because screenplay pages use eighths (1/8, 2/8 … 8/8).

All fields that Gemini might not be able to determine are ``Optional``
with a ``None`` default so the schema is lenient enough for incomplete
or short-form screenplays, while still enforcing all known constraints.

``DirectorAnalysis``
    The top-level schema that the parser returns and the LangGraph node
    writes into AgentState.  Its ``model_config`` makes it trivially
    serialisable to ``dict`` for JSON storage in the ``agent_sessions``
    JSONB column.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Primitive enums (Literal types)
# ---------------------------------------------------------------------------

IntExt      = Literal["INT", "EXT", "INT/EXT"]
TimeOfDay   = Literal["DAY", "NIGHT", "DUSK", "DAWN", "CONTINUOUS", "LATER", "MOMENTS LATER"]
CharRole    = Literal["lead", "supporting", "featured_extra", "extra"]
PropCat     = Literal["weapon", "vehicle", "costume", "set_dressing", "action_prop", "other"]
BudgetTier  = Literal["micro", "low", "mid", "high", "studio"]


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class DirectorAgentInput(BaseModel):
    """
    Payload accepted by ``DirectorAgent.analyse()``.

    ``screenplay``
        Full screenplay text (plain text or Final Draft export).
        Must be non-empty; whitespace-only strings are rejected.
    ``max_scenes``
        Optional extraction limit — useful for very long screenplays
        during development / testing.
    ``temperature``
        Gemini sampling temperature (0.0 = deterministic, 1.0 = creative).
        Lower values produce more consistent structured output.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    screenplay: Annotated[str, Field(min_length=10, description="Full screenplay text.")]
    max_scenes: Optional[int] = Field(
        default=None,
        ge=1,
        le=500,
        description="Maximum number of scenes to extract (None = all).",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Gemini sampling temperature.",
    )


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class SceneAnalysis(BaseModel):
    """A single scene extracted from the screenplay."""

    model_config = ConfigDict(str_strip_whitespace=True)

    scene_number:   int = Field(ge=1, description="Sequential 1-based scene number.")
    slug_line:      str = Field(description="Full scene heading (e.g. 'INT. OFFICE - DAY').")
    int_ext:        IntExt
    location_name:  str = Field(description="Descriptive location name.")
    location_query: str = Field(description="Google Maps search query for this location.")
    time_of_day:    TimeOfDay
    description:    str = Field(description="1–3 sentence scene action summary.")
    page_count:     float = Field(default=1.0, ge=0.125, description="Estimated page count.")
    characters:     list[str] = Field(default_factory=list, description="Character names in this scene.")
    props:          list[str] = Field(default_factory=list, description="Props required in this scene.")
    shooting_notes: Optional[str] = Field(default=None, description="Special shooting requirements.")

    @field_validator("characters", "props", mode="before")
    @classmethod
    def _coerce_list(cls, v: Any) -> list:
        """Accept None or missing lists gracefully."""
        if v is None:
            return []
        return v

    @field_validator("int_ext", mode="before")
    @classmethod
    def _normalise_int_ext(cls, v: Any) -> str:
        """Normalise common variants (Interior, I/E, etc.) to INT/EXT."""
        mapping = {
            "interior": "INT",
            "exterior": "EXT",
            "i/e":      "INT/EXT",
            "e/i":      "INT/EXT",
            "int./ext.":"INT/EXT",
        }
        if isinstance(v, str):
            lower = v.strip().lower().rstrip(".")
            return mapping.get(lower, v.strip().upper())
        return v

    @field_validator("time_of_day", mode="before")
    @classmethod
    def _normalise_time_of_day(cls, v: Any) -> str:
        """Normalise common shorthand values."""
        mapping = {
            "d":         "DAY",
            "n":         "NIGHT",
            "eve":       "DUSK",
            "evening":   "DUSK",
            "twilight":  "DUSK",
            "sunrise":   "DAWN",
            "cont.":     "CONTINUOUS",
            "cont":      "CONTINUOUS",
        }
        if isinstance(v, str):
            lower = v.strip().lower()
            return mapping.get(lower, v.strip().upper())
        return v


# ---------------------------------------------------------------------------
# Character
# ---------------------------------------------------------------------------

class CharacterAnalysis(BaseModel):
    """A character extracted from the screenplay."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name:             str   = Field(description="Character name in CAPS.")
    role:             CharRole = Field(default="supporting")
    scene_numbers:    list[int] = Field(default_factory=list)
    description:      Optional[str] = None
    first_appearance: int   = Field(ge=1, description="Scene number of first appearance.")

    @field_validator("name", mode="before")
    @classmethod
    def _uppercase_name(cls, v: Any) -> str:
        """Normalise character names to uppercase."""
        return str(v).strip().upper() if v else v

    @model_validator(mode="after")
    def _set_first_appearance_from_scenes(self) -> "CharacterAnalysis":
        """If first_appearance is 0 but scene_numbers is populated, derive it."""
        if self.scene_numbers and self.first_appearance < 1:
            self.first_appearance = min(self.scene_numbers)
        return self


# ---------------------------------------------------------------------------
# Prop
# ---------------------------------------------------------------------------

class PropAnalysis(BaseModel):
    """A prop or physical item extracted from the screenplay."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name:          str      = Field(description="Prop name.")
    category:      PropCat  = Field(default="other")
    scene_numbers: list[int] = Field(default_factory=list)
    notes:         Optional[str] = None


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

class LocationAnalysis(BaseModel):
    """A distinct filming location consolidated across all scenes."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name:           str    = Field(description="Descriptive location name.")
    int_ext:        IntExt
    location_query: str    = Field(description="Google Maps search query.")
    scene_numbers:  list[int] = Field(default_factory=list)
    description:    Optional[str] = None
    shooting_days:  Optional[int] = Field(default=None, ge=1)


# ---------------------------------------------------------------------------
# Shooting requirements
# ---------------------------------------------------------------------------

class ShootingRequirements(BaseModel):
    """Production-level requirements extracted from the screenplay."""

    model_config = ConfigDict(str_strip_whitespace=True)

    estimated_shoot_days:  Optional[int]        = Field(default=None, ge=1)
    estimated_budget_tier: Optional[BudgetTier] = None
    special_equipment:     list[str]            = Field(default_factory=list)
    vfx_scenes:            list[int]            = Field(default_factory=list)
    stunt_scenes:          list[int]            = Field(default_factory=list)
    night_scenes:          list[int]            = Field(default_factory=list)
    exterior_scenes:       list[int]            = Field(default_factory=list)
    period_setting:        Optional[str]        = None
    summary:               str                  = Field(default="")

    @field_validator(
        "special_equipment", "vfx_scenes", "stunt_scenes",
        "night_scenes", "exterior_scenes",
        mode="before",
    )
    @classmethod
    def _coerce_list(cls, v: Any) -> list:
        if v is None:
            return []
        return v


# ---------------------------------------------------------------------------
# Top-level analysis result
# ---------------------------------------------------------------------------

class DirectorAnalysis(BaseModel):
    """
    Complete structured breakdown of a screenplay produced by the Director Agent.

    This is the single type written to ``AgentState.director_analysis`` and
    stored in the ``agent_sessions.state_snapshot`` JSONB column.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        # Allow the model to be serialised to a plain dict for JSONB storage
        # without needing model.model_dump() at the call site.
        populate_by_name=True,
    )

    title:                Optional[str]               = None
    genre:                Optional[str]               = None
    logline:              Optional[str]               = None
    scenes:               list[SceneAnalysis]          = Field(default_factory=list)
    characters:           list[CharacterAnalysis]      = Field(default_factory=list)
    props:                list[PropAnalysis]           = Field(default_factory=list)
    locations:            list[LocationAnalysis]       = Field(default_factory=list)
    shooting_requirements: ShootingRequirements        = Field(
        default_factory=ShootingRequirements
    )

    # ------------------------------------------------------------------
    # Derived / computed helpers
    # ------------------------------------------------------------------

    @property
    def scene_count(self) -> int:
        return len(self.scenes)

    @property
    def unique_locations(self) -> list[str]:
        return list(dict.fromkeys(s.location_name for s in self.scenes))

    @property
    def lead_characters(self) -> list[CharacterAnalysis]:
        return [c for c in self.characters if c.role == "lead"]

    @model_validator(mode="after")
    def _derive_night_exterior_lists(self) -> "DirectorAnalysis":
        """
        Back-fill shooting_requirements.night_scenes / exterior_scenes
        if Gemini did not populate them but we have scene data to derive
        them from.
        """
        req = self.shooting_requirements
        if not req.night_scenes:
            req.night_scenes = [
                s.scene_number for s in self.scenes if s.time_of_day == "NIGHT"
            ]
        if not req.exterior_scenes:
            req.exterior_scenes = [
                s.scene_number for s in self.scenes if s.int_ext in ("EXT", "INT/EXT")
            ]
        return self
