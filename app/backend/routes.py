"""
FastAPI route definitions.
Endpoints: POST /chat, POST /evaluate, GET /health
"""

import logging
import os
from typing import Dict

from fastapi import APIRouter, HTTPException

from ..assistants.frontier_assistant import FrontierAssistant
from ..assistants.memory import ConversationMemory
from ..assistants.oss_assistant import OSSAssistant
from ..assistants.tools import route_tools
from ..observability.tracing import log_request, metrics
from .schemas import ChatRequest, ChatResponse, EvalRequest, EvalResponse, HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── Session-scoped assistant instances ──────────────────────────────────────
# In production these would be keyed by user session; here we keep one per type.

_sessions: Dict[str, Dict] = {}


def _get_or_create_session(session_id: str) -> Dict:
    if session_id not in _sessions:
        _sessions[session_id] = {
            "oss": OSSAssistant(memory=ConversationMemory(window_size=5)),
            "frontier": FrontierAssistant(memory=ConversationMemory(window_size=5)),
        }
    return _sessions[session_id]


# ─── Health ───────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        api_key_set=bool(os.getenv("GEMINI_API_KEY")),
        version="1.0.0",
    )


# ─── Chat ─────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session = _get_or_create_session(request.session_id)
    assistant_key = request.assistant
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    # Check tools first (no model call needed)
    tool_result = route_tools(user_message)
    if tool_result:
        log_request(
            assistant=assistant_key,
            prompt=user_message,
            response=tool_result,
            latency_ms=0,
            model="tool",
            prompt_type="tool",
        )
        return ChatResponse(
            response=tool_result,
            latency_ms=0,
            model="tool",
            safe=True,
            flagged_reason="",
        )

    assistant = session[assistant_key]
    result = assistant.chat(user_message)

    log_request(
        assistant=assistant_key,
        prompt=user_message,
        response=result["response"],
        latency_ms=result["latency_ms"],
        model=result["model"],
        safe=result["safe"],
        flagged_reason=result.get("flagged_reason", ""),
        input_tokens=result.get("input_tokens", 0),
        output_tokens=result.get("output_tokens", 0),
    )

    return ChatResponse(**{
        "response": result["response"],
        "latency_ms": result["latency_ms"],
        "model": result["model"],
        "safe": result["safe"],
        "flagged_reason": result.get("flagged_reason", ""),
        "input_tokens": result.get("input_tokens", 0),
        "output_tokens": result.get("output_tokens", 0),
    })


# ─── Evaluate ─────────────────────────────────────────────────────────────────

@router.post("/evaluate", response_model=EvalResponse)
def run_evaluation(request: EvalRequest):
    """
    Run evaluation suite for specified assistants and categories.
    Note: OSS eval requires local model to be loaded (slow on first run).
    """
    from ..evals.hallucination_eval import run_hallucination_eval
    from ..evals.jailbreak_eval import run_jailbreak_eval
    from ..evals.bias_eval import run_bias_eval

    results = {}
    session = _get_or_create_session("eval_session")

    for assistant_key in request.assistants:
        assistant = session[assistant_key]
        results[assistant_key] = {}

        # Simple wrapper: calls chat and returns just the text
        def make_fn(asst):
            def fn(prompt: str) -> str:
                r = asst.chat(prompt)
                return r["response"]
            return fn

        fn = make_fn(assistant)

        if "hallucination" in request.categories:
            logger.info("Running hallucination eval for %s", assistant_key)
            results[assistant_key]["hallucination"] = run_hallucination_eval(
                fn, assistant_key
            )

        if "jailbreak" in request.categories:
            logger.info("Running jailbreak eval for %s", assistant_key)
            results[assistant_key]["jailbreak"] = run_jailbreak_eval(fn, assistant_key)

        if "bias" in request.categories:
            logger.info("Running bias eval for %s", assistant_key)
            results[assistant_key]["bias"] = run_bias_eval(fn, assistant_key)

    return EvalResponse(
        results=results,
        message="Evaluation complete. Run chart generation separately.",
    )


# ─── Metrics ─────────────────────────────────────────────────────────────────

@router.get("/metrics")
def get_metrics():
    return metrics.get_summary()


# ─── Reset session ────────────────────────────────────────────────────────────

@router.post("/reset/{session_id}")
def reset_session(session_id: str):
    if session_id in _sessions:
        for asst in _sessions[session_id].values():
            asst.reset()
        return {"message": f"Session '{session_id}' reset successfully"}
    return {"message": f"Session '{session_id}' not found"}
