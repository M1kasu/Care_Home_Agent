"""Entity state machine that emits state_changed events."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .event_bus import EventBus
from .models import utc_now


class StateMachine:
    def __init__(self, states: dict[str, dict[str, Any]], event_bus: EventBus) -> None:
        self._states = states
        self._events = event_bus

    def get(self, entity_id: str) -> dict[str, Any] | None:
        state = self._states.get(entity_id)
        return deepcopy(state) if state is not None else None

    def all(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._states)

    def set(
        self,
        entity_id: str,
        value: Any,
        attributes: dict[str, Any] | None = None,
        *,
        source: str = "runtime",
        emit: bool = True,
    ) -> dict[str, Any]:
        old_state = deepcopy(self._states.get(entity_id))
        new_state = {
            "state": deepcopy(value),
            "attributes": deepcopy(attributes or {}),
            "updated_at": utc_now(),
        }
        comparable_old = None if old_state is None else {
            "state": old_state.get("state"),
            "attributes": old_state.get("attributes", {}),
        }
        comparable_new = {"state": new_state["state"], "attributes": new_state["attributes"]}
        self._states[entity_id] = new_state
        if emit and comparable_old != comparable_new:
            self._events.fire(
                "state_changed",
                {
                    "entity_id": entity_id,
                    "old_state": old_state,
                    "new_state": deepcopy(new_state),
                    "source": source,
                },
            )
        return deepcopy(new_state)

    def remove(self, entity_id: str, *, source: str = "runtime") -> None:
        old_state = self._states.pop(entity_id, None)
        if old_state is not None:
            self._events.fire(
                "state_changed",
                {"entity_id": entity_id, "old_state": old_state, "new_state": None, "source": source},
            )
