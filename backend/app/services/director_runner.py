# Test screenplay → Runner → Director Agent → Structured JSON

# Main purpose of the code here:
# Take raw screenplay text, pass it to an AI agent,
# and return structured analysis.

# uuid4 is used to generate a unique identifier for each screenplay analysis.
from uuid import uuid4

from google.adk.runners import Runner

"""
The Runner is the execution engine.
It handles the event loop and orchestrates interactions between
the user, agent, tools, and session storage.
"""

from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# Use this import if the backend is started from inside the backend directory.
from app.agents.director_agent import (
    ScriptRubric,
    director_agent,
)


# APP_NAME is the identifier used by the session service
# to group session data belonging to this application.
APP_NAME = "cinepilot"

# This must match output_key="extracted_data" in director_agent.py.
OUTPUT_KEY = "extracted_data"


async def run_director_runner(
    # screenplay_text and user_id are function parameters.
    # Their values can be different each time this function is called.
    screenplay_text: str,

    # The function expects user_id to be a string.
    # If a user ID is not provided, we use "test_user".
    user_id: str = "test_user",
) -> ScriptRubric:
    # The arrow specifies the expected return type.

    # Remove unnecessary spaces and line breaks
    # from the beginning and end.
    screenplay_text = screenplay_text.strip()

    # Check whether the screenplay text is empty.
    if not screenplay_text:
        # raise is Python's keyword for intentionally triggering an exception.
        raise ValueError("Screenplay text is empty.")

    # Each execution needs its own identity.
    # Different IDs prevent separate runs from being mixed together.
    # session_id is the identifier for one single run of this function.
    session_id = str(uuid4())

    # Think of it as temporary storage and management for session data.
    # The data is stored in the backend server's memory.
    session_service = InMemorySessionService()

    # await means:
    # Pause this function until an asynchronous operation finishes,
    # and then continue.
    await session_service.create_session(
        # Creating the session may require asynchronous work.
        # await lets Python handle other work while this function is waiting.
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    # Create a Runner object and store it in runner.
    # This is the setup or configuration phase.
    runner = Runner(
        # agent=director_agent tells the Runner which agent to execute.
        agent=director_agent,  # Brain: which agent should be executed
        app_name=APP_NAME,  # Context: which application owns this run
        session_service=session_service,  # Storage: where session data is managed
    )

    # Convert the screenplay text into the structured
    # conversation format expected by ADK and Gemini.
    user_message = Content(
        # This tells the agent that the message comes from the user.
        role="user",

        # One message can contain multiple parts,
        # so parts is a Python list.
        parts=[
            Part(
                text=(
                    "Analyze the screenplay below scene by scene.\n\n"
                    "SCREENPLAY:\n"
                    f"{screenplay_text}"
                )
            )
        ],
    )

    try:
        # runner.run_async() actually executes the Director Agent.
        # The agent may generate several events while it is running.
        async for event in runner.run_async(
            user_id=user_id,  # Identifies who is sending the message
            session_id=session_id,  # Identifies this particular session
            new_message=user_message,  # The message containing the screenplay
        ):
            # Check whether this event contains the final agent response.
            if event.is_final_response():
                # We do not need to extract event.content here because
                # the structured result is saved in the session state.
                pass

        # We do not get the answer from event.content because we want
        # the structured output stored under the agent's output_key.

        # await pauses this specific function until the session
        # has been fully retrieved.
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )

        # Make sure the session was successfully found.
        if session is None:
            raise RuntimeError("Director Agent session not found.")

        # Retrieve the structured result saved by the Director Agent.
        extracted_data = session.state.get(OUTPUT_KEY)

        # Make sure the Director Agent produced structured data.
        if extracted_data is None:
            raise RuntimeError(
                "Failed to extract structured data from "
                "the Director Agent session."
            )

        # Validate the output and convert it into a ScriptRubric object.
        # If it is already a ScriptRubric object, return it directly.
        if isinstance(extracted_data, ScriptRubric):
            return extracted_data

        # Otherwise, ask Pydantic to validate and convert the data.
        return ScriptRubric.model_validate(extracted_data)

    except Exception as error:
        # Convert any execution error into a clearer Director Agent error.
        raise RuntimeError(
            f"Director Agent execution failed: {error}"
        ) from error