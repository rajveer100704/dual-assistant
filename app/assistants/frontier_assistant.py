"""
Frontier Assistant — Gemini 2.5 Flash via Google GenAI SDK.

Free tier: https://aistudio.google.com/app/apikey
No credit card required. Generous rate limits.

Model: gemini-2.5-flash  — fast, capable, free tier available.
SDK:   google-genai       — official Google GenAI Python SDK (v1+)
"""

import logging
import os
import time
from typing import Optional

from .memory import ConversationMemory
from .guardrails import screen_prompt, screen_output

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"


class FrontierAssistant:
    """
    Personal assistant backed by Gemini 2.5 Flash (Google GenAI).

    Attributes
    ----------
    memory : ConversationMemory
        Sliding-window conversation history.
    model_name : str
        Google GenAI model identifier.
    """

    SYSTEM_PROMPT = (
        "You are a helpful, harmless, and honest AI assistant. "
        "Provide clear, accurate, and concise responses. "
        "If you are unsure about something, acknowledge uncertainty rather than "
        "fabricating information. Be conversational and warm."
    )

    def __init__(
        self,
        memory: Optional[ConversationMemory] = None,
        model: str = MODEL_NAME,
    ) -> None:
        self.memory = memory or ConversationMemory(window_size=5)
        self.model_name = model
        self._client = None

    def _get_client(self):
        """Lazy-init Gemini client."""
        if self._client is not None:
            return self._client

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY environment variable is not set. "
                "Get a free key at: https://aistudio.google.com/app/apikey  "
                "Then add it to your .env file: GEMINI_API_KEY=AIza..."
            )

        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
        except ImportError:
            raise ImportError(
                "google-genai package not found. Run: pip install google-genai"
            )

        return self._client

    def _build_prompt(self, user_input: str) -> str:
        """Build a single prompt string with system context + history + user turn."""
        history = self.memory.get_context()
        parts = [self.SYSTEM_PROMPT, ""]
        if history:
            parts += ["Conversation so far:", history, ""]
        parts += [f"User: {user_input}", "Assistant:"]
        return "\n".join(parts)

    def chat(self, user_input: str) -> dict:
        """
        Process a user message and return a response dict.

        Returns
        -------
        dict with keys: response, latency_ms, model, safe, flagged_reason,
                        input_tokens, output_tokens
        """
        start = time.time()

        # Input safety screening
        from .hybrid_moderation import hybrid_screen
        is_safe, refusal, safety_meta = hybrid_screen(user_input)
        if not is_safe:
            return {
                "response": refusal,
                "latency_ms": round((time.time() - start) * 1000, 1),
                "model": self.model_name,
                "safe": False,
                "flagged_reason": safety_meta.get("blocked_by", "input_blocked"),
                "input_tokens": 0,
                "output_tokens": 0,
            }

        try:
            client = self._get_client()
        except (EnvironmentError, ImportError) as exc:
            return {
                "response": str(exc),
                "latency_ms": round((time.time() - start) * 1000, 1),
                "model": self.model_name,
                "safe": True,
                "flagged_reason": "config_error",
                "input_tokens": 0,
                "output_tokens": 0,
            }

        prompt = self._build_prompt(user_input)

        try:
            from google import genai as _genai
            from google.genai import types as _types

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=_types.GenerateContentConfig(
                    system_instruction=self.SYSTEM_PROMPT,
                    temperature=0.7,
                    max_output_tokens=1024,
                ),
            )
            raw_text = response.text.strip()

            # Token usage (Gemini returns usage_metadata)
            usage = getattr(response, "usage_metadata", None)
            input_tokens  = getattr(usage, "prompt_token_count",     0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0

        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            return {
                "response": f"API error: {exc}",
                "latency_ms": round((time.time() - start) * 1000, 1),
                "model": self.model_name,
                "safe": True,
                "flagged_reason": "api_error",
                "input_tokens": 0,
                "output_tokens": 0,
            }

        # Output safety check
        output_safe, final_response = screen_output(raw_text)
        flagged = "" if output_safe else "output_filtered"

        self.memory.save(user_input, final_response)

        return {
            "response": final_response,
            "latency_ms": round((time.time() - start) * 1000, 1),
            "model": self.model_name,
            "safe": output_safe,
            "flagged_reason": flagged,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    def reset(self) -> None:
        """Clear conversation memory."""
        self.memory.reset()
