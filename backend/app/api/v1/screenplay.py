from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.agents.director_agent import ScriptRubric
from backend.app.services.director_runner import run_director_agent

router = APIRouter()


class ScreenplayAnalysisRequest(BaseModel):
    screenplay_text: str = Field(
        min_length=1,  #min_length means the user can not submit an empty string.
        description="The screenplay text to analyze",
    )

    user_id: str = "test_user"


@router.post("/analyze", response_model=ScriptRubric)
async def analyze_screenplay(
    request: ScreenplayAnalysisRequest, 
) -> ScriptRubric:
    try:
        return await run_director_agent(
            screenplay_text=request.screenplay_text,
            user_id=request.user_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error
    
    