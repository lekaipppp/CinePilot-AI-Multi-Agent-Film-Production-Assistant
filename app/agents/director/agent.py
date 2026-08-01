"""
app/agents/director/agent.py
============================
``DirectorAgent`` — the orchestrating class for screenplay analysis.

The module-level ``director_agent`` singleton is created lazily via
``_get_director_agent()`` so that importing this module never triggers
a Gemini SDK call at startup.
"""

from __future__ import annotations

from app.agents.director.parser import DirectorParseError, parse_director_response
from app.agents.director.prompts import build_director_prompt
from app.agents.director.schemas import DirectorAgentInput, DirectorAnalysis
from app.agents.director.service import GeminiDirectorService
from app.exceptions import AgentExecutionError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DirectorAgent:
    """
    Orchestrates screenplay analysis using the Gemini API.

    Safe to instantiate without GEMINI_API_KEY — the key is only required
    when ``analyse()`` is actually called.
    """

    def __init__(self, service: GeminiDirectorService | None = None) -> None:
        # Accept an injected service (for tests); otherwise create one lazily.
        # GeminiDirectorService.__init__ is now safe to call without a key.
        self._service = service or GeminiDirectorService()

    async def analyse(self, input_data: DirectorAgentInput) -> DirectorAnalysis:
        """
        Analyse a screenplay and return a structured ``DirectorAnalysis``.

        Raises
        ------
        AgentExecutionError
            Wraps any Gemini / parse error with a descriptive message.
            Also raised (with a clear message) when GEMINI_API_KEY is not set.
        """
        logger.info(
            "DirectorAgent.analyse started",
            extra={
                "screenplay_chars": len(input_data.screenplay),
                "max_scenes":       input_data.max_scenes,
                "temperature":      input_data.temperature,
            },
        )

        # ── 1. Build prompt ────────────────────────────────────────────
        try:
            system_instruction, user_prompt = build_director_prompt(
                screenplay=input_data.screenplay,
                max_scenes=input_data.max_scenes,
            )
        except ValueError as exc:
            raise AgentExecutionError(f"Prompt build failed: {exc}") from exc

        # ── 2. Call Gemini ─────────────────────────────────────────────
        try:
            raw_response = await self._service.analyse(
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                temperature=input_data.temperature,
            )
        except (RuntimeError, ImportError) as exc:
            # Clear message for missing key / package
            raise AgentExecutionError(str(exc)) from exc
        except Exception as exc:
            raise AgentExecutionError(
                f"Gemini API call failed in DirectorAgent: {exc}"
            ) from exc

        # ── 3. Parse + validate ────────────────────────────────────────
        try:
            analysis = parse_director_response(raw_response)
        except DirectorParseError as exc:
            raise AgentExecutionError(
                f"Director response parsing failed ({exc.reason}): {exc}"
            ) from exc

        logger.info(
            "DirectorAgent.analyse completed",
            extra={
                "title":           analysis.title,
                "scene_count":     analysis.scene_count,
                "character_count": len(analysis.characters),
                "prop_count":      len(analysis.props),
                "location_count":  len(analysis.locations),
            },
        )

        return analysis


# ---------------------------------------------------------------------------
# Module-level singleton — built once per process, lazily on first access
# ---------------------------------------------------------------------------

_director_agent_instance: DirectorAgent | None = None


def _get_director_agent() -> DirectorAgent:
    """Return (or lazily create) the shared DirectorAgent singleton."""
    global _director_agent_instance
    if _director_agent_instance is None:
        _director_agent_instance = DirectorAgent()
    return _director_agent_instance


# Backward-compatible module-level name.
# Accessing ``director_agent.analyse(...)`` triggers lazy creation.
class _AgentProxy:
    """Proxy that creates the DirectorAgent on first attribute access."""
    def __getattr__(self, item):
        return getattr(_get_director_agent(), item)


director_agent = _AgentProxy()
