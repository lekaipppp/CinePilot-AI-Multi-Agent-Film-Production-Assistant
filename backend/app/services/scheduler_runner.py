import json
from typing import Any, Dict, List
from uuid import uuid4

from backend.app.agents.scheduler_agent import scheduler_agent
from backend.app.schemas.scheduler import SchedulerAgentOutput

from google.genai.types import Content, Part
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

APP_NAME = "cinepilot"
OUTPUT_KEY = "schedule_data"


async def scheduler_runner(
    scenes: List[Dict[str, Any]],
    constraints: Dict[str, Any],
    user_id: str = "test_user",
) -> SchedulerAgentOutput:

    if not scenes:
        raise ValueError("No scenes were supplied to the Scheduler Agent.")

    if not constraints:
        raise ValueError("Scheduling constraints are required.")

    session_service = InMemorySessionService()
    scheduler_session_id = str(uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=scheduler_session_id,
    )

    runner = Runner(
        agent=scheduler_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    input_data = {
        "scenes": scenes,
        "constraints": constraints,
    }

    formatted_input = json.dumps(
        input_data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    scheduler_message = Content(
        role="user",
        parts=[
            Part(
                text=(
                    "Build a day-by-day shoot schedule for every scene "
                    "below, minimizing company moves and night-shoot "
                    "turnaround problems, and flag every conflict you "
                    "can support with evidence.\n\n"
                    "Only use information present in the scenes and the "
                    "user's constraints. Do not invent locations, cast "
                    "availability, or call times beyond the stated "
                    "defaults.\n\n"
                    "INPUT DATA:\n"
                    f"{formatted_input}"
                )
            )
        ],
    )

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=scheduler_session_id,
            new_message=scheduler_message,
        ):
            if event.is_final_response():
                pass

        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=scheduler_session_id,
        )

        if session is None:
            raise RuntimeError("Scheduler Agent session not found.")

        schedule_data = session.state.get(OUTPUT_KEY)

        if schedule_data is None:
            raise RuntimeError(
                "Scheduler Agent did not produce structured output."
            )

        if isinstance(schedule_data, SchedulerAgentOutput):
            return schedule_data

        if isinstance(schedule_data, str):
            return SchedulerAgentOutput.model_validate_json(schedule_data)

        return SchedulerAgentOutput.model_validate(schedule_data)

    except Exception as error:
        raise RuntimeError(
            f"Scheduler Agent execution failed: {error}"
        ) from error
