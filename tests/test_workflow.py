"""
tests/test_workflow.py
======================
Unit tests for the CinePilot LangGraph workflow.

Strategy
--------
* Every test builds a minimal ``AgentState`` dict and runs it through the
  graph with all five content nodes replaced by ``AsyncMock`` stubs.
* Tests verify *state transitions*, *edge routing*, and the *output shape*
  returned by ``assemble_output_node`` — not business logic.
* No Gemini / Maps / Weather API calls are made.
* The graph is rebuilt fresh for each test class by calling ``build_graph()``
  with patched node imports — this avoids polluting the module-level
  ``cinepilot_graph`` singleton.

Tested surface
--------------
edges.py          — routing functions (pure, no mocks needed)
output.py         — assemble_output_node (pure, no mocks needed)
graph.py          — full pipeline integration (all nodes mocked)
WorkflowRunner    — run() method (graph mocked)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.graph.edges import (
    ERROR_HANDLER,
    route_after_budget,
    route_after_director,
    route_after_location,
    route_after_risk,
    route_after_scheduler,
)
from app.graph.output import assemble_output_node, _determine_status
from app.graph.graph import WorkflowRunner, build_graph
from app.graph.state import AgentState
from app.exceptions import AgentExecutionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_state(**overrides) -> AgentState:
    """Return a minimal valid AgentState with optional field overrides."""
    base: AgentState = {
        "project_id":  "test-proj-001",
        "agent_type":  "production_planning",
        "script_draft": "FADE IN:\n\nINT. ROOM - DAY\n\nFADE OUT.",
        "input_data":  {},
        "messages":    [],
        "run_metadata": {"run_id": "test-run-001"},
    }
    base.update(overrides)
    return base


SAMPLE_DIRECTOR_ANALYSIS = {
    "title":    "Test Film",
    "genre":    "Drama",
    "logline":  "A test logline.",
    "scenes":   [],
    "characters": [],
    "props":    [],
    "locations": [],
    "shooting_requirements": {},
}

SAMPLE_SCHEDULE = {
    "shoot_days":       [{"date": "2024-06-01", "scenes": [1], "location": "Studio"}],
    "total_shoot_days": 1,
    "scheduling_notes": "Single day shoot.",
}

SAMPLE_BUDGET = {
    "currency":             "USD",
    "departments":          [{"name": "cast", "estimated_cost": 50000}],
    "total_estimated_cost": 50000,
    "contingency_pct":      10.0,
    "assumptions":          "Low-budget indie.",
}

SAMPLE_RISK = {
    "overall_risk_level": "low",
    "summary":            "Minimal risks identified.",
    "recommendations":    "Proceed.",
    "items":              [],
}


# ---------------------------------------------------------------------------
# edges.py — routing functions
# ---------------------------------------------------------------------------

class TestEdgeRouters:
    """Routing functions are pure — no mocks needed."""

    def test_director_routes_to_location_on_ok(self):
        state = _empty_state()
        assert route_after_director(state) == "location"

    def test_director_routes_to_error_handler_on_error(self):
        state = _empty_state(error="director failed")
        assert route_after_director(state) == ERROR_HANDLER

    def test_location_routes_to_scheduler_on_ok(self):
        assert route_after_location(_empty_state()) == "scheduler"

    def test_location_routes_to_error_handler_on_error(self):
        assert route_after_location(_empty_state(error="e")) == ERROR_HANDLER

    def test_scheduler_routes_to_budget_on_ok(self):
        assert route_after_scheduler(_empty_state()) == "budget"

    def test_scheduler_routes_to_error_handler_on_error(self):
        assert route_after_scheduler(_empty_state(error="e")) == ERROR_HANDLER

    def test_budget_routes_to_risk_on_ok(self):
        assert route_after_budget(_empty_state()) == "risk"

    def test_budget_routes_to_error_handler_on_error(self):
        assert route_after_budget(_empty_state(error="e")) == ERROR_HANDLER

    def test_risk_routes_to_assemble_output_on_ok(self):
        assert route_after_risk(_empty_state()) == "assemble_output"

    def test_risk_routes_to_error_handler_on_error(self):
        assert route_after_risk(_empty_state(error="e")) == ERROR_HANDLER

    def test_empty_error_string_treated_as_ok(self):
        """Empty string error is falsy — treated as success."""
        state = _empty_state(error="")
        assert route_after_director(state) == "location"


# ---------------------------------------------------------------------------
# output.py — _determine_status + assemble_output_node
# ---------------------------------------------------------------------------

class TestDetermineStatus:

    def test_complete_when_all_keys_present(self):
        state = _empty_state(
            director_analysis=SAMPLE_DIRECTOR_ANALYSIS,
            location_results=[{}],
            schedule=SAMPLE_SCHEDULE,
            budget_estimate=SAMPLE_BUDGET,
            risk_report=SAMPLE_RISK,
        )
        assert _determine_status(state) == "complete"

    def test_failed_when_error_set(self):
        state = _empty_state(
            error="something broke",
            director_analysis=SAMPLE_DIRECTOR_ANALYSIS,
        )
        assert _determine_status(state) == "failed"

    def test_partial_when_missing_keys(self):
        # No schedule, no budget, no risk
        state = _empty_state(
            director_analysis=SAMPLE_DIRECTOR_ANALYSIS,
            location_results=[{}],
        )
        assert _determine_status(state) == "partial"

    def test_partial_overrides_missing_even_without_error(self):
        state = _empty_state(
            director_analysis=SAMPLE_DIRECTOR_ANALYSIS,
        )
        assert _determine_status(state) == "partial"


class TestAssembleOutputNode:

    @pytest.mark.asyncio
    async def test_always_writes_production_plan(self):
        state = _empty_state()
        result = await assemble_output_node(state)
        assert "production_plan" in result

    @pytest.mark.asyncio
    async def test_status_is_partial_on_empty_pipeline(self):
        result = await assemble_output_node(_empty_state())
        assert result["production_plan"]["status"] == "partial"

    @pytest.mark.asyncio
    async def test_status_is_failed_when_error_set(self):
        state = _empty_state(error="director blew up")
        result = await assemble_output_node(state)
        plan = result["production_plan"]
        assert plan["status"] == "failed"
        assert plan["error"] == "director blew up"

    @pytest.mark.asyncio
    async def test_status_complete_with_all_keys(self):
        state = _empty_state(
            director_analysis=SAMPLE_DIRECTOR_ANALYSIS,
            scenes=[{"scene_number": 1}],
            location_results=[{}],
            schedule=SAMPLE_SCHEDULE,
            budget_estimate=SAMPLE_BUDGET,
            risk_report=SAMPLE_RISK,
        )
        result = await assemble_output_node(state)
        assert result["production_plan"]["status"] == "complete"

    @pytest.mark.asyncio
    async def test_plan_has_all_required_keys(self):
        result = await assemble_output_node(_empty_state())
        plan = result["production_plan"]
        for key in (
            "project_id", "status", "error", "title", "genre", "logline",
            "scene_count", "scenes", "characters", "props", "locations",
            "shooting_requirements", "location_results", "weather_reports",
            "schedule", "budget_estimate", "risk_report", "run_metadata",
        ):
            assert key in plan, f"Missing key in production_plan: '{key}'"

    @pytest.mark.asyncio
    async def test_assembles_director_title(self):
        state = _empty_state(director_analysis=SAMPLE_DIRECTOR_ANALYSIS)
        result = await assemble_output_node(state)
        assert result["production_plan"]["title"] == "Test Film"

    @pytest.mark.asyncio
    async def test_scene_count_matches_scenes_list(self):
        state = _empty_state(
            scenes=[{"scene_number": 1}, {"scene_number": 2}]
        )
        result = await assemble_output_node(state)
        assert result["production_plan"]["scene_count"] == 2

    @pytest.mark.asyncio
    async def test_run_metadata_preserved(self):
        state = _empty_state(run_metadata={"run_id": "abc-123"})
        result = await assemble_output_node(state)
        assert result["production_plan"]["run_metadata"]["run_id"] == "abc-123"

    @pytest.mark.asyncio
    async def test_assembled_at_timestamp_added(self):
        result = await assemble_output_node(_empty_state())
        meta = result["production_plan"]["run_metadata"]
        assert "assembled_at" in meta


# ---------------------------------------------------------------------------
# Full pipeline integration — all content nodes mocked
# ---------------------------------------------------------------------------

class TestFullPipeline:
    """
    Run the compiled graph end-to-end with content nodes replaced by
    AsyncMocks that return pre-built state fragments.
    """

    def _make_mock_director(self) -> AsyncMock:
        async def _mock(state: AgentState) -> AgentState:
            return {
                **state,
                "director_analysis": SAMPLE_DIRECTOR_ANALYSIS,
                "scenes":            [{"scene_number": 1, "title": "Scene 1",
                                       "location_query": "coffee shop"}],
            }
        return _mock

    def _make_mock_location(self) -> AsyncMock:
        async def _mock(state: AgentState) -> AgentState:
            return {
                **state,
                "location_results": [{"scene_number": 1, "places": []}],
                "weather_reports":  [{"scene_number": 1, "weather": None}],
            }
        return _mock

    def _make_mock_scheduler(self) -> AsyncMock:
        async def _mock(state: AgentState) -> AgentState:
            return {**state, "schedule": SAMPLE_SCHEDULE}
        return _mock

    def _make_mock_budget(self) -> AsyncMock:
        async def _mock(state: AgentState) -> AgentState:
            return {**state, "budget_estimate": SAMPLE_BUDGET}
        return _mock

    def _make_mock_risk(self) -> AsyncMock:
        async def _mock(state: AgentState) -> AgentState:
            return {**state, "risk_report": SAMPLE_RISK}
        return _mock

    @pytest.mark.asyncio
    async def test_happy_path_returns_complete_plan(self):
        with (
            patch("app.graph.nodes.director_node",   self._make_mock_director()),
            patch("app.graph.nodes.location_node",   self._make_mock_location()),
            patch("app.graph.nodes.scheduler_node",  self._make_mock_scheduler()),
            patch("app.graph.nodes.budget_node",     self._make_mock_budget()),
            patch("app.graph.nodes.risk_node",       self._make_mock_risk()),
        ):
            graph = build_graph()

        runner = WorkflowRunner(graph=graph)
        plan = await runner.run(
            project_id="proj-happy",
            screenplay="FADE IN:\nINT. ROOM - DAY\nFADE OUT.",
        )

        assert plan["status"] in ("complete", "partial")
        assert plan["project_id"] == "proj-happy"
        assert "run_metadata" in plan
        assert "elapsed_secs" in plan["run_metadata"]

    @pytest.mark.asyncio
    async def test_error_in_director_still_returns_production_plan(self):
        """
        Even when director sets an error, assemble_output_node must still run
        and ``production_plan`` must be present in the result.
        """
        async def _failing_director(state: AgentState) -> AgentState:
            return {**state, "error": "Gemini API rate-limited"}

        with (
            patch("app.graph.nodes.director_node",  _failing_director),
            patch("app.graph.nodes.location_node",  self._make_mock_location()),
            patch("app.graph.nodes.scheduler_node", self._make_mock_scheduler()),
            patch("app.graph.nodes.budget_node",    self._make_mock_budget()),
            patch("app.graph.nodes.risk_node",      self._make_mock_risk()),
        ):
            graph = build_graph()

        runner = WorkflowRunner(graph=graph)
        plan = await runner.run(
            project_id="proj-error",
            screenplay="FADE IN:",
        )

        assert plan["status"] == "failed"
        assert "Gemini API rate-limited" in plan["error"]

    @pytest.mark.asyncio
    async def test_run_metadata_contains_project_id(self):
        with (
            patch("app.graph.nodes.director_node",  self._make_mock_director()),
            patch("app.graph.nodes.location_node",  self._make_mock_location()),
            patch("app.graph.nodes.scheduler_node", self._make_mock_scheduler()),
            patch("app.graph.nodes.budget_node",    self._make_mock_budget()),
            patch("app.graph.nodes.risk_node",      self._make_mock_risk()),
        ):
            graph = build_graph()

        runner = WorkflowRunner(graph=graph)
        plan = await runner.run(project_id="proj-meta", screenplay="FADE IN:")
        assert plan["run_metadata"]["project_id"] == "proj-meta"


# ---------------------------------------------------------------------------
# WorkflowRunner
# ---------------------------------------------------------------------------

class TestWorkflowRunner:

    @pytest.mark.asyncio
    async def test_runner_raises_agent_execution_error_on_graph_exception(self):
        """``WorkflowRunner.run()`` wraps LangGraph exceptions in AgentExecutionError."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = RuntimeError("LangGraph internal error")

        runner = WorkflowRunner(graph=mock_graph)
        with pytest.raises(AgentExecutionError, match="Pipeline execution failed"):
            await runner.run(project_id="proj-fail", screenplay="FADE IN:")

    @pytest.mark.asyncio
    async def test_runner_stamps_run_metadata_before_invoke(self):
        """Initial state passed to ainvoke must contain run_metadata."""
        captured_state = {}

        async def _capture(state):
            captured_state.update(state)
            return {"production_plan": {}, **state}

        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = _capture

        runner = WorkflowRunner(graph=mock_graph)
        await runner.run(project_id="proj-stamp", screenplay="FADE IN:")

        assert "run_metadata" in captured_state
        assert captured_state["run_metadata"]["project_id"] == "proj-stamp"
        assert "started_at" in captured_state["run_metadata"]

    @pytest.mark.asyncio
    async def test_runner_returns_production_plan_from_final_state(self):
        expected_plan = {"status": "complete", "title": "My Film"}
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "production_plan": expected_plan,
            "project_id": "proj-return",
        }

        runner = WorkflowRunner(graph=mock_graph)
        plan = await runner.run(project_id="proj-return", screenplay="FADE IN:")

        assert plan["status"] == "complete"
        assert plan["title"] == "My Film"
