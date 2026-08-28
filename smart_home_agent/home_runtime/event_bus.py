"""Synchronous event bus used by the single-process runtime."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from .models import RuntimeEvent

EventHandler = Callable[[RuntimeEvent], None]


class EventBus:
    def __init__(self, event_log: list[dict[str, Any]], *, max_events: int = 100) -> None:
        self._listeners: dict[str, list[EventHandler]] = defaultdict(list)
        self._event_log = event_log
        self._max_events = max_events

    def subscribe(self, event_type: str, handler: EventHandler) -> Callable[[], None]:
        self._listeners[event_type].append(handler)

        def unsubscribe() -> None:
            listeners = self._listeners.get(event_type, [])
            if handler in listeners:
                listeners.remove(handler)

        return unsubscribe

    def fire(self, event_type: str, data: dict[str, Any] | None = None) -> RuntimeEvent:
        event = RuntimeEvent(event_type=event_type, data=dict(data or {}))
        self._event_log.append(event.to_dict())
        if len(self._event_log) > self._max_events:
            del self._event_log[: len(self._event_log) - self._max_events]
        errors: list[str] = []
        for handler in [*self._listeners.get(event_type, []), *self._listeners.get("*", [])]:
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001 - isolate event consumers
                errors.append(f"{type(exc).__name__}: {exc}")
        if errors:
            event.data["handler_errors"] = errors
            self._event_log[-1] = event.to_dict()
        return event
