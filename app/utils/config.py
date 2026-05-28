"""Configuration utilities — load and validate environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

_root = Path(__file__).parent.parent.parent
load_dotenv(_root / ".env", override=False)


def get_gemini_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            "Get a free key at: https://aistudio.google.com/app/apikey  "
            "Then add to .env: GEMINI_API_KEY=AIzaSy..."
        )
    return key


def is_debug() -> bool:
    return os.getenv("DEBUG", "false").lower() == "true"
