"""Small white-list tool registry inspired by Agent-Hub SkillRegistry."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from ..core.models import ToolResult, ToolSpec

ToolFunc = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolSpec, ToolFunc]] = {}

    def register(self, spec: ToolSpec, func: ToolFunc) -> None:
        if spec.name in self._tools:
            raise ValueError(f"tool already registered: {spec.name}")
        self._tools[spec.name] = (spec, func)

    def spec(self, name: str) -> ToolSpec | None:
        pair = self._tools.get(name)
        return pair[0] if pair else None

    def list_tools(self) -> list[dict[str, Any]]:
        return [asdict(spec) for spec, _ in self._tools.values()]

    def invoke(
        self,
        step_id: str,
        tool_name: str,
        args: dict[str, Any],
        context: dict[str, Any],
    ) -> ToolResult:
        pair = self._tools.get(tool_name)
        if pair is None:
            return ToolResult(
                step_id=step_id,
                tool=tool_name,
                status="error",
                message=f"工具未注册: {tool_name}",
            )
        _, func = pair
        start = time.perf_counter()
        try:
            payload = func(args, context)
            status = str(payload.get("status", "success"))
            data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
            message = str(payload.get("message", ""))
        except Exception as exc:  # noqa: BLE001 - tool boundary should not crash pipeline
            status = "error"
            data = {}
            message = str(exc)
        duration_ms = int((time.perf_counter() - start) * 1000)
        return ToolResult(
            step_id=step_id,
            tool=tool_name,
            status=status,
            data=data,
            message=message,
            duration_ms=duration_ms,
        )
