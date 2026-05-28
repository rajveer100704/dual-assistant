"""
Hallucination evaluation — hybrid keyword + LLM-as-judge scorer.

Methodology inspired by:
  - TruthfulQA (Lin et al. 2022)  — adversarial factual prompts
  - SimpleQA (Wei et al. 2024)    — short factual Q&A benchmark
  - HELM (Liang et al. 2022)      — holistic LLM evaluation framework

Scoring pipeline:
  1. Keyword matching (baseline, zero-cost)
  2. LLM judge (semantic, higher fidelity) — if GEMINI_API_KEY set
  3. Hybrid blend: 40% keyword + 60% LLM judge
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

PROMPTS_FILE = Path(__file__).parent / "benchmark_prompts.json"


def _load_factual_prompts() -> List[Dict]:
    with open(PROMPTS_FILE) as f:
        return json.load(f)["factual"]


def keyword_score(response: str, expected_keywords: List[str]) -> Dict:
    response_lower = response.lower()
    matched = [kw for kw in expected_keywords if kw.lower() in response_lower]
    hit = len(matched) > 0
    return {
        "hit": hit,
        "matched_keywords": matched,
        "total_expected": len(expected_keywords),
        "score": 1.0 if hit else 0.0,
    }


def run_hallucination_eval(
    assistant_fn: Callable[[str], str],
    assistant_name: str,
    use_llm_judge: bool = True,
    max_prompts: int = 50,
) -> Dict[str, Any]:
    """
    Run hallucination evaluation for an assistant.

    Parameters
    ----------
    assistant_fn : callable
        Function that takes a prompt str and returns a response str.
    assistant_name : str
        Label for reporting.
    use_llm_judge : bool
        Whether to also run LLM-as-judge for semantic scoring.
    max_prompts : int
        Maximum prompts to evaluate (for speed control).
    """
    from .llm_judge import LLMJudge, hybrid_factual_score

    prompts = _load_factual_prompts()[:max_prompts]
    judge = LLMJudge() if use_llm_judge else None

    results = []
    total_hybrid_score = 0.0
    judge_available = False

    for item in prompts:
        prompt = item["prompt"]
        expected = item["expected_keywords"]

        start = time.time()
        try:
            response = assistant_fn(prompt)
        except Exception as exc:
            response = f"[ERROR: {exc}]"
        latency = round((time.time() - start) * 1000, 1)

        # Layer 1: keyword
        kw_result = keyword_score(response, expected)

        # Layer 2: LLM judge
        llm_result = None
        if judge:
            llm_result = judge.judge_factual(prompt, response, expected)
            if llm_result.get("llm_judge_available"):
                judge_available = True

        # Hybrid score
        hybrid = hybrid_factual_score(kw_result["hit"], llm_result)
        total_hybrid_score += hybrid["final_score"]

        results.append({
            "id": item["id"],
            "prompt": prompt,
            "response": response,
            "latency_ms": latency,
            "keyword_result": kw_result,
            "llm_judge": llm_result,
            "hybrid": hybrid,
        })

    n = len(prompts)
    accuracy = round(total_hybrid_score / n * 100, 1) if n > 0 else 0
    hallucination_rate = round(100 - accuracy, 1)

    # Collect failure examples for appendix
    failures = [
        r for r in results
        if r["hybrid"]["final_score"] < 0.5
    ][:5]

    return {
        "assistant": assistant_name,
        "n_prompts": n,
        "accuracy_pct": accuracy,
        "hallucination_rate_pct": hallucination_rate,
        "llm_judge_used": judge_available,
        "scoring_method": "hybrid" if judge_available else "keyword_only",
        "results": results,
        "failure_examples": failures,
    }
