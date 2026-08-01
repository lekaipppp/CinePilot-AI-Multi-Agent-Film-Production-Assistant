"""
app/agents/director/prompts.py
==============================
Prompt template and builder for the Director Agent.

Architecture rule
-----------------
This module contains **only strings and one pure function**.
It has zero imports from the rest of the application and no I/O.
That makes prompts independently testable and trivially editable
without touching any agent or service logic.

Prompt design notes
-------------------
* The system instruction is separated from the user instruction so that
  callers using the Gemini Chat API can attach the system instruction to
  the model config rather than prepending it to every turn.
* The JSON schema is embedded directly in the prompt rather than using
  function-calling / tool-use so the agent is compatible with every
  Gemini API tier (Flash, Pro, Ultra) and requires no SDK-specific
  function-declaration boilerplate.
* We use explicit enum values (INT/EXT, DAY/NIGHT/DUSK/DAWN) that match
  the CHECK constraints on the ``scenes`` table so parser output can be
  written to the DB without re-mapping.
* A <SCREENPLAY> XML-style fence delimits the user-supplied text from
  the prompt instructions, preventing accidental prompt injection from
  screenplay content that contains imperative sentences.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# System instruction (model persona — attached once per session)
# ---------------------------------------------------------------------------

DIRECTOR_SYSTEM_INSTRUCTION: str = """
You are an experienced Hollywood director and script supervisor with 25 years
of pre-production experience across studio and independent film.

Your role is to perform a meticulous script breakdown — the same analysis
a professional script supervisor produces before principal photography.

You extract structured production data from screenplays with surgical precision,
following industry-standard terminology (AMPAS / PGA conventions).
""".strip()


# ---------------------------------------------------------------------------
# User-turn prompt template
# ---------------------------------------------------------------------------
# Placeholders:
#   {screenplay}   — the full screenplay text submitted by the user
#   {scene_limit}  — optional max scenes (default "all")

DIRECTOR_ANALYSIS_TEMPLATE: str = """
Analyse the following screenplay and return a **single, valid JSON object**
that conforms exactly to the schema below.

<SCREENPLAY>
{screenplay}
</SCREENPLAY>

─────────────────────────────────────────────────────────────────────────────
REQUIRED JSON SCHEMA
─────────────────────────────────────────────────────────────────────────────

{{
  "title":   "<string | null>  — film title extracted from the title page",
  "genre":   "<string | null>  — primary genre (e.g. Thriller, Drama, Comedy)",
  "logline": "<string | null>  — one-sentence story summary (≤ 40 words)",

  "scenes": [
    {{
      "scene_number":    "<integer>   — sequential 1-based scene number",
      "slug_line":       "<string>    — full scene heading (e.g. INT. OFFICE - DAY)",
      "int_ext":         "<'INT'|'EXT'|'INT/EXT'>",
      "location_name":   "<string>    — descriptive location name (e.g. 'Police Precinct')",
      "location_query":  "<string>    — Google Maps search query for this location",
      "time_of_day":     "<'DAY'|'NIGHT'|'DUSK'|'DAWN'|'CONTINUOUS'|'LATER'|'MOMENTS LATER'>",
      "description":     "<string>    — 1–3 sentence summary of the scene action",
      "page_count":      "<number>    — estimated pages (1 page ≈ 1 min screen time)",
      "characters":      ["<string>", "..."],
      "props":           ["<string>", "..."],
      "shooting_notes":  "<string | null>  — special requirements (stunts, VFX, rain, etc.)"
    }}
  ],

  "characters": [
    {{
      "name":             "<string>   — character name in CAPS as written in script",
      "role":             "<'lead'|'supporting'|'featured_extra'|'extra'>",
      "scene_numbers":    [<integer>, "..."],
      "description":      "<string | null>  — brief physical/personality description",
      "first_appearance": "<integer>  — scene_number of first appearance"
    }}
  ],

  "props": [
    {{
      "name":          "<string>  — prop name",
      "category":      "<'weapon'|'vehicle'|'costume'|'set_dressing'|'action_prop'|'other'>",
      "scene_numbers": [<integer>, "..."],
      "notes":         "<string | null>  — special handling, period accuracy, SFX, etc."
    }}
  ],

  "locations": [
    {{
      "name":          "<string>  — descriptive location name",
      "int_ext":       "<'INT'|'EXT'|'INT/EXT'>",
      "location_query":"<string>  — specific Google Maps search query",
      "scene_numbers": [<integer>, "..."],
      "description":   "<string | null>  — atmosphere, set requirements, access notes",
      "shooting_days": "<integer | null> — estimated days needed at this location"
    }}
  ],

  "shooting_requirements": {{
    "estimated_shoot_days":   "<integer | null>",
    "estimated_budget_tier":  "<'micro'|'low'|'mid'|'high'|'studio'|null>",
    "special_equipment":      ["<string>", "..."],
    "vfx_scenes":             [<integer>, "..."],
    "stunt_scenes":           [<integer>, "..."],
    "night_scenes":           [<integer>, "..."],
    "exterior_scenes":        [<integer>, "..."],
    "period_setting":         "<string | null>  — e.g. '1940s Los Angeles'",
    "summary":                "<string>  — 2–4 sentence production overview"
  }}
}}

─────────────────────────────────────────────────────────────────────────────
STRICT RULES
─────────────────────────────────────────────────────────────────────────────
1.  Return ONLY the JSON object — no markdown fences, no commentary.
2.  Every scene in the screenplay must appear in "scenes".{scene_limit_clause}
3.  scene_number values must be sequential integers starting at 1.
4.  All scene_number references in characters/props/locations must exist.
5.  int_ext must be exactly one of: INT, EXT, INT/EXT
6.  time_of_day must be exactly one of: DAY, NIGHT, DUSK, DAWN,
    CONTINUOUS, LATER, MOMENTS LATER
7.  If a field cannot be determined, use null — never omit the key.
8.  Character names must match the screenplay exactly (CAPS convention).
""".strip()


# ---------------------------------------------------------------------------
# Builder function
# ---------------------------------------------------------------------------

def build_director_prompt(
    screenplay: str,
    max_scenes: int | None = None,
) -> tuple[str, str]:
    """
    Construct the (system_instruction, user_prompt) tuple for the Director Agent.

    Parameters
    ----------
    screenplay:
        Full screenplay text submitted by the user.
    max_scenes:
        Optional upper bound on the number of scenes extracted.
        When None, all scenes are extracted.

    Returns
    -------
    tuple[str, str]
        ``(system_instruction, user_prompt)`` ready to be passed to Gemini.
        The system instruction is the model persona; the user prompt is the
        per-call analysis request.
    """
    if not screenplay or not screenplay.strip():
        raise ValueError("screenplay must be a non-empty string")

    scene_limit_clause = (
        f"\n    Only extract the first {max_scenes} scenes if the screenplay is long."
        if max_scenes is not None
        else ""
    )

    user_prompt = DIRECTOR_ANALYSIS_TEMPLATE.format(
        screenplay=screenplay.strip(),
        scene_limit_clause=scene_limit_clause,
    )

    return DIRECTOR_SYSTEM_INSTRUCTION, user_prompt
