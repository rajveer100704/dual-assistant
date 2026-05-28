"""
OSS Assistant — Qwen2.5-0.5B-Instruct via HuggingFace Transformers.
Runs fully on CPU; no GPU required.
"""

import logging
import time
from typing import Optional

from .memory import ConversationMemory
from .guardrails import screen_prompt, screen_output

logger = logging.getLogger(__name__)

_pipe = None  # lazy-loaded singleton
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


def _load_pipeline():
    """Lazy-load the Qwen pipeline once at first use."""
    global _pipe
    if _pipe is not None:
        return _pipe

    logger.info("Loading OSS model: %s (this may take ~30s on first run)", MODEL_NAME)
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        import torch

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,   # float32 for CPU compat
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )

        _pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
            repetition_penalty=1.1,
            return_full_text=False,      # only return new tokens
        )
        logger.info("OSS model loaded successfully")
    except Exception as exc:
        logger.error("Failed to load OSS model: %s", exc)
        _pipe = None
        raise

    return _pipe


def _get_cached_pipeline():
    """
    Streamlit-aware wrapper around _load_pipeline.
    When running inside a Streamlit app (HF Spaces or local UI),
    uses @st.cache_resource so the ~1.2GB model is loaded once and
    shared across all reruns — preventing OOM and cold-start reloads.
    Falls back to the plain module-level singleton in FastAPI/test contexts.
    """
    try:
        import streamlit as st
        # Only use cache_resource if Streamlit runtime is active
        if hasattr(st, "cache_resource"):
            @st.cache_resource(show_spinner="Loading Qwen2.5-0.5B (first run ~30s)...")
            def _st_cached():
                return _load_pipeline()
            return _st_cached()
    except Exception:
        pass
    # Fallback: plain singleton
    return _load_pipeline()



class OSSAssistant:
    """
    Personal assistant backed by Qwen2.5-0.5B-Instruct.

    Attributes
    ----------
    memory : ConversationMemory
        Sliding-window conversation history.
    model_name : str
        HuggingFace model identifier.
    """

    SYSTEM_PROMPT = (
        "You are a helpful, harmless, and honest AI assistant. "
        "Answer questions clearly and concisely. "
        "If you don't know something, say so rather than making up an answer."
    )

    def __init__(self, memory: Optional[ConversationMemory] = None) -> None:
        self.memory = memory or ConversationMemory(window_size=5)
        self.model_name = MODEL_NAME
        self._model_loaded = False

    def _build_prompt(self, user_input: str) -> str:
        """Construct chat-formatted prompt with history."""
        history = self.memory.get_context()

        if history:
            prompt = (
                f"{self.SYSTEM_PROMPT}\n\n"
                f"Conversation so far:\n{history}\n\n"
                f"User: {user_input}\nAssistant:"
            )
        else:
            prompt = (
                f"{self.SYSTEM_PROMPT}\n\n"
                f"User: {user_input}\nAssistant:"
            )
        return prompt

    def chat(self, user_input: str) -> dict:
        """
        Process a user message and return a response dict.

        Returns
        -------
        dict with keys: response, latency_ms, model, safe, flagged_reason
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
            }

        try:
            pipe = _get_cached_pipeline()
            self._model_loaded = True
        except Exception as exc:
            return {
                "response": f"Model loading error: {exc}. Please check your environment.",
                "latency_ms": round((time.time() - start) * 1000, 1),
                "model": self.model_name,
                "safe": True,
                "flagged_reason": "model_error",
            }

        prompt = self._build_prompt(user_input)

        try:
            result = pipe(prompt)
            raw_text = result[0]["generated_text"].strip()
        except Exception as exc:
            logger.error("Inference error: %s", exc)
            return {
                "response": "I encountered an error generating a response. Please try again.",
                "latency_ms": round((time.time() - start) * 1000, 1),
                "model": self.model_name,
                "safe": True,
                "flagged_reason": "inference_error",
            }

        # Output safety check
        output_safe, final_response = screen_output(raw_text)
        flagged = "" if output_safe else "output_filtered"

        # Save to memory only if we have a real response
        self.memory.save(user_input, final_response)

        return {
            "response": final_response,
            "latency_ms": round((time.time() - start) * 1000, 1),
            "model": self.model_name,
            "safe": output_safe,
            "flagged_reason": flagged,
        }

    def reset(self) -> None:
        """Clear conversation memory."""
        self.memory.reset()
