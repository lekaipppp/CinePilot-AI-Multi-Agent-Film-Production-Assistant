# Test screenplay → Runner → Director Agent → Structured JSON

# main purpose of code here, take raw screenplay text, and passes it to an AI agent, and returns structured analysis back

import json
#uuid is used to generate a unique identifier for each screenplay
from uuid import uuid4

from google.adk.runners import Runner
'''The Runner is the execution engine,
It handles the event loop and orchestration interaction between the users
the agent, tools, and session storage.'''
from google.adk.sessions import InMemorySessionService
from google.genai.types import Cotent, Part

from backend.app.agents.director_agent import (
    ScriptRubric,
    director_agent,
)

#app_bame is the identifier used by teh session service to group session data
APP_NAME = "cinepilot"
OUTPUT_KEY = "extracted_data"

async def run_director_runner(
        #the reason for using temporary placeholders is to allow they can be changed
        screenplay_text: str,
        #The function expects user_id to be a string, if user ID is not provided, then we use test_user.
        user_id: str= "test_user",
) -> ScriptRubric: 
# The arrow specifies the expected return type.
        
        #Remove redundunt spaces
        screenplay_text = screenplay_text.strip()



