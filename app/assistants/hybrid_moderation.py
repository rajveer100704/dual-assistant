"""
Hybrid moderation architecture — Gemini 2.5 Flash as neural classifier.

Layer 1: Regex prescreening (30+ patterns, zero latency)
Layer 2: Gemini 2.5 Flash classifying against LlamaGuard S1-S14 taxonomy
         Free tier — no GPU, no credit card required.
"""

import json
import logging
import os
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

LLAMAGUARD_CATEGORIES = {
    "S1": "Violent Crimes", "S2": "Non-Violent Crimes", "S3": "Sex-Related Crimes",
    "S4": "Child Sexual Exploitation", "S5": "Defamation",
    "S6": "Specialized Advice (medical/legal/financial)", "S7": "Privacy",
    "S8": "Intellectual Property", "S9": "Indiscriminate Weapons (CBRN)",
    "S10": "Hate Speech", "S11": "Suicide & Self-Harm", "S12": "Sexual Content",
    "S13": "Elections", "S14": "Code Interpreter Abuse",
}

NEURAL_MODERATION_PROMPT = """You are a content safety classifier implementing the LlamaGuard safety taxonomy.
Classify the following user prompt.
Return ONLY valid JSON:

{{
  "safe": true or false,
  "violated_categories": ["S1", "S9"],
  "severity": "none" | "low" | "medium" | "high",
  "reasoning": "one sentence"
}}

Category codes:
S1=Violent Crimes, S2=Non-Violent Crimes, S3=Sex Crimes, S4=Child Exploitation,
S5=Defamation, S6=Harmful Advice, S7=Privacy, S8=IP, S9=CBRN Weapons,
S10=Hate Speech, S11=Self-Harm, S12=Sexual Content, S13=Elections, S14=Code Abuse

User prompt:
{prompt}"""


class NeuralModerator:
    """Gemini 2.5 Flash neural moderation classifier (free tier)."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
        except ImportError:
            return None
        return self._client

    def classify(self, prompt: str) -> Dict:
        client = self._get_client()
        if not client:
            return {"available": False, "safe": True, "violated_categories": [],
                    "severity": "none", "reasoning": "Neural moderation unavailable — regex layer active"}
        try:
            from google.genai import types as _types
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=NEURAL_MODERATION_PROMPT.format(prompt=prompt[:600]),
                config=_types.GenerateContentConfig(
                    system_instruction="You are a content safety classifier. Respond with valid JSON only.",
                    temperature=0.0,
                    max_output_tokens=200,
                ),
            )
            raw = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(raw)
            result["available"] = True
            return result
        except Exception as exc:
            logger.debug("Neural moderation error: %s", exc)
            return {"available": False, "safe": True, "violated_categories": [],
                    "severity": "none", "reasoning": f"Classifier error: {exc}"}


_neural_mod = NeuralModerator()


def hybrid_screen(prompt: str) -> Tuple[bool, str, Dict]:
    """Two-layer safety: regex → neural. Returns (is_safe, refusal_msg, metadata)."""
    from .guardrails import screen_prompt
    l1_safe, l1_refusal = screen_prompt(prompt)
    if not l1_safe:
        return False, l1_refusal, {"layer": "regex", "blocked_by": "regex_prescreening"}

    neural = _neural_mod.classify(prompt)
    if not neural.get("safe", True) and neural.get("severity") in ("high", "medium"):
        cats = neural.get("violated_categories", [])
        cat_names = [LLAMAGUARD_CATEGORIES.get(c, c) for c in cats]
        refusal = (
            "I'm not able to help with that. This request may involve: "
            f"{', '.join(cat_names) if cat_names else 'potentially harmful content'}."
        )
        return False, refusal, {"layer": "neural", "neural": neural,
                                "blocked_by": "neural_classifier"}

    return True, "", {"layer": "passed", "neural": neural, "blocked_by": None}
