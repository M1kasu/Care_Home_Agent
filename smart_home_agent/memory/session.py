"""Sliding-window session memory stored inside the returned state."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class SessionMemory:
    def __init__(self, max_items: int = 12) -> None:
        self.max_items = max_items

    def append(
        self,
        state: dict[str, Any],
        *,
        role: str,
        content: str,
        intent: str | None = None,
    ) -> None:
        history = state.setdefault("history", [])
        history.append(
            {
                "role": role,
                "content": content,
                "intent": intent,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        )
        if len(history) > self.max_items:
            del history[: len(history) - self.max_items]

    def recent_text(self, state: dict[str, Any], limit: int = 6) -> str:
        recent = state.get("history", [])[-limit:]
        return "\n".join(f"{item.get('role')}: {item.get('content')}" for item in recent)
