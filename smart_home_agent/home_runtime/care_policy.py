"""Event-driven household care policies."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .models import RuntimeEvent, utc_now

if TYPE_CHECKING:
    from .runtime import HomeRuntime


class CarePolicyEngine:
    def __init__(self, runtime: "HomeRuntime") -> None:
        self._runtime = runtime

    def install(self) -> None:
        self._runtime.events.subscribe("runtime_ready", self._on_runtime_ready)
        self._runtime.events.subscribe("state_changed", self._on_state_changed)

    def _on_runtime_ready(self, event: RuntimeEvent) -> None:
        del event
        self.evaluate_all()

    def _on_state_changed(self, event: RuntimeEvent) -> None:
        entity_id = str(event.data.get("entity_id") or "")
        if not entity_id.startswith("sensor."):
            return
        new_state = event.data.get("new_state") or {}
        attributes = dict(new_state.get("attributes") or {})
        room = attributes.get("room")
        if room:
            sensor = self._runtime.root_state.get("sensors", {}).get(room, {})
            self.evaluate_room(str(room), sensor)

    def evaluate_all(self) -> list[dict[str, Any]]:
        for room, sensor in self._runtime.root_state.get("sensors", {}).items():
            self.evaluate_room(room, sensor)
        return self.active_alerts()

    def evaluate_room(self, room: str, sensor: dict[str, Any]) -> None:
        conditions = {
            "elderly_inactive": room == "老人房" and not sensor.get("motion") and int(sensor.get("last_motion_min", 0)) >= 120,
            "elderly_low_temperature": room == "老人房" and float(sensor.get("temperature", 99)) < 18,
            "child_noise": room == "儿童房" and float(sensor.get("noise_db", 0)) > 60,
        }
        definitions = {
            "elderly_inactive": ("warning", "老人房已超过 120 分钟无人活动，建议家人确认老人状态"),
            "elderly_low_temperature": ("warning", "老人房温度低于 18℃，建议检查供暖并避免老人着凉"),
            "child_noise": ("info", "儿童房噪声超过 60dB，建议开启安静/睡眠场景"),
        }
        for alert_type, active in conditions.items():
            if not active:
                self._resolve(alert_type, room)
                continue
            level, message = definitions[alert_type]
            self._upsert(alert_type, room, level, message, sensor)

    def active_alerts(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._runtime.root_state.setdefault("alerts", []) if item.get("active", True)]

    def _upsert(
        self,
        alert_type: str,
        room: str,
        level: str,
        message: str,
        sensor: dict[str, Any],
    ) -> None:
        alerts = self._runtime.root_state.setdefault("alerts", [])
        existing = next((item for item in alerts if item.get("type") == alert_type and item.get("room") == room), None)
        payload = {
            "id": f"alert-{alert_type}-{room}",
            "type": alert_type,
            "room": room,
            "level": level,
            "message": message,
            "active": True,
            "sensor": dict(sensor),
            "updated_at": utc_now(),
        }
        if existing is not None:
            was_active = bool(existing.get("active", True))
            existing.update(payload)
            if was_active:
                return
        else:
            alerts.append(payload)
        self._runtime.events.fire("care_alert", payload)

    def _resolve(self, alert_type: str, room: str) -> None:
        for item in self._runtime.root_state.setdefault("alerts", []):
            if item.get("type") == alert_type and item.get("room") == room and item.get("active", True):
                item["active"] = False
                item["resolved_at"] = utc_now()
                self._runtime.events.fire("care_alert_resolved", dict(item))
