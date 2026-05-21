"""Lightweight edge smart-home agent."""

from __future__ import annotations

from .pipeline import SmartHomeAgent

_AGENT = SmartHomeAgent()


def run(user_input: str, state: dict | None = None, config: dict | None = None) -> dict:
    """Official run entry used by the contest wrapper."""
    return _AGENT.run(user_input=user_input, state=state, config=config)


__all__ = ["SmartHomeAgent", "run"]
