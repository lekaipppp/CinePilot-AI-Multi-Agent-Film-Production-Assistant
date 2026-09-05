import json
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.app.agents.risk_agent import risk_agent
from backend.app.schemas.risk import RiskAgentOutput

from google.genai.types import Content, Part
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

logger = logging.getLogger(__name__)

APP_NAME = "cinepilot"
OUTPUT_KEY = "risk_data"


def _apply_deterministic_ids(result: RiskAgentOutput) -> RiskAgentOutput:
    """
    Assign each risk a deterministic id, rather than trusting the model
    to invent unique ones — the same "don't trust model bookkeeping"
    treatment already applied to totals in scheduler_runner.py and
    budget_runner.py.
    """

    for index, item in enumerate(result.risks):
        item.id = f"risk-{index + 1}"

    return result


async def risk_runner(
    scenes: List[Dict[str, Any]],
    selected_locations: List[Dict[str, Any]],
    schedule: Optional[Dict[str, Any]],
    budget: Optional[Dict[str, Any]],
    user_id: str = "test_user",
) -> RiskAgentOutput:

    if not scenes:
        raise ValueError("No scenes were supplied to the Risk Agent.")

    session_service = InMemorySessionService()
    risk_session_id = str(uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=risk_session_id,
    )

    runner = Runner(
        agent=risk_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    input_data = {
        "scenes": scenes,
        "selected_locations": selected_locations,
        "schedule": schedule,
        "budget": budget,
    }

    formatted_input = json.dumps(
        input_data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    risk_message = Content(
        role="user",
        parts=[
            Part(
                text=(
                    "Identify production risks from the data below "
                    "across the five fixed categories: Weather, "
                    "Permits, Budget, Scheduling, Safety.\n\n"
                    "Only produce Budget risks when a budget is "
                    "supplied, and only produce Scheduling risks when a "
                    "schedule is supplied. Ground every risk in "
                    "evidence actually present in the input — never "
                    "invent a forecast, permit status, cost, or "
                    "conflict.\n\n"
                    "INPUT DATA:\n"
                    f"{formatted_input}"
                )
            )
        ],
    )

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=risk_session_id,
            new_message=risk_message,
        ):
            if event.is_final_response():
                pass

        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=risk_session_id,
        )

        if session is None:
            raise RuntimeError("Risk Agent session not found.")

        risk_data = session.state.get(OUTPUT_KEY)

        if risk_data is None:
            raise RuntimeError(
                "Risk Agent did not produce structured output."
            )

        if isinstance(risk_data, RiskAgentOutput):
            result = risk_data
        elif isinstance(risk_data, str):
            result = RiskAgentOutput.model_validate_json(risk_data)
        else:
            result = RiskAgentOutput.model_validate(risk_data)

        return _apply_deterministic_ids(result)

    except Exception as error:
        raise RuntimeError(
            f"Risk Agent execution failed: {error}"
        ) from error
