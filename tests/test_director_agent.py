"""
tests/test_director_agent.py
============================
Unit tests for the Director Agent — zero network / Gemini calls.

Test strategy
-------------
* ``prompts``   — pure string functions, tested without any mock.
* ``parser``    — pure function tested with hard-coded fixture strings.
* ``schemas``   — Pydantic validation tested by constructing models directly.
* ``agent``     — ``GeminiDirectorService`` is replaced by an ``AsyncMock``
                  so ``DirectorAgent.analyse()`` is tested end-to-end with
                  no HTTP traffic.
* ``node``      — ``director_agent`` singleton is patched so the LangGraph
                  node function is tested in isolation.

Fixtures are defined at module level as plain strings / dicts.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.director.parser import (
    DirectorParseError,
    _extract_json_object,
    _strip_fences,
    parse_director_response,
)
from app.agents.director.prompts import (
    DIRECTOR_SYSTEM_INSTRUCTION,
    build_director_prompt,
)
from app.agents.director.schemas import (
    CharacterAnalysis,
    DirectorAgentInput,
    DirectorAnalysis,
    LocationAnalysis,
    PropAnalysis,
    SceneAnalysis,
    ShootingRequirements,
)
from app.agents.director.agent import DirectorAgent
from app.agents.director.node import director_node
from app.exceptions import AgentExecutionError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_SCREENPLAY = """
FADE IN:

INT. COFFEE SHOP - DAY

ANNA (30s, tired) sits alone. A BARISTA approaches.

BARISTA
Can I help you?

ANNA
Just coffee. Black.

The BARISTA nods and leaves.

FADE OUT.
""".strip()

MINIMAL_ANALYSIS_DICT = {
    "title": "Untitled",
    "genre": "Drama",
    "logline": "A tired woman orders coffee.",
    "scenes": [
        {
            "scene_number": 1,
            "slug_line": "INT. COFFEE SHOP - DAY",
            "int_ext": "INT",
            "location_name": "Coffee Shop",
            "location_query": "coffee shop interior",
            "time_of_day": "DAY",
            "description": "Anna sits alone in a coffee shop. A barista approaches and takes her order.",
            "page_count": 1.0,
            "characters": ["ANNA", "BARISTA"],
            "props": ["coffee cup"],
            "shooting_notes": None,
        }
    ],
    "characters": [
        {
            "name": "ANNA",
            "role": "lead",
            "scene_numbers": [1],
            "description": "Woman in her 30s, tired.",
            "first_appearance": 1,
        },
        {
            "name": "BARISTA",
            "role": "supporting",
            "scene_numbers": [1],
            "description": None,
            "first_appearance": 1,
        },
    ],
    "props": [
        {
            "name": "coffee cup",
            "category": "action_prop",
            "scene_numbers": [1],
            "notes": None,
        }
    ],
    "locations": [
        {
            "name": "Coffee Shop",
            "int_ext": "INT",
            "location_query": "coffee shop interior",
            "scene_numbers": [1],
            "description": "A quiet coffee shop.",
            "shooting_days": 1,
        }
    ],
    "shooting_requirements": {
        "estimated_shoot_days": 1,
        "estimated_budget_tier": "micro",
        "special_equipment": [],
        "vfx_scenes": [],
        "stunt_scenes": [],
        "night_scenes": [],
        "exterior_scenes": [],
        "period_setting": None,
        "summary": "Single-location, one-day shoot.",
    },
}

MINIMAL_ANALYSIS_JSON = json.dumps(MINIMAL_ANALYSIS_DICT)


# ---------------------------------------------------------------------------
# prompts.py
# ---------------------------------------------------------------------------

class TestBuildDirectorPrompt:

    def test_returns_two_strings(self):
        sys_inst, user_prompt = build_director_prompt(MINIMAL_SCREENPLAY)
        assert isinstance(sys_inst, str)
        assert isinstance(user_prompt, str)

    def test_system_instruction_is_constant(self):
        sys_inst, _ = build_director_prompt(MINIMAL_SCREENPLAY)
        assert sys_inst == DIRECTOR_SYSTEM_INSTRUCTION

    def test_screenplay_embedded_in_user_prompt(self):
        _, user_prompt = build_director_prompt(MINIMAL_SCREENPLAY)
        assert MINIMAL_SCREENPLAY in user_prompt

    def test_schema_keywords_present(self):
        _, user_prompt = build_director_prompt(MINIMAL_SCREENPLAY)
        for keyword in ("scenes", "characters", "props", "locations", "shooting_requirements"):
            assert keyword in user_prompt, f"Expected '{keyword}' in prompt"

    def test_max_scenes_clause_added(self):
        _, user_prompt = build_director_prompt(MINIMAL_SCREENPLAY, max_scenes=10)
        assert "10" in user_prompt

    def test_no_max_scenes_clause_when_none(self):
        _, user_prompt = build_director_prompt(MINIMAL_SCREENPLAY, max_scenes=None)
        assert "Only extract the first" not in user_prompt

    def test_empty_screenplay_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            build_director_prompt("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            build_director_prompt("   \n  ")


# ---------------------------------------------------------------------------
# parser.py — helpers
# ---------------------------------------------------------------------------

class TestStripFences:

    def test_strips_json_fence(self):
        text = "```json\n{\"key\": 1}\n```"
        assert _strip_fences(text) == '{"key": 1}'

    def test_strips_bare_fence(self):
        text = "```\n{\"key\": 1}\n```"
        assert _strip_fences(text) == '{"key": 1}'

    def test_passthrough_when_no_fence(self):
        text = '{"key": 1}'
        assert _strip_fences(text) == text

    def test_strips_surrounding_whitespace(self):
        text = "   {\"key\": 1}   "
        assert _strip_fences(text) == '{"key": 1}'


class TestExtractJsonObject:

    def test_extracts_simple_object(self):
        text = 'prefix {"a": 1} suffix'
        result = _extract_json_object(text)
        assert result == '{"a": 1}'

    def test_extracts_nested_object(self):
        text = '{"outer": {"inner": 1}}'
        result = _extract_json_object(text)
        assert result == text

    def test_raises_when_no_object(self):
        with pytest.raises(DirectorParseError, match="No balanced JSON"):
            _extract_json_object("no json here")

    def test_raises_on_unclosed_brace(self):
        with pytest.raises(DirectorParseError):
            _extract_json_object('{"unclosed": ')


# ---------------------------------------------------------------------------
# parser.py — parse_director_response
# ---------------------------------------------------------------------------

class TestParseDirectorResponse:

    def test_parses_valid_json(self):
        result = parse_director_response(MINIMAL_ANALYSIS_JSON)
        assert isinstance(result, DirectorAnalysis)
        assert result.title == "Untitled"
        assert result.scene_count == 1

    def test_parses_json_wrapped_in_fences(self):
        fenced = f"```json\n{MINIMAL_ANALYSIS_JSON}\n```"
        result = parse_director_response(fenced)
        assert result.title == "Untitled"

    def test_raises_on_empty_response(self):
        with pytest.raises(DirectorParseError) as exc_info:
            parse_director_response("")
        assert exc_info.value.reason == "empty_response"

    def test_raises_on_whitespace_response(self):
        with pytest.raises(DirectorParseError) as exc_info:
            parse_director_response("   ")
        assert exc_info.value.reason == "empty_response"

    def test_raises_on_no_json(self):
        with pytest.raises(DirectorParseError) as exc_info:
            parse_director_response("Here is your breakdown: sorry, no JSON today.")
        assert exc_info.value.reason == "no_json_object"

    def test_raises_on_invalid_json(self):
        with pytest.raises(DirectorParseError) as exc_info:
            parse_director_response("{invalid json:::}")
        assert exc_info.value.reason == "invalid_json"

    def test_raises_on_validation_failure(self):
        bad = json.dumps({"scenes": "not-a-list"})
        with pytest.raises(DirectorParseError) as exc_info:
            parse_director_response(bad)
        assert exc_info.value.reason == "validation_error"

    def test_populates_night_scenes_from_scene_data(self):
        data = dict(MINIMAL_ANALYSIS_DICT)
        data["scenes"] = [
            {**MINIMAL_ANALYSIS_DICT["scenes"][0], "time_of_day": "NIGHT", "scene_number": 1}
        ]
        data["shooting_requirements"] = {
            **MINIMAL_ANALYSIS_DICT["shooting_requirements"],
            "night_scenes": [],
        }
        result = parse_director_response(json.dumps(data))
        assert 1 in result.shooting_requirements.night_scenes

    def test_scene_number_ref_warnings_do_not_raise(self):
        """Bad cross-references should warn but not crash."""
        data = dict(MINIMAL_ANALYSIS_DICT)
        data["characters"] = [
            {**MINIMAL_ANALYSIS_DICT["characters"][0], "scene_numbers": [999]}
        ]
        # Should not raise
        result = parse_director_response(json.dumps(data))
        assert isinstance(result, DirectorAnalysis)


# ---------------------------------------------------------------------------
# schemas.py
# ---------------------------------------------------------------------------

class TestSceneAnalysis:

    def test_valid_scene(self):
        scene = SceneAnalysis(
            scene_number=1,
            slug_line="INT. OFFICE - DAY",
            int_ext="INT",
            location_name="Office",
            location_query="corporate office interior",
            time_of_day="DAY",
            description="A tense meeting.",
        )
        assert scene.int_ext == "INT"
        assert scene.time_of_day == "DAY"

    def test_normalises_interior_to_int(self):
        scene = SceneAnalysis(
            scene_number=1,
            slug_line="INT. OFFICE - DAY",
            int_ext="interior",  # type: ignore[arg-type]
            location_name="Office",
            location_query="office",
            time_of_day="DAY",
            description=".",
        )
        assert scene.int_ext == "INT"

    def test_normalises_eve_to_dusk(self):
        scene = SceneAnalysis(
            scene_number=1,
            slug_line="EXT. STREET - EVENING",
            int_ext="EXT",
            location_name="Street",
            location_query="street",
            time_of_day="eve",  # type: ignore[arg-type]
            description=".",
        )
        assert scene.time_of_day == "DUSK"

    def test_empty_characters_defaults_to_list(self):
        scene = SceneAnalysis(
            scene_number=1,
            slug_line="INT. ROOM - DAY",
            int_ext="INT",
            location_name="Room",
            location_query="room",
            time_of_day="DAY",
            description=".",
            characters=None,  # type: ignore[arg-type]
        )
        assert scene.characters == []


class TestDirectorAnalysis:

    def test_lead_characters_property(self):
        analysis = DirectorAnalysis(**MINIMAL_ANALYSIS_DICT)
        leads = analysis.lead_characters
        assert len(leads) == 1
        assert leads[0].name == "ANNA"

    def test_unique_locations_property(self):
        analysis = DirectorAnalysis(**MINIMAL_ANALYSIS_DICT)
        assert "Coffee Shop" in analysis.unique_locations

    def test_scene_count_property(self):
        analysis = DirectorAnalysis(**MINIMAL_ANALYSIS_DICT)
        assert analysis.scene_count == 1

    def test_exterior_scenes_derived_from_scenes(self):
        data = dict(MINIMAL_ANALYSIS_DICT)
        data["scenes"] = [
            {**MINIMAL_ANALYSIS_DICT["scenes"][0], "int_ext": "EXT"}
        ]
        data["shooting_requirements"] = {
            **MINIMAL_ANALYSIS_DICT["shooting_requirements"],
            "exterior_scenes": [],
        }
        analysis = DirectorAnalysis(**data)
        assert 1 in analysis.shooting_requirements.exterior_scenes


class TestDirectorAgentInput:

    def test_valid_input(self):
        inp = DirectorAgentInput(screenplay=MINIMAL_SCREENPLAY)
        assert inp.temperature == 0.1
        assert inp.max_scenes is None

    def test_strips_screenplay_whitespace(self):
        inp = DirectorAgentInput(screenplay=f"  {MINIMAL_SCREENPLAY}  ")
        assert not inp.screenplay.startswith(" ")

    def test_rejects_empty_screenplay(self):
        with pytest.raises(Exception):
            DirectorAgentInput(screenplay="")

    def test_rejects_temperature_out_of_range(self):
        with pytest.raises(Exception):
            DirectorAgentInput(screenplay=MINIMAL_SCREENPLAY, temperature=2.0)


# ---------------------------------------------------------------------------
# agent.py — DirectorAgent (mocked Gemini service)
# ---------------------------------------------------------------------------

class TestDirectorAgent:

    @pytest.fixture
    def mock_service(self):
        svc = MagicMock()
        svc.analyse = AsyncMock(return_value=MINIMAL_ANALYSIS_JSON)
        return svc

    @pytest.mark.asyncio
    async def test_analyse_returns_director_analysis(self, mock_service):
        agent = DirectorAgent(service=mock_service)
        result = await agent.analyse(DirectorAgentInput(screenplay=MINIMAL_SCREENPLAY))
        assert isinstance(result, DirectorAnalysis)
        assert result.title == "Untitled"

    @pytest.mark.asyncio
    async def test_analyse_calls_service_once(self, mock_service):
        agent = DirectorAgent(service=mock_service)
        await agent.analyse(DirectorAgentInput(screenplay=MINIMAL_SCREENPLAY))
        mock_service.analyse.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analyse_passes_temperature(self, mock_service):
        agent = DirectorAgent(service=mock_service)
        await agent.analyse(DirectorAgentInput(screenplay=MINIMAL_SCREENPLAY, temperature=0.5))
        call_kwargs = mock_service.analyse.call_args.kwargs
        assert call_kwargs["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_gemini_error_raises_agent_execution_error(self, mock_service):
        mock_service.analyse.side_effect = RuntimeError("Gemini is down")
        agent = DirectorAgent(service=mock_service)
        with pytest.raises(AgentExecutionError, match="Gemini API call failed"):
            await agent.analyse(DirectorAgentInput(screenplay=MINIMAL_SCREENPLAY))

    @pytest.mark.asyncio
    async def test_parse_error_raises_agent_execution_error(self, mock_service):
        mock_service.analyse = AsyncMock(return_value="not valid json at all")
        agent = DirectorAgent(service=mock_service)
        with pytest.raises(AgentExecutionError, match="parsing failed"):
            await agent.analyse(DirectorAgentInput(screenplay=MINIMAL_SCREENPLAY))


# ---------------------------------------------------------------------------
# node.py — director_node (mocked DirectorAgent)
# ---------------------------------------------------------------------------

class TestDirectorNode:

    def _make_state(self, **overrides) -> dict:
        base = {
            "project_id": "proj-123",
            "agent_type": "full_pipeline",
            "input_data": {},
            "script_draft": MINIMAL_SCREENPLAY,
        }
        base.update(overrides)
        return base

    @pytest.mark.asyncio
    async def test_node_populates_director_analysis_and_scenes(self):
        mock_analysis = DirectorAnalysis(**MINIMAL_ANALYSIS_DICT)

        with patch(
            "app.agents.director.node.director_agent.analyse",
            new=AsyncMock(return_value=mock_analysis),
        ):
            result = await director_node(self._make_state())

        assert "director_analysis" in result
        assert "scenes" in result
        assert len(result["scenes"]) == 1
        assert result["scenes"][0]["scene_number"] == 1

    @pytest.mark.asyncio
    async def test_node_returns_error_when_script_draft_empty(self):
        result = await director_node(self._make_state(script_draft=""))
        assert "error" in result
        assert result.get("director_analysis") is None

    @pytest.mark.asyncio
    async def test_node_skips_when_upstream_error_set(self):
        state = self._make_state(error="upstream broke something")
        result = await director_node(state)
        # State unchanged — no director_analysis added
        assert "director_analysis" not in result

    @pytest.mark.asyncio
    async def test_node_sets_error_on_agent_execution_error(self):
        with patch(
            "app.agents.director.node.director_agent.analyse",
            new=AsyncMock(side_effect=AgentExecutionError("boom")),
        ):
            result = await director_node(self._make_state())

        assert "error" in result
        assert "director_node failed" in result["error"]

    @pytest.mark.asyncio
    async def test_node_scene_list_contains_expected_keys(self):
        mock_analysis = DirectorAnalysis(**MINIMAL_ANALYSIS_DICT)

        with patch(
            "app.agents.director.node.director_agent.analyse",
            new=AsyncMock(return_value=mock_analysis),
        ):
            result = await director_node(self._make_state())

        scene = result["scenes"][0]
        for key in ("scene_number", "title", "description", "location_query",
                    "int_ext", "time_of_day", "characters", "props"):
            assert key in scene, f"Expected key '{key}' in scene dict"
