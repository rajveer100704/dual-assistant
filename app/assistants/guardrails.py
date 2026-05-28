"""
Safety & guardrails pipeline.
Screens both incoming prompts and outgoing responses.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# ─── Blocked content patterns ────────────────────────────────────────────────

BLOCKED_PATTERNS = [
    # Weapons / violence
    r"how (to|do i|can i|could i) (make|build|create|synthesize|manufacture) (a |an )?(bomb|explosive|weapon|poison|bioweapon|nerve agent)",
    r"(synthesize|manufacture|produce) (explosives?|nerve agents?|chemical weapons?|bioweapons?)",
    r"how to (kill|murder|assault|harm) (someone|a person|people)",
    r"step[s]? (to|for) (making|building) (a |an )?(gun|firearm|explosive)",
    # Malware / hacking
    r"(write|create|build|code) (me )?(a |an )?(malware|ransomware|virus|trojan|keylogger|exploit)",
    r"(bypass|crack|hack) (a )?(password|authentication|security system)",
    r"how to (conduct|perform|do) (a )?(ddos|sql injection|xss attack)",
    # Fraud / illegal financial
    r"(credit card|carding|card) fraud",
    r"(steal|clone) (credit cards?|identit)",
    r"(make|create|generate) (fake|counterfeit) (currency|money|documents)",
    # Self-harm
    r"how (to|do i) (kill|hurt|harm) myself",
    r"(best|effective) (method|way) (of|for) suicide",
    r"(how to|ways to) (commit suicide|self harm)",
    # Hate speech
    r"why (are|is) (women|men|blacks?|whites?|jews?|muslims?|christians?|asians?|hispanics?) (inferior|stupid|evil|bad|lazy|criminals?)",
    r"(racial|ethnic) (slur|hate)",
    # CSAM
    r"(child|minor|underage).{0,20}(porn|sexual|nude|naked)",
]

# ─── Prompt injection patterns ────────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore (all |all previous |previous |your |the )?(instructions?|system prompt|guidelines?|rules?)",
    r"(forget|disregard|override) (everything|all|your|the)? ?(instructions?|guidelines?|rules?|training|constraints?)",
    r"you are now (an? )?(evil|unrestricted|unfiltered|jailbroken|dan)",
    r"act (as if|like) (you have no|you are without) (restrictions?|limits?|guidelines?)",
    r"(reveal|show|print|output|repeat) (your |the )?(system prompt|instructions|guidelines)",
    r"pretend (you are|to be) (an? )?(evil|unrestricted|different) (ai|assistant|model)",
    r"(bypass|disable|turn off) (your )?(safety|filter|content policy|moderation)",
    r"do anything now",
    r"developer mode",
    r"jailbreak",
]

_BLOCKED_RE = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]
_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def is_unsafe(prompt: str) -> Tuple[bool, str]:
    """
    Check if a prompt contains blocked content.
    Returns (is_blocked, reason).
    """
    for pattern in _BLOCKED_RE:
        if pattern.search(prompt):
            logger.warning("Unsafe prompt detected: pattern=%s", pattern.pattern[:40])
            return True, "harmful_content"
    return False, ""


def is_injection(prompt: str) -> Tuple[bool, str]:
    """
    Check if a prompt is attempting prompt injection.
    Returns (is_injection, reason).
    """
    for pattern in _INJECTION_RE:
        if pattern.search(prompt):
            logger.warning("Prompt injection detected: pattern=%s", pattern.pattern[:40])
            return True, "prompt_injection"
    return False, ""


def screen_prompt(prompt: str) -> Tuple[bool, str]:
    """
    Full input screening pipeline.
    Returns (is_safe, refusal_message).
    """
    if not prompt or not prompt.strip():
        return False, "Please enter a message."

    blocked, _ = is_injection(prompt)
    if blocked:
        return False, (
            "I've detected an attempt to override my safety guidelines. "
            "I'm designed to be a helpful, safe assistant and will continue "
            "operating within those boundaries."
        )

    unsafe, _ = is_unsafe(prompt)
    if unsafe:
        return False, (
            "I'm not able to help with that request. It appears to involve "
            "content that could cause harm. If you have a genuine need, "
            "please consult appropriate professional resources."
        )

    return True, ""


def screen_output(response: str) -> Tuple[bool, str]:
    """
    Post-generation output safety check.
    Catches cases where the model generates unsafe content despite input filtering.
    """
    # Basic heuristic: check response for same blocked patterns
    for pattern in _BLOCKED_RE:
        if pattern.search(response):
            logger.warning("Unsafe output detected, replacing with refusal")
            return False, "I'm sorry, I can't provide that information."
    return True, response
