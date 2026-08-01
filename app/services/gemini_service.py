"""
GeminiService – thin async wrapper around Google Generative AI (Gemini).

Lazy initialisation: the SDK client is created on first use, NOT at import
time.  If GEMINI_API_KEY is missing, each method raises a clear RuntimeError
instead of crashing at startup.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.config.settings import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _require_gemini():
    """
    Ensure the Gemini SDK is available and GEMINI_API_KEY is set.
    Import the SDK lazily so the module can be imported without the key.

    Returns
    -------
    module
        The ``google.generativeai`` module, already configured.

    Raises
    ------
    RuntimeError
        When GEMINI_API_KEY is empty — gives a clear human-readable error.
    ImportError
        When the ``google-generativeai`` package is not installed.
    """
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add GEMINI_API_KEY=<your-key> to your .env file. "
            "Get a key at https://aistudio.google.com/app/apikey"
        )

    try:
        import google.generativeai as genai  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "google-generativeai is not installed. "
            "Run: pip install google-generativeai"
        ) from exc

    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai


class GeminiService:
    """
    Provides async text generation via the Gemini API.

    The model object is created on first use — import this class freely
    without worrying about API key availability at import time.
    """

    def __init__(self) -> None:
        # Do NOT call genai here — defer to first method call
        self._model = None

    def _get_model(self):
        """Return (or lazily create) the Gemini model instance."""
        if self._model is None:
            genai = _require_gemini()
            self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
        return self._model

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Send a prompt to Gemini and return the raw text response.
        kwargs are forwarded to generate_content (temperature, max_tokens, etc.)
        """
        model = self._get_model()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: model.generate_content(prompt, **kwargs)
        )
        return response.text

    async def generate_json(self, prompt: str) -> dict:
        """
        Request a JSON response from Gemini and parse it.
        """
        json_prompt = prompt + "\n\nRespond with valid JSON only. No markdown fences."
        raw = await self.generate(json_prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        return json.loads(raw)
