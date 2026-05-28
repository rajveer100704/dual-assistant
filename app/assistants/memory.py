"""
Conversation memory system with sliding window for dual assistants.
Maintains independent session history per assistant.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
import time


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)


class ConversationMemory:
    """
    Sliding-window conversation memory.
    Keeps the last `window_size` exchanges (user + assistant pairs).
    """

    def __init__(self, window_size: int = 5) -> None:
        self.window_size = window_size
        self._messages: List[Message] = []

    def save(self, user_input: str, assistant_response: str) -> None:
        """Append a user/assistant exchange and trim to window."""
        self._messages.append(Message(role="user", content=user_input))
        self._messages.append(Message(role="assistant", content=assistant_response))
        # Keep only last window_size exchanges (2 messages each)
        self._messages = self._messages[-(self.window_size * 2):]

    def get_messages(self) -> List[Dict[str, str]]:
        """Return messages as list of dicts for API calls."""
        return [{"role": m.role, "content": m.content} for m in self._messages]

    def get_context(self) -> str:
        """Return conversation history as a formatted string for prompt injection."""
        lines = []
        for m in self._messages:
            prefix = "User" if m.role == "user" else "Assistant"
            lines.append(f"{prefix}: {m.content}")
        return "\n".join(lines)

    def reset(self) -> None:
        """Clear all conversation history."""
        self._messages = []

    def replay(self) -> List[Dict]:
        """Return full message log with timestamps for observability."""
        return [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp}
            for m in self._messages
        ]

    def __len__(self) -> int:
        return len(self._messages)
