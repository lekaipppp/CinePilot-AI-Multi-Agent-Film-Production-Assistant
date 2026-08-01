"""
ScriptWriterAgent – LangGraph node.
Uses Gemini to draft a film script from a project brief.
"""

from app.graph.state import AgentState
from app.services.gemini_service import GeminiService

_gemini = GeminiService()

SCRIPT_WRITER_PROMPT = """
You are an experienced Hollywood screenwriter.
Based on the following project brief, write a structured film script draft.

Project Brief:
{brief}

Deliver: Title, Genre, Logline, Three-Act Outline, and key scene headings.
""".strip()


async def script_writer_node(state: AgentState) -> AgentState:
    """
    LangGraph node: generate an initial script draft.
    Reads `input_data` from state and writes `script_draft`.
    """
    brief = state.get("input_data", {}).get("brief", "No brief provided.")
    prompt = SCRIPT_WRITER_PROMPT.format(brief=brief)

    try:
        draft = await _gemini.generate(prompt)
        return {**state, "script_draft": draft}
    except Exception as exc:
        return {**state, "error": f"ScriptWriterAgent failed: {exc}"}
