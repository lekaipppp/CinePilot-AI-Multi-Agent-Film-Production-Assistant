"""
app/agents/director/parser.py
==============================
Raw Gemini response → validated ``DirectorAnalysis``.

Architecture rule
-----------------
This module is a **pure function layer** — no I/O, no Gemini calls,
no database access.  It accepts a raw string and returns a typed result.
That makes it independently unit-testable with any fixture string.

Parsing strategy
----------------
1. **Strip** markdown code fences that Gemini occasionally wraps around
   JSON despite being told not to.  We handle both `` ```json `` and bare
   `` ``` `` fences plus any leading/trailing whitespace.
2. **Find the outermost JSON object** using a bracket-counter scan rather
   than regex so nested ``{`` / ``}`` inside string values are handled
   correctly.  This is more robust than ``re.search(r'\{.*\}', raw, re.S)``
   which can return a partial match on malformed output.
3. **Parse** with ``json.loads()`` — raises ``json.JSONDecodeError`` on
   invalid JSON, which we wrap into ``DirectorParseError``.
4. **Validate** with Pydantic.  ``DirectorAnalysis(**data)`` runs all
   field validators, coercions, and model validators defined in schemas.py.
   Pydantic ``ValidationError`` is caught and re-raised as ``DirectorParseError``
   so callers always see one exception type from this module.
5. **Post-validate** cross-field consistency:
   * Scene numbers referenced in characters/props/locations are verified
     to exist in the scenes list.
   * Duplicate scene numbers are detected and reported.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.agents.director.schemas import DirectorAnalysis
from app.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Module-specific exception
# ---------------------------------------------------------------------------

class DirectorParseError(Exception):
    """
    Raised when the raw Gemini response cannot be parsed or validated.

    Attributes
    ----------
    raw_response:
        The original string received from Gemini (truncated to 500 chars
        in the message for log safety; full text stored here).
    reason:
        Short machine-readable reason code.  One of:
        ``"empty_response"`` | ``"no_json_object"`` |
        ``"invalid_json"``   | ``"validation_error"``
    """

    def __init__(self, message: str, raw_response: str = "", reason: str = "unknown"):
        super().__init__(message)
        self.raw_response = raw_response
        self.reason = reason


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(
    r"^```(?:json)?\s*\n?(.*?)\n?```\s*$",
    re.DOTALL | re.IGNORECASE,
)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from Gemini output."""
    m = _FENCE_RE.match(text.strip())
    return m.group(1).strip() if m else text.strip()


def _extract_json_object(text: str) -> str:
    """
    Find the outermost ``{ … }`` object in *text* using a bracket counter.

    Returns the JSON substring on success.
    Raises ``DirectorParseError`` if no balanced object is found.
    """
    depth = 0
    start = None

    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return text[start : i + 1]

    raise DirectorParseError(
        message=(
            f"No balanced JSON object found in Gemini response. "
            f"First 200 chars: {text[:200]!r}"
        ),
        raw_response=text,
        reason="no_json_object",
    )


def _validate_scene_number_refs(data: DirectorAnalysis) -> list[str]:
    """
    Check that all scene_number references in characters / props / locations
    point to scenes that actually exist in data.scenes.

    Returns a list of warning strings (empty = no issues).
    These are logged as warnings but do NOT raise — a partial analysis
    is better than no analysis.
    """
    valid = {s.scene_number for s in data.scenes}
    warnings: list[str] = []

    for char in data.characters:
        bad = [n for n in char.scene_numbers if n not in valid]
        if bad:
            warnings.append(f"Character '{char.name}' references unknown scenes {bad}")

    for prop in data.props:
        bad = [n for n in prop.scene_numbers if n not in valid]
        if bad:
            warnings.append(f"Prop '{prop.name}' references unknown scenes {bad}")

    for loc in data.locations:
        bad = [n for n in loc.scene_numbers if n not in valid]
        if bad:
            warnings.append(f"Location '{loc.name}' references unknown scenes {bad}")

    return warnings


def _check_duplicate_scene_numbers(data: DirectorAnalysis) -> list[str]:
    """Return warnings for duplicate scene_number values."""
    seen: set[int] = set()
    dupes: set[int] = set()
    for s in data.scenes:
        if s.scene_number in seen:
            dupes.add(s.scene_number)
        seen.add(s.scene_number)
    if dupes:
        return [f"Duplicate scene numbers detected: {sorted(dupes)}"]
    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_director_response(raw_response: str) -> DirectorAnalysis:
    """
    Parse and validate a raw Gemini text response into a ``DirectorAnalysis``.

    Parameters
    ----------
    raw_response:
        The raw string returned by the Gemini API.

    Returns
    -------
    DirectorAnalysis
        Fully validated, type-annotated analysis ready for use by the agent.

    Raises
    ------
    DirectorParseError
        If the response is empty, contains no JSON object, contains invalid
        JSON, or fails Pydantic validation.
    """
    if not raw_response or not raw_response.strip():
        raise DirectorParseError(
            message="Gemini returned an empty response.",
            raw_response=raw_response,
            reason="empty_response",
        )

    # Step 1 — strip markdown fences
    cleaned = _strip_fences(raw_response)

    # Step 2 — locate the outermost JSON object
    json_str = _extract_json_object(cleaned)

    # Step 3 — parse JSON
    try:
        data: dict[str, Any] = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise DirectorParseError(
            message=f"Invalid JSON from Gemini: {exc}",
            raw_response=raw_response,
            reason="invalid_json",
        ) from exc

    # Step 4 — Pydantic validation
    try:
        analysis = DirectorAnalysis(**data)
    except ValidationError as exc:
        # Collect the first 5 errors for the message; full detail in raw
        errors = exc.errors()[:5]
        summary = "; ".join(
            f"{'/'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in errors
        )
        raise DirectorParseError(
            message=f"Director analysis validation failed: {summary}",
            raw_response=raw_response,
            reason="validation_error",
        ) from exc

    # Step 5 — cross-field consistency checks (warnings only)
    warnings = (
        _check_duplicate_scene_numbers(analysis)
        + _validate_scene_number_refs(analysis)
    )
    if warnings:
        for w in warnings:
            logger.warning("DirectorParser: %s", w, extra={"scene_count": analysis.scene_count})

    logger.info(
        "Director analysis parsed successfully",
        extra={
            "scene_count":     analysis.scene_count,
            "character_count": len(analysis.characters),
            "prop_count":      len(analysis.props),
            "location_count":  len(analysis.locations),
        },
    )

    return analysis
