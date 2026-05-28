"""Pydantic schemas for API request/response validation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    assistant: str = Field(..., pattern="^(oss|frontier)$", description="'oss' or 'frontier'")
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default="default")


class ChatResponse(BaseModel):
    response: str
    latency_ms: float
    model: str
    safe: bool
    flagged_reason: Optional[str] = ""
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0


class EvalRequest(BaseModel):
    assistants: List[str] = Field(
        default=["frontier"],
        description="List of assistants to evaluate: 'oss', 'frontier', or both",
    )
    categories: List[str] = Field(
        default=["hallucination", "jailbreak", "bias"],
        description="Evaluation categories to run",
    )


class EvalResponse(BaseModel):
    results: Dict[str, Any]
    message: str


class HealthResponse(BaseModel):
    status: str
    api_key_set: bool
    version: str
