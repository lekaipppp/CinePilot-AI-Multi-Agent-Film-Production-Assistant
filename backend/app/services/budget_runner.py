import json
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.app.agents.budget_agent import budget_agent
from backend.app.schemas.budget import BudgetAgentOutput

from google.genai.types import Content, Part
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

logger = logging.getLogger(__name__)

APP_NAME = "cinepilot"
OUTPUT_KEY = "budget_data"


def _apply_deterministic_total(
    result: BudgetAgentOutput,
) -> BudgetAgentOutput:
    """
    Recompute total_estimated_amount as the sum of the five line items,
    rather than trusting the Budget Agent's own arithmetic, logging
    whenever the model's number didn't match.
    """

    recomputed_total = sum(
        item.estimated_amount for item in result.line_items
    )

    if recomputed_total != result.total_estimated_amount:
        logger.warning(
            "Budget Agent total_estimated_amount mismatch: model "
            "returned %s, recomputed %s from the line items.",
            result.total_estimated_amount,
            recomputed_total,
        )

        result.total_estimated_amount = recomputed_total

    return result


async def budget_runner(
    scenes: List[Dict[str, Any]],
    selected_locations: List[Dict[str, Any]],
    total_shoot_days: Optional[int],
    constraints: Dict[str, Any],
    user_id: str = "test_user",
) -> BudgetAgentOutput:

    if not scenes:
        raise ValueError("No scenes were supplied to the Budget Agent.")

    if not constraints:
        raise ValueError("Budget constraints are required.")

    session_service = InMemorySessionService()
    budget_session_id = str(uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=budget_session_id,
    )

    runner = Runner(
        agent=budget_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    input_data = {
        "scenes": scenes,
        "selected_locations": selected_locations,
        "total_shoot_days": total_shoot_days,
        "constraints": constraints,
    }

    formatted_input = json.dumps(
        input_data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    budget_message = Content(
        role="user",
        parts=[
            Part(
                text=(
                    "Estimate a five-line-item production budget from "
                    "the data below: locations, equipment, crew, "
                    "transportation, and contingency.\n\n"
                    "Ground the locations estimate in the confirmed "
                    "location candidates' pricing when available. "
                    "Clearly mark every other figure as an estimate, "
                    "never as confirmed pricing.\n\n"
                    "INPUT DATA:\n"
                    f"{formatted_input}"
                )
            )
        ],
    )

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=budget_session_id,
            new_message=budget_message,
        ):
            if event.is_final_response():
                pass

        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=budget_session_id,
        )

        if session is None:
            raise RuntimeError("Budget Agent session not found.")

        budget_data = session.state.get(OUTPUT_KEY)

        if budget_data is None:
            raise RuntimeError(
                "Budget Agent did not produce structured output."
            )

        if isinstance(budget_data, BudgetAgentOutput):
            result = budget_data
        elif isinstance(budget_data, str):
            result = BudgetAgentOutput.model_validate_json(budget_data)
        else:
            result = BudgetAgentOutput.model_validate(budget_data)

        return _apply_deterministic_total(result)

    except Exception as error:
        raise RuntimeError(
            f"Budget Agent execution failed: {error}"
        ) from error
