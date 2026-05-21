"""Serializable models used across routing, planning and execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Intent:
    name: str
    confidence: float
    slots: dict[str, Any] = field(default_factory=dict)
    source: str = "rule"
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PlanStep:
    step_id: str
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    depends_on: list[str] = field(default_factory=list)
    requires_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ToolResult:
    step_id: str
    tool: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ToolSpec:
    name: str
    description: str
    side_effect: str = "read"
    requires_confirmation: bool = False
    timeout_ms: int = 3000
