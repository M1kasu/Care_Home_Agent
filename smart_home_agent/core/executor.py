"""DAG executor for local tool calls."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import PlanStep, ToolResult
from ..tools.registry import ToolRegistry


def topological_layers(steps: list[PlanStep]) -> list[list[PlanStep]]:
    if not steps:
        return []
    by_id = {step.step_id: step for step in steps}
    in_degree = {step.step_id: 0 for step in steps}
    children: dict[str, list[str]] = defaultdict(list)
    for step in steps:
        for dep in step.depends_on:
            if dep in by_id:
                in_degree[step.step_id] += 1
                children[dep].append(step.step_id)
    ready = [step_id for step_id, degree in in_degree.items() if degree == 0]
    layers: list[list[PlanStep]] = []
    while ready:
        layer = [by_id[step_id] for step_id in ready]
        layers.append(layer)
        next_ready: list[str] = []
        for step_id in ready:
            for child in children[step_id]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    next_ready.append(child)
        ready = next_ready
    return layers


class PlanExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def execute(self, steps: list[PlanStep], context: dict[str, Any], config: dict[str, Any]) -> tuple[list[ToolResult], dict[str, Any]]:
        results: list[ToolResult] = []
        safety = {"need_confirmation": False, "message": ""}
        max_steps = int(config.get("max_steps", 8))
        for layer in topological_layers(steps):
            for step in layer:
                if len(results) >= max_steps:
                    return results, safety
                result = self._registry.invoke(step.step_id, step.tool, step.args, context)
                results.append(result)
                if step.tool == "safety.check" and result.data.get("need_confirmation") and config.get("require_confirm", True):
                    pending = result.data.get("pending_action") or {}
                    context["state"]["pending_confirmations"] = [pending]
                    safety = {"need_confirmation": True, "message": result.message}
                    return results, safety
        return results, safety
