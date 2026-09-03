import json
import logging
from typing import Any, Dict, List
from uuid import uuid4

from backend.app.agents.scheduler_agent import scheduler_agent
from backend.app.schemas.scheduler import ScheduleBlock, SchedulerAgentOutput

from google.genai.types import Content, Part
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

logger = logging.getLogger(__name__)

APP_NAME = "cinepilot"
OUTPUT_KEY = "schedule_data"


def _shooting_requirements_by_scene(
    scenes: List[Dict[str, Any]],
) -> Dict[int, List[str]]:
    """
    Map scene_number to shooting_requirements from the original Director
    Agent scenes, so the night-scene check below doesn't depend on the
    Scheduler Agent having echoed anything back correctly.
    """

    lookup: Dict[int, List[str]] = {}

    for scene in scenes:
        scene_number = scene.get("scene_number")

        if scene_number is None:
            continue

        lookup[scene_number] = scene.get("shooting_requirements") or []

    return lookup


def _is_night_block(
    block: ScheduleBlock,
    shooting_requirements_by_scene: Dict[int, List[str]],
) -> bool:
    """
    Mirrors the Scheduler Agent instruction's rule 9 definition of a
    night scene, computed deterministically instead of trusted from the
    model's own summary counts.
    """

    if block.time_of_day and "night" in block.time_of_day.lower():
        return True

    requirements = shooting_requirements_by_scene.get(
        block.scene_number, []
    )

    return any(
        "night shoot" in requirement.lower()
        for requirement in requirements
    )


def _apply_deterministic_summary(
    result: SchedulerAgentOutput,
    scenes: List[Dict[str, Any]],
) -> SchedulerAgentOutput:
    """
    Recompute total_shoot_days and night_block_count from the actual
    schedule rather than trusting the Scheduler Agent's own arithmetic,
    logging whenever the model's numbers didn't match.
    """

    recomputed_total_shoot_days = max(
        (block.shoot_day for block in result.schedule),
        default=0,
    )

    if recomputed_total_shoot_days != result.total_shoot_days:
        logger.warning(
            "Scheduler Agent total_shoot_days mismatch: model returned "
            "%s, recomputed %s from the schedule.",
            result.total_shoot_days,
            recomputed_total_shoot_days,
        )

        result.total_shoot_days = recomputed_total_shoot_days

    shooting_requirements_by_scene = _shooting_requirements_by_scene(
        scenes
    )

    night_shoot_days = {
        block.shoot_day
        for block in result.schedule
        if _is_night_block(block, shooting_requirements_by_scene)
    }

    recomputed_night_block_count = len(night_shoot_days)

    if recomputed_night_block_count != result.night_block_count:
        logger.warning(
            "Scheduler Agent night_block_count mismatch: model returned "
            "%s, recomputed %s from the schedule.",
            result.night_block_count,
            recomputed_night_block_count,
        )

        result.night_block_count = recomputed_night_block_count

    return result


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
            result = schedule_data
        elif isinstance(schedule_data, str):
            result = SchedulerAgentOutput.model_validate_json(
                schedule_data
            )
        else:
            result = SchedulerAgentOutput.model_validate(schedule_data)

        return _apply_deterministic_summary(result, scenes)

    except Exception as error:
        raise RuntimeError(
            f"Scheduler Agent execution failed: {error}"
        ) from error
