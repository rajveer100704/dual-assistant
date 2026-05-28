"""
Observability layer — structured logging and metrics collection.
Writes JSON-newline logs to logs/app.log for downstream analysis.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

# ─── Setup ────────────────────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Structured JSON logger
_json_logger = logging.getLogger("observability.json")
_json_logger.setLevel(logging.INFO)

if not _json_logger.handlers:
    _fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(message)s"))
    _json_logger.addHandler(_fh)
    _json_logger.propagate = False

# Human-readable console logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# ─── In-memory metrics store ─────────────────────────────────────────────────

class MetricsStore:
    """Thread-safe in-memory metrics accumulator."""

    def __init__(self):
        self._records: list[Dict] = []

    def record(self, entry: Dict) -> None:
        self._records.append(entry)

    def get_all(self) -> list[Dict]:
        return list(self._records)

    def get_summary(self) -> Dict[str, Any]:
        if not self._records:
            return {}

        oss = [r for r in self._records if r.get("assistant") == "oss"]
        frontier = [r for r in self._records if r.get("assistant") == "frontier"]

        def avg(lst, key):
            vals = [r[key] for r in lst if key in r and r[key] is not None]
            return round(sum(vals) / len(vals), 2) if vals else None

        return {
            "total_requests": len(self._records),
            "oss": {
                "requests": len(oss),
                "avg_latency_ms": avg(oss, "latency_ms"),
                "safety_flags": sum(1 for r in oss if not r.get("safe", True)),
            },
            "frontier": {
                "requests": len(frontier),
                "avg_latency_ms": avg(frontier, "latency_ms"),
                "safety_flags": sum(1 for r in frontier if not r.get("safe", True)),
                "total_input_tokens": sum(r.get("input_tokens", 0) for r in frontier),
                "total_output_tokens": sum(r.get("output_tokens", 0) for r in frontier),
            },
        }

    def clear(self) -> None:
        self._records.clear()


# Singleton metrics store
metrics = MetricsStore()


# ─── Logging helpers ──────────────────────────────────────────────────────────

def log_request(
    assistant: str,
    prompt: str,
    response: str,
    latency_ms: float,
    model: str,
    safe: bool = True,
    flagged_reason: str = "",
    input_tokens: int = 0,
    output_tokens: int = 0,
    prompt_type: str = "general",
) -> None:
    """Write a structured log entry and update in-memory metrics."""
    entry = {
        "ts": time.time(),
        "timestamp": time.time(),       # alias — both keys present for compatibility
        "assistant": assistant,
        "model": model,
        "prompt_type": prompt_type,
        "prompt_len": len(prompt),
        "response_len": len(response),
        "latency_ms": latency_ms,
        "safe": safe,
        "flagged_reason": flagged_reason,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    _json_logger.info(json.dumps(entry))
    metrics.record(entry)


def log_eval_result(
    assistant: str,
    category: str,
    prompt: str,
    response: str,
    scores: Dict[str, Any],
) -> None:
    """Log an evaluation result."""
    entry = {
        "ts": time.time(),
        "type": "eval",
        "assistant": assistant,
        "category": category,
        "prompt_len": len(prompt),
        "response_len": len(response),
        "scores": scores,
    }
    _json_logger.info(json.dumps(entry))
