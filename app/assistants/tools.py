"""
Lightweight tool suite for both assistants.
Includes calculator, datetime, and unit-conversion tools.
"""

import math
import re
from datetime import datetime, timezone
from typing import Optional


# ─── Calculator ───────────────────────────────────────────────────────────────

_SAFE_NAMES = {k: v for k, v in vars(math).items() if not k.startswith("_")}
_SAFE_NAMES.update({"abs": abs, "round": round, "min": min, "max": max})


def calculator(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.

    Examples
    --------
    >>> calculator("2 ** 10")
    '1024'
    >>> calculator("sqrt(144)")
    '12.0'
    """
    # Strip any accidental text before/after the expression
    expr = expression.strip().strip("=").strip()
    try:
        result = eval(expr, {"__builtins__": {}}, _SAFE_NAMES)  # noqa: S307
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception as exc:
        return f"Error: could not evaluate '{expr}' — {exc}"


# ─── DateTime ─────────────────────────────────────────────────────────────────

def current_datetime(timezone_name: Optional[str] = None) -> str:
    """Return current UTC date/time as a readable string."""
    now = datetime.now(timezone.utc)
    return now.strftime("UTC %Y-%m-%d %H:%M:%S (%A)")


# ─── Tool Router ──────────────────────────────────────────────────────────────

_CALC_PATTERN = re.compile(
    r"(?:calculate|compute|what is|solve|eval)\s+(.+)", re.IGNORECASE
)
_DATE_PATTERN = re.compile(
    r"(?:what(?:'?s| is) (?:today|the (?:date|time|current (?:date|time|datetime))))"
    r"|(?:current (?:date|time|datetime))"
    r"|(?:today(?:'?s)? date)",
    re.IGNORECASE,
)


def route_tools(user_input: str) -> Optional[str]:
    """
    Check if a user message can be resolved by a tool without calling the LLM.
    Returns tool output string if matched, else None.
    Date check runs before calculator to prevent "what is the current date"
    being captured by the calc regex.
    """
    # Date/time check first (higher specificity)
    if _DATE_PATTERN.search(user_input):
        return f"The current date and time is: {current_datetime()}"

    # Calculator — only fires when explicit math verb is present
    calc_match = _CALC_PATTERN.search(user_input)
    if calc_match:
        expr = calc_match.group(1).strip()
        # Skip if the expression looks like natural language (no digits or operators)
        if any(ch in expr for ch in "0123456789+-*/^%()"):
            result = calculator(expr)
            return f"Calculator result: {result}"

    return None
