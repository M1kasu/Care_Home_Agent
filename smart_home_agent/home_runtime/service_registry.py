"""Runtime service registry, separate from the Agent-facing tool registry."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .models import utc_now

ServiceHandler = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


class ServiceRegistry:
    def __init__(self, call_log: list[dict[str, Any]], *, max_calls: int = 100) -> None:
        self._handlers: dict[str, ServiceHandler] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._call_log = call_log
        self._max_calls = max_calls

    def register(
        self,
        name: str,
        handler: ServiceHandler,
        *,
        side_effect: str = "read",
        integration: str = "core",
        replace: bool = False,
    ) -> None:
        if name in self._handlers and not replace:
            raise ValueError(f"service already registered: {name}")
        self._handlers[name] = handler
        self._metadata[name] = {"name": name, "side_effect": side_effect, "integration": integration}

    def has(self, name: str) -> bool:
        return name in self._handlers

    def handler(self, name: str) -> ServiceHandler | None:
        """Return a registered handler so an overlay integration can delegate."""
        return self._handlers.get(name)

    def list_services(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._metadata.values()]

    def call(self, name: str, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        handler = self._handlers.get(name)
        if handler is None:
            return {"status": "error", "data": {}, "message": f"运行时服务未注册: {name}"}
        try:
            payload = handler(dict(args or {}), context)
        except Exception as exc:  # noqa: BLE001 - service boundary must be isolated
            payload = {"status": "error", "data": {}, "message": f"{type(exc).__name__}: {exc}"}
        entry = {
            "service": name,
            "args": dict(args or {}),
            "status": str(payload.get("status", "success")),
            "timestamp": utc_now(),
        }
        self._call_log.append(entry)
        if len(self._call_log) > self._max_calls:
            del self._call_log[: len(self._call_log) - self._max_calls]
        return payload
