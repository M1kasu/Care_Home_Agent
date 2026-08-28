"""ESPHome Native API integration for the embedded home runtime.

The implementation follows the same boundary used by Home Assistant's ESPHome
integration: aioesphomeapi owns the persistent, encrypted local-push connection;
the Agent only sees normalized runtime services and entity state.
"""

from __future__ import annotations

import asyncio
import atexit
import logging
import math
import threading
import time
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from aioesphomeapi import (
    APIClient,
    BinarySensorInfo,
    BinarySensorState,
    ClimateInfo,
    ClimateMode,
    ClimateState,
    CoverInfo,
    CoverState,
    LightInfo,
    LightState,
    SensorInfo,
    SensorState,
)

from ..models import AreaRecord, DeviceRecord, EntityRecord

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ESPHomeNode:
    device_id: str
    name: str
    device_type: str
    host: str
    port: int
    expected_name: str


def default_nodes(host: str) -> tuple[ESPHomeNode, ...]:
    return (
        ESPHomeNode("livingroom_light", "客厅灯", "light", host, 6053, "living-room-light"),
        ESPHomeNode("livingroom_curtain", "客厅窗帘", "cover", host, 6054, "living-room-curtain"),
        ESPHomeNode("livingroom_presence", "客厅人体存在", "presence", host, 6056, "living-room-presence"),
        ESPHomeNode("livingroom_ac", "客厅空调", "air_conditioner", host, 6055, "living-room-ac"),
    )


class ESPHomeBridge:
    """Own one background asyncio loop and persistent clients for all nodes."""

    def __init__(
        self,
        nodes: tuple[ESPHomeNode, ...],
        noise_psk: str,
        *,
        command_timeout: float = 5.0,
    ) -> None:
        self.nodes = nodes
        self.noise_psk = noise_psk
        self.command_timeout = command_timeout
        self._lock = threading.RLock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started = threading.Event()
        self._ready = {node.device_id: threading.Event() for node in nodes}
        self._clients: dict[str, APIClient] = {}
        self._entities: dict[str, dict[tuple[int, int], Any]] = {
            node.device_id: {} for node in nodes
        }
        self._states: dict[str, dict[tuple[int, int], Any]] = {
            node.device_id: {} for node in nodes
        }
        self._status: dict[str, dict[str, Any]] = {
            node.device_id: {
                "connected": False,
                "host": node.host,
                "port": node.port,
                "error": "not started",
            }
            for node in nodes
        }

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._thread_main,
            name="esphome-native-api",
            daemon=True,
        )
        self._thread.start()
        if not self._started.wait(3):
            raise RuntimeError("ESPHome background event loop failed to start")

    def wait_ready(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        for event in self._ready.values():
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not event.wait(remaining):
                return False
        return True

    def status(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return deepcopy(self._status)

    def device_states(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {
                node.device_id: self._normalize_device(node)
                for node in self.nodes
                if self._ready[node.device_id].is_set()
            }

    def command(self, device_id: str, action: str, value: Any = None) -> None:
        loop = self._loop
        if loop is None or not loop.is_running():
            raise ConnectionError("ESPHome event loop is not running")
        future = asyncio.run_coroutine_threadsafe(
            self._async_command(device_id, action, value),
            loop,
        )
        future.result(timeout=self.command_timeout)

    def stop(self) -> None:
        loop = self._loop
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._started.set()
        for node in self.nodes:
            loop.create_task(self._maintain_node(node))
        try:
            loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    async def _maintain_node(self, node: ESPHomeNode) -> None:
        backoff = 1.0
        while True:
            disconnected = asyncio.Event()

            async def on_stop(
                expected_disconnect: bool,
                event: asyncio.Event = disconnected,
            ) -> None:
                del expected_disconnect
                event.set()

            client = APIClient(
                node.host,
                node.port,
                noise_psk=self.noise_psk,
                expected_name=node.expected_name,
                client_info="Care Home Agent 0.1.0",
            )
            try:
                await client.connect(on_stop=on_stop, login=True)
                device_info, entities, _ = await client.device_info_and_list_entities()
                with self._lock:
                    self._clients[node.device_id] = client
                    self._entities[node.device_id] = {
                        _entity_key(entity): entity for entity in entities
                    }
                    self._states[node.device_id] = {}
                    self._status[node.device_id] = {
                        "connected": True,
                        "host": node.host,
                        "port": node.port,
                        "name": device_info.name,
                        "api_version": str(client.api_version),
                        "entity_count": len(entities),
                        "error": "",
                    }
                    self._ready[node.device_id].clear()
                client.subscribe_states(
                    lambda state, node_id=node.device_id: self._on_state(node_id, state)
                )
                backoff = 1.0
                await disconnected.wait()
            except asyncio.CancelledError:
                try:
                    await client.disconnect(force=True)
                except Exception as exc:
                    LOGGER.debug("Failed to disconnect ESPHome client cleanly", exc_info=exc)
                raise
            except Exception as exc:  # noqa: BLE001 - reconnect boundary
                with self._lock:
                    self._clients.pop(node.device_id, None)
                    self._status[node.device_id].update(
                        connected=False,
                        error=f"{type(exc).__name__}: {exc}",
                    )
            finally:
                with self._lock:
                    if self._clients.get(node.device_id) is client:
                        self._clients.pop(node.device_id, None)
                    self._status[node.device_id]["connected"] = False
                    self._ready[node.device_id].clear()
            await asyncio.sleep(backoff)
            backoff = min(30.0, backoff * 2)

    def _on_state(self, device_id: str, state: Any) -> None:
        with self._lock:
            self._states[device_id][_entity_key(state)] = state
            self._ready[device_id].set()

    async def _async_command(self, device_id: str, action: str, value: Any) -> None:
        with self._lock:
            client = self._clients.get(device_id)
            entities = list(self._entities.get(device_id, {}).values())
        if client is None:
            raise ConnectionError(f"ESPHome device is disconnected: {device_id}")

        node = next((item for item in self.nodes if item.device_id == device_id), None)
        if node is None:
            raise ValueError(f"Unknown ESPHome device: {device_id}")
        entity = _primary_entity(node.device_type, entities)
        if entity is None:
            raise LookupError(f"No controllable {node.device_type} entity on {device_id}")
        key = int(entity.key)
        api_device_id = int(getattr(entity, "device_id", 0))

        if node.device_type == "light":
            if action == "turn_on":
                client.light_command(key, state=True, device_id=api_device_id)
            elif action == "turn_off":
                client.light_command(key, state=False, device_id=api_device_id)
            elif action == "set_brightness":
                brightness = _bounded_float(value, 0, 100) / 100
                client.light_command(
                    key,
                    state=brightness > 0,
                    brightness=brightness,
                    device_id=api_device_id,
                )
            else:
                raise ValueError(f"Unsupported light action: {action}")
        elif node.device_type == "cover":
            if action in {"turn_on", "open"}:
                client.cover_command(key, position=1.0, device_id=api_device_id)
            elif action in {"turn_off", "close"}:
                client.cover_command(key, position=0.0, device_id=api_device_id)
            elif action == "stop":
                client.cover_command(key, stop=True, device_id=api_device_id)
            else:
                raise ValueError(f"Unsupported cover action: {action}")
        elif node.device_type == "air_conditioner":
            if action == "turn_off":
                client.climate_command(key, mode=ClimateMode.OFF, device_id=api_device_id)
            elif action == "turn_on":
                client.climate_command(key, mode=ClimateMode.COOL, device_id=api_device_id)
            elif action == "set_temperature":
                temperature = _bounded_float(value, 16, 30)
                client.climate_command(
                    key,
                    mode=ClimateMode.COOL,
                    target_temperature_high=temperature,
                    device_id=api_device_id,
                )
            elif action == "set_mode":
                mode = ClimateMode.OFF if str(value).lower() == "off" else ClimateMode.COOL
                client.climate_command(key, mode=mode, device_id=api_device_id)
            else:
                raise ValueError(f"Unsupported climate action: {action}")
        else:
            raise ValueError(f"Device is read-only: {device_id}")

        # Commands are fire-and-push at protocol level. Yield so the subscription
        # callback can ingest the immediate state update before the caller syncs.
        await asyncio.sleep(0.25)

    def _normalize_device(self, node: ESPHomeNode) -> dict[str, Any]:
        states = self._states[node.device_id]
        entities = self._entities[node.device_id]
        by_type: dict[type[Any], tuple[Any, Any]] = {}
        for key, info in entities.items():
            state = states.get(key)
            if state is not None:
                by_type[type(info)] = (info, state)

        base: dict[str, Any] = {
            "name": node.name,
            "room": "客厅",
            "type": node.device_type,
            "source": "esphome",
            "available": bool(self._status[node.device_id].get("connected")),
            "host": node.host,
            "port": node.port,
        }
        if node.device_type == "light":
            _, state = by_type.get(LightInfo, (None, None))
            if isinstance(state, LightState):
                base.update(
                    power="on" if state.state else "off",
                    brightness=round(state.brightness * 100) if state.state else 0,
                )
        elif node.device_type == "cover":
            _, state = by_type.get(CoverInfo, (None, None))
            if isinstance(state, CoverState):
                operation = getattr(state.current_operation, "name", "IDLE").lower()
                base.update(
                    power="open" if state.position > 0 else "closed",
                    position=round(state.position * 100),
                    operation=operation,
                )
        elif node.device_type == "presence":
            _, state = by_type.get(BinarySensorInfo, (None, None))
            if isinstance(state, BinarySensorState):
                base.update(power="on" if state.state else "off", occupied=bool(state.state))
        elif node.device_type == "air_conditioner":
            _, climate = by_type.get(ClimateInfo, (None, None))
            _, sensor = by_type.get(SensorInfo, (None, None))
            if isinstance(climate, ClimateState):
                mode = getattr(climate.mode, "name", "OFF").lower()
                action = getattr(climate.action, "name", "OFF").lower()
                target = climate.target_temperature_high or climate.target_temperature
                base.update(
                    power="off" if mode == "off" else "on",
                    mode=mode,
                    action=action,
                    temperature=_finite_or_none(target),
                    current_temperature=_finite_or_none(climate.current_temperature),
                )
            if isinstance(sensor, SensorState):
                base["current_temperature"] = _finite_or_none(sensor.state)
        return base


class ESPHomeIntegration:
    """Overlay real ESPHome devices on top of the contest simulator services."""

    domain = "esphome"

    def __init__(
        self,
        bridge: ESPHomeBridge,
        *,
        connect_timeout: float = 12.0,
        strict_connect: bool = True,
    ) -> None:
        self.bridge = bridge
        self.connect_timeout = connect_timeout
        self.strict_connect = strict_connect
        self._fallback_services: dict[str, Any] = {}

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ESPHomeIntegration:
        host = str(config.get("esphome_host") or "192.168.111.134")
        noise_psk = str(config.get("esphome_noise_psk") or "").strip()
        if not noise_psk:
            raise ValueError(
                "ESPHOME_NOISE_PSK is required when HOME_BACKEND=esphome"
            )
        bridge = _shared_bridge(
            default_nodes(host),
            noise_psk,
            command_timeout=float(config.get("esphome_command_timeout", 5)),
        )
        return cls(
            bridge,
            connect_timeout=float(config.get("esphome_connect_timeout", 12)),
            strict_connect=bool(config.get("esphome_strict_connect", True)),
        )

    def setup(self, runtime: Any) -> None:
        self.bridge.start()
        ready = self.bridge.wait_ready(self.connect_timeout)
        if self.strict_connect and not ready:
            failures = {
                key: value.get("error")
                for key, value in self.bridge.status().items()
                if not value.get("connected")
            }
            raise ConnectionError(f"ESPHome nodes not ready: {failures}")

        runtime.areas.register(AreaRecord(area_id="客厅", name="客厅"))
        self._sync(runtime)
        self._fallback_services = {
            name: runtime.services.handler(name)
            for name in ("device.control", "scene.apply")
        }
        runtime.services.register(
            "device.query", self._device_query, integration=self.domain, replace=True
        )
        runtime.services.register(
            "device.control",
            self._device_control,
            side_effect="write",
            integration=self.domain,
            replace=True,
        )
        runtime.services.register(
            "sensor.query", self._sensor_query, integration=self.domain, replace=True
        )
        runtime.services.register(
            "scene.apply",
            self._scene_apply,
            side_effect="write",
            integration=self.domain,
            replace=True,
        )
        runtime.services.register(
            "esphome.status", self._status, integration=self.domain
        )

    def _sync(self, runtime: Any) -> dict[str, dict[str, Any]]:
        devices = self.bridge.device_states()
        root = runtime.root_state
        room_devices = root["family"]["rooms"]["客厅"].setdefault("devices", [])
        for device_id, info in devices.items():
            root["devices"][device_id] = deepcopy(info)
            if device_id not in room_devices:
                room_devices.append(device_id)
            domain = {
                "light": "light",
                "cover": "cover",
                "presence": "binary_sensor",
                "air_conditioner": "climate",
            }[info["type"]]
            entity_id = f"{domain}.{device_id}"
            runtime.devices.register(
                DeviceRecord(
                    device_id=device_id,
                    name=info["name"],
                    manufacturer="ESPHome",
                    model="Host",
                    area_id="客厅",
                    integration=self.domain,
                    attributes={"host": info["host"], "port": info["port"]},
                )
            )
            runtime.entities.register(
                EntityRecord(
                    entity_id=entity_id,
                    domain=domain,
                    name=info["name"],
                    device_id=device_id,
                    area_id="客厅",
                )
            )
            runtime.states.set(
                entity_id,
                _primary_state(info),
                deepcopy(info),
                source="esphome",
                emit=False,
            )

        presence = devices.get("livingroom_presence", {})
        ac = devices.get("livingroom_ac", {})
        sensor = root["sensors"].setdefault("客厅", {})
        if "occupied" in presence:
            sensor["motion"] = presence["occupied"]
            sensor["last_motion_min"] = 0 if presence["occupied"] else sensor.get("last_motion_min", 1)
            sensor.setdefault("sources", {})["motion"] = "esphome"
        if ac.get("current_temperature") is not None:
            sensor["temperature"] = ac["current_temperature"]
            sensor.setdefault("sources", {})["temperature"] = "esphome"
        runtime.states.set(
            "sensor.living_room_environment",
            sensor.get("temperature"),
            {"room": "客厅", **deepcopy(sensor), "source": "esphome"},
            source="esphome",
            emit=False,
        )
        return devices

    def _device_query(self, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        runtime = context["runtime"]
        devices = self._sync(runtime)
        state_devices = context["state"]["devices"]
        device_id = args.get("device_id")
        if device_id:
            device = state_devices.get(device_id)
            if not device:
                return {"status": "error", "data": {}, "message": f"未找到设备 {device_id}"}
            return {
                "status": "success",
                "data": {"device_id": device_id, "state": deepcopy(device)},
                "message": f"{device['name']} 状态已读取",
            }
        room = args.get("room")
        selected = {
            key: deepcopy(value)
            for key, value in state_devices.items()
            if room is None or value.get("room") == room
        }
        return {
            "status": "success",
            "data": {"devices": selected, "esphome_devices": list(devices)},
            "message": "设备状态已读取",
        }

    def _device_control(self, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        runtime = context["runtime"]
        self._sync(runtime)
        device_id = args.get("device_id") or _resolve_device_id(args)
        if device_id not in {node.device_id for node in self.bridge.nodes}:
            fallback = self._fallback_services.get("device.control")
            if fallback is not None:
                return fallback(args, context)
            return {"status": "error", "data": {}, "message": "该设备未映射到 ESPHome"}
        old_state = deepcopy(context["state"]["devices"].get(device_id, {}))
        self.bridge.command(device_id, str(args.get("action") or ""), args.get("value"))
        self._sync(runtime)
        new_state = deepcopy(context["state"]["devices"].get(device_id, {}))
        return {
            "status": "success",
            "data": {
                "device_id": device_id,
                "old_state": old_state,
                "new_state": new_state,
            },
            "message": f"{new_state.get('name', device_id)} 已通过 ESPHome 执行 {args.get('action')}",
        }

    def _sensor_query(self, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        runtime = context["runtime"]
        self._sync(runtime)
        room = args.get("room")
        sensors = context["state"].get("sensors", {})
        if room:
            sensor = sensors.get(room)
            if sensor is None:
                return {"status": "error", "data": {}, "message": f"未找到房间 {room} 的传感器"}
            return {
                "status": "success",
                "data": {"room": room, "sensor": deepcopy(sensor)},
                "message": f"{room} ESPHome 传感器已读取",
            }
        return {
            "status": "success",
            "data": {"sensors": deepcopy(sensors)},
            "message": "传感器全量已读取",
        }

    def _scene_apply(self, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        scene = str(args.get("scene") or "movie")
        fallback = self._fallback_services.get("scene.apply")
        actions: list[tuple[str, str, Any]] = []
        if scene == "movie":
            actions = [
                ("livingroom_curtain", "turn_off", None),
                ("livingroom_light", "set_brightness", 15),
                ("livingroom_ac", "set_temperature", 26),
            ]
        elif scene == "home":
            actions = [
                ("livingroom_curtain", "turn_on", None),
                ("livingroom_light", "turn_on", None),
            ]
        elif scene in {"away", "sleep"}:
            actions = [
                ("livingroom_light", "turn_off", None),
                ("livingroom_curtain", "turn_off", None),
                ("livingroom_ac", "turn_off", None),
            ]
        else:
            if fallback is not None:
                return fallback(args, context)
            return {"status": "error", "data": {}, "message": f"ESPHome 暂不支持场景 {scene}"}

        fallback_result = fallback(args, context) if fallback is not None else None
        results = []
        for device_id, action, value in actions:
            results.append(
                self._device_control(
                    {"device_id": device_id, "action": action, "value": value},
                    context,
                )
            )
        context["state"]["active_scene"] = scene
        return {
            "status": "success",
            "data": {
                "scene": scene,
                "actions": results,
                "simulator_actions": (fallback_result or {}).get("data", {}).get("actions", []),
            },
            "message": f"{scene} 场景已通过 ESPHome 执行",
        }

    def _status(self, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        del args, context
        status = self.bridge.status()
        connected = sum(1 for item in status.values() if item.get("connected"))
        return {
            "status": "success" if connected == len(status) else "error",
            "data": {"nodes": status, "connected": connected, "total": len(status)},
            "message": f"ESPHome 已连接 {connected}/{len(status)} 个节点",
        }


_BRIDGES: dict[tuple[Any, ...], ESPHomeBridge] = {}
_BRIDGES_LOCK = threading.Lock()


def _shared_bridge(
    nodes: tuple[ESPHomeNode, ...],
    noise_psk: str,
    *,
    command_timeout: float,
) -> ESPHomeBridge:
    key = (
        tuple((node.host, node.port, node.expected_name) for node in nodes),
        noise_psk,
    )
    with _BRIDGES_LOCK:
        bridge = _BRIDGES.get(key)
        if bridge is None:
            bridge = ESPHomeBridge(nodes, noise_psk, command_timeout=command_timeout)
            _BRIDGES[key] = bridge
        return bridge


def _stop_bridges() -> None:
    with _BRIDGES_LOCK:
        bridges = list(_BRIDGES.values())
    for bridge in bridges:
        bridge.stop()


atexit.register(_stop_bridges)


def _entity_key(entity: Any) -> tuple[int, int]:
    return int(entity.key), int(getattr(entity, "device_id", 0))


def _primary_entity(device_type: str, entities: list[Any]) -> Any | None:
    expected = {
        "light": LightInfo,
        "cover": CoverInfo,
        "air_conditioner": ClimateInfo,
    }.get(device_type)
    return next((entity for entity in entities if expected and isinstance(entity, expected)), None)


def _resolve_device_id(args: dict[str, Any]) -> str | None:
    device = str(args.get("device") or "")
    room = str(args.get("room") or "")
    if room and room != "客厅":
        return None
    if "窗帘" in device:
        return "livingroom_curtain"
    if "空调" in device:
        return "livingroom_ac"
    if "灯" in device:
        return "livingroom_light"
    return None


def _primary_state(info: dict[str, Any]) -> Any:
    if info.get("type") == "cover":
        return info.get("position", 0)
    if info.get("type") == "presence":
        return info.get("occupied", False)
    return info.get("power", "unknown")


def _bounded_float(value: Any, minimum: float, maximum: float) -> float:
    parsed = float(value)
    if not minimum <= parsed <= maximum:
        raise ValueError(f"value must be between {minimum:g} and {maximum:g}")
    return parsed


def _finite_or_none(value: Any) -> float | None:
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


__all__ = ["ESPHomeBridge", "ESPHomeIntegration", "ESPHomeNode", "default_nodes"]
