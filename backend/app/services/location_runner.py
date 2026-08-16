import json
from typing import Any, Dict, List
from uuid import uuid4
from backend.app.agents.location_agent import location_agent, LocationAgentOutput

from google.genai.types import Content, Part
#Used to create a Runner object
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

APP_NAME = "cinepilot"
OUTPUT_KEY = "location_data"

async def location_runner(
        
    director_analysis: Dict[str, Any],
    user_requirements: Dict[str, Any],
    parallel_results: List[Dict[str, Any]],
    user_id: str = "test_user",
) -> LocationAgentOutput:

    if not parallel_results:
        raise ValueError("Parallel Search returned no results.")

    if not user_requirements:
        raise ValueError("User requirement is required. ")

#if we want to caculate the match_score, we need to have the infromation related to the scenen, and the user requirement

    session_service = InMemorySessionService()
    location_session_id = str(uuid4())

    #create a session service

    await session_service.create_session(
        app_name=APP_NAME,
        user_id= user_id,
        session_id=location_session_id,
    )

    runner = Runner(
        agent=location_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    #we need to combine all information needed for evaludation
    input_data = {
        "scene":director_analysis,
        "user_requirement":user_requirements,
        "parallel_search_results":parallel_results,
    }

    formatted_input = json.dumps(
        input_data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    location_message = Content(
        # This tells the agent that the message comes from the user.
        role="user",

        # One message can contain multiple parts,
        # so parts is a Python list.
        parts=[
            Part(
                text=(
                    "Evaluate and rank the real location candidates for every "
                    "scene using the structured data below.\n\n"
                    "Use the Director Agent's scene requirements and the user's "
                    "production constraints when calculating the match scores.\n\n"
                    "Only use facts contained in the Parallel Search results. "
                    "Do not invent locations, prices, availability, coordinates, "
                    "images, amenities, or source URLs.\n\n"
                    "INPUT DATA:\n"
                    f"{formatted_input}"
                )
            )
        ],
    )

    #starts to run the agent

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=location_session_id,
            new_message = location_message,  #location_messaage should be a Python string.
        ):
            if event.is_final_response():
                pass

        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=location_session_id,
        )

        if session is None:
            raise RuntimeError("Location Agent session not found.")

        location_data = session.state.get(OUTPUT_KEY)

        if location_data is None:
            raise RuntimeError(
                "Location Agent did not produce structured output."
            )

        if isinstance(location_data, LocationAgentOutput):
            return location_data

        if isinstance(location_data, str):
            return LocationAgentOutput.model_validate_json(location_data)

        return LocationAgentOutput.model_validate(location_data)

    except Exception as error:
        raise RuntimeError(
            f"Location Agent execution failed: {error}"
        ) from error         