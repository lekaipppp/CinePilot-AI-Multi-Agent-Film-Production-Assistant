"""
app/agents/director/service.py
==============================
``GeminiDirectorService`` — the Gemini API adapter for the Director Agent.

Lazy initialisation: the SDK model is NOT created at import time.
If GEMINI_API_KEY is missing the class can be safely imported;
each actual API call raises a clear RuntimeError at the call site.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.config.settings import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES:       int   = 3
BASE_BACKOFF_SECS: float = 1.0


def _require_gemini_model(model_name: str, system_instruction=None):
    """
    Lazily import and configure the Gemini SDK, then return a GenerativeModel.

    Raises
    ------
    RuntimeError
        When GEMINI_API_KEY is not set.
    ImportError
        When google-generativeai is not installed.
    """
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add GEMINI_API_KEY=<your-key> to your .env file. "
            "Get a key at https://aistudio.google.com/app/apikey"
        )

    try:
        import google.generativeai as genai  # type: ignore[import]
        from google.generativeai.types import GenerationConfig  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "google-generativeai is not installed. Run: pip install google-generativeai"
        ) from exc

    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction,
    )


class GeminiDirectorService:
    """
    Thin async adapter between the Director Agent and the Gemini SDK.

    Safe to instantiate without a GEMINI_API_KEY — the key is only required
    when ``analyse()`` is actually called.
    """

    def __init__(
        self,
        *,
        model_name: str | None = None,
        max_output_tokens: int = 8192,
    ) -> None:
        self._model_name       = model_name or settings.GEMINI_MODEL
        self._max_output_tokens = max_output_tokens
        # No SDK call here — deferred to first analyse() call

        if not settings.GEMINI_API_KEY:
            logger.warning(
                "GEMINI_API_KEY is not set — Director Agent calls will fail "
                "at runtime with a clear error message."
            )

    async def analyse(
        self,
        *,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> str:
        """
        Send a Director analysis request to Gemini and return the raw text.

        Raises
        ------
        RuntimeError
            When GEMINI_API_KEY is not configured.
        Exception
            Re-raises the last SDK exception after MAX_RETRIES attempts.
        """
        # Import and validate lazily at call time — not at construction time
        try:
            import google.generativeai as genai  # type: ignore[import]
            from google.generativeai.types import GenerationConfig
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is not installed. "
                "Run: pip install google-generativeai"
            ) from exc

        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Add it to your .env file to use the Director Agent."
            )

        genai.configure(api_key=settings.GEMINI_API_KEY)

        generation_config = GenerationConfig(
            temperature=temperature,
            candidate_count=1,
            max_output_tokens=self._max_output_tokens,
            response_mime_type="application/json",
        )

        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_instruction,
        )

        return await self._call_with_retry(
            model=model,
            prompt=user_prompt,
            generation_config=generation_config,
        )

    async def _call_with_retry(
        self,
        *,
        model: Any,
        prompt: str,
        generation_config: Any,
    ) -> str:
        """Invoke the Gemini SDK with exponential back-off on transient errors."""
        last_exc: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: model.generate_content(
                        prompt,
                        generation_config=generation_config,
                    ),
                )

                if not response.text:
                    raise ValueError("Gemini returned an empty response body")

                logger.debug(
                    "Gemini Director call succeeded",
                    extra={
                        "attempt":        attempt,
                        "response_chars": len(response.text),
                        "finish_reason":  str(response.candidates[0].finish_reason)
                        if response.candidates else "unknown",
                    },
                )
                return response.text

            except Exception as exc:
                last_exc = exc
                if attempt < MAX_RETRIES:
                    wait = BASE_BACKOFF_SECS * (2 ** (attempt - 1))
                    logger.warning(
                        "Gemini Director call failed — retrying",
                        extra={
                            "attempt":     attempt,
                            "max_retries": MAX_RETRIES,
                            "wait_secs":   wait,
                            "error":       str(exc),
                        },
                    )
                    await asyncio.sleep(wait)

        logger.error(
            "Gemini Director call failed after all retries",
            extra={"max_retries": MAX_RETRIES, "error": str(last_exc)},
        )
        raise last_exc  # type: ignore[misc]
