import json
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.app.agents.report_agent import report_agent
from backend.app.schemas.report import ReportAgentOutput

from google.genai.types import Content, Part
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

logger = logging.getLogger(__name__)

APP_NAME = "cinepilot"
OUTPUT_KEY = "report_data"


async def report_runner(
    scenes: List[Dict[str, Any]],
    selected_locations: List[Dict[str, Any]],
    schedule: Optional[Dict[str, Any]],
    budget: Optional[Dict[str, Any]],
    risk: Optional[Dict[str, Any]],
    user_id: str = "test_user",
) -> ReportAgentOutput:

    if not scenes:
        raise ValueError("No scenes were supplied to the Report Agent.")

    session_service = InMemorySessionService()
    report_session_id = str(uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=report_session_id,
    )

    runner = Runner(
        agent=report_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    input_data = {
        "scenes": scenes,
        "selected_locations": selected_locations,
        "schedule": schedule,
        "budget": budget,
        "risk": risk,
    }

    formatted_input = json.dumps(
        input_data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    report_message = Content(
        role="user",
        parts=[
            Part(
                text=(
                    "Synthesize a short executive summary and a handful "
                    "of cross-cutting highlights from the production "
                    "data below. Do not restate individual fields "
                    "verbatim — connect evidence across sources where "
                    "possible, and ground every statement in data "
                    "actually present in the input.\n\n"
                    "INPUT DATA:\n"
                    f"{formatted_input}"
                )
            )
        ],
    )

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=report_session_id,
            new_message=report_message,
        ):
            if event.is_final_response():
                pass

        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=report_session_id,
        )

        if session is None:
            raise RuntimeError("Report Agent session not found.")

        report_data = session.state.get(OUTPUT_KEY)

        if report_data is None:
            raise RuntimeError(
                "Report Agent did not produce structured output."
            )

        if isinstance(report_data, ReportAgentOutput):
            result = report_data
        elif isinstance(report_data, str):
            result = ReportAgentOutput.model_validate_json(report_data)
        else:
            result = ReportAgentOutput.model_validate(report_data)

        return result

    except Exception as error:
        raise RuntimeError(
            f"Report Agent execution failed: {error}"
        ) from error
