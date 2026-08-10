#Allows users to use async and await.
#It allows your program to handle multiple tasks at once without freezing
import asyncio

#os stands for operating system, it allows Python to interact with your operation system
import os

# This is used for "type hinting", it helos code editors catch errors before the code runs.
# Any allows you to explicitly state that a specific varaible, function argument, or return value can be of any data type
from typing import Any

#This imports a specific function from the python-dotenv package.
#When you call load_dotenv(), it looks ofr a .env file in the project and securely loads those values into your system's environent variables.
from dotenv import load_dotenv
from parallel import Parallel

from backend.app.agents.director_agent import Scene
from backend.app.schemas.location import LocationRequirements

load_dotenv()

# Building the search objectives
def build_search_objective(
        scene: Scene,
        requiremetns: LocationRequirements
) -> str:

    