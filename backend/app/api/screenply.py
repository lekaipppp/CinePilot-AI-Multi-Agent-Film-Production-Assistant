"""
API endpoint for sending screenplay text to the Director Agent.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.director_runner import run_director_runner


# Every endpoint in this file begins with "/screenplay".
router = APIRouter(
    prefix="/screenplay",
    tags=["Screenplay Analysis"],
)


class ScreenplayRequest(BaseModel):
    """
    Data that the frontend must send to this endpoint.
    """

    screenplay_text: str = Field(
        ...,
        min_length=1,
        description="The raw screenplay text to analyze.",
    )

    user_id: str = Field(
        default="test_user",
        description="Identifier of the user requesting the analysis.",
    )


@router.post("/analyze")
async def analyze_screenplay(request: ScreenplayRequest):
    """
    Send screenplay text to the Director Runner and return
    the structured Director Agent result.
    """

    try:
        # Call the Director Runner.
        result = await run_director_runner(
            screenplay_text=request.screenplay_text,
            user_id=request.user_id,
        )

        # FastAPI and Pydantic automatically convert this result into JSON.
        return result

    except ValueError as error:
        # A ValueError normally means the input is invalid or empty.
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        # This handles errors from the runner, Gemini, or session service.
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error