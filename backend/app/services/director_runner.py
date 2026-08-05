from uuid import uuid4
from backend.app.agents.director_agent import director_agent, ScriptRubric
from google.genai.types import Content, Part
#Used to create a Runner object
from google.adk.agents import Runner
from google.adk.sessions import InMemorySessionService

APP_NAME = "cinepilot"
OUTPUT_KEY = "extracted_data"


async def run_director_agent(
        screenplay_text: str,
        user_id: str= "test_user",
) -> ScriptRubric:

    screenplay_text = screenplay_text.strip()
    if not screenplay_text:
        raise ValueError("Screenplay text is empty.")
    
    session_id = uuid4()

    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name=APP_NAME,
        user_id= user_id,
        session_id=session_id,
    )

    runner = Runner(
        agent=director_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

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

#The runner.run_async atually executes the director agent
    try:
        async for event in runner.run_async(
            user_id = user_id,
            session_id = session_id,
            new_message=user_message
        ):
            if event.is_final_response():
                pass

        #we do not get the answer from the event, cuz we need the answer in a specific format

        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )

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