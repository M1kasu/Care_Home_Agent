"""Agent-facing adapters for embedded home-runtime services."""

from __future__ import annotations

from typing import Any

from ..core.models import ToolSpec
from ..home_runtime.integrations.simulator import (
    DEFAULT_HOME_STATE,
    SIMULATOR_SERVICE_SPECS,
    SimulatorIntegration,
    ensure_home_state,
)
from ..memory.family_profile import FamilyProfileMemory
from ..memory.sqlite_store import SQLiteKnowledgeBase
from .registry import ToolRegistry


AGENT_EXPOSED_SERVICES = (
    "home_profile.query",
    "device.query",
    "device.control",
    "scene.apply",
    "network.diagnose",
    "network.apply_qos",
    "reminder.create",
    "reminder.query",
    "reminder.complete",
    "reminder.cancel",
    "safety.check",
    "sensor.query",
    "sensor.check_alert",
    "energy.query",
    "energy.optimize",
    "device.set_timer",
)


def register_home_tools(
    registry: ToolRegistry,
    knowledge_base: SQLiteKnowledgeBase,
    profile_memory: FamilyProfileMemory | None = None,
) -> None:
    """Register a narrow Agent bridge; business behavior stays in integrations."""
    for service_name in AGENT_EXPOSED_SERVICES:
        metadata = SIMULATOR_SERVICE_SPECS[service_name]
        registry.register(
            ToolSpec(
                service_name,
                metadata["description"],
                side_effect=metadata["side_effect"],
            ),
            _runtime_service_adapter(service_name),
        )

    def _knowledge_search(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        del context
        query = str(args.get("query") or "")
        hits = knowledge_base.search(query, top_k=int(args.get("top_k", 3)))
        message = f"本地知识库命中 {len(hits)} 条" if hits else "本地知识库未命中可信答案"
        return {"status": "success", "data": {"hits": hits}, "message": message}

    registry.register(ToolSpec("knowledge.search", "SQLite 本地知识库检索"), _knowledge_search)

    if profile_memory is not None:

        def _profile_remember(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
            state = context["state"]
            family = state.get("family", {})
            result = profile_memory.remember_from_text(
                str(args.get("text") or ""),
                known_members=list(family.get("members", {}).keys()),
                member_groups=family.get("member_groups", {}),
            )
            state["family_profiles"] = result["profiles"]
            status = "success" if result.get("updated") else "error"
            return {"status": status, "data": result, "message": result["message"]}

        def _profile_query(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
            state = context["state"]
            member = args.get("member")
            result = profile_memory.query(str(member) if member else None)
            state["family_profiles"] = profile_memory.load()
            return {"status": "success", "data": result, "message": result["message"]}

        registry.register(ToolSpec("profile.remember", "写入长期家庭成员画像", side_effect="write"), _profile_remember)
        registry.register(ToolSpec("profile.query", "查询长期家庭成员画像"), _profile_query)


def _runtime_service_adapter(service_name: str) -> Any:
    def _invoke(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        runtime = context.get("runtime")
        if runtime is None:
            return {"status": "error", "data": {}, "message": "Home Runtime 尚未启动"}
        return runtime.call_service(service_name, args)

    return _invoke


__all__ = [
    "DEFAULT_HOME_STATE",
    "SimulatorIntegration",
    "ensure_home_state",
    "register_home_tools",
]
