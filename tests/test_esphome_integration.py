"""Contract tests for the ESPHome Native API runtime overlay."""

from __future__ import annotations

from copy import deepcopy

from smart_home_agent.core.router import LocalRouter
from smart_home_agent.home_runtime import HomeRuntime
from smart_home_agent.home_runtime.integrations import (
    ESPHomeIntegration,
    SimulatorIntegration,
)
from smart_home_agent.home_runtime.integrations.esphome import default_nodes
from smart_home_agent.memory.session import SessionMemory
from smart_home_agent.pipeline import SmartHomeAgent
from smart_home_agent.tools.home_tools import ensure_home_state


class FakeESPHomeBridge:
    def __init__(self) -> None:
        self.nodes = default_nodes("192.168.111.134")
        self.commands: list[tuple[str, str, object]] = []
        self._devices = {
            "livingroom_light": {
                "name": "客厅灯",
                "room": "客厅",
                "type": "light",
                "source": "esphome",
                "available": True,
                "host": "192.168.111.134",
                "port": 6053,
                "power": "on",
                "brightness": 80,
            },
            "livingroom_curtain": {
                "name": "客厅窗帘",
                "room": "客厅",
                "type": "cover",
                "source": "esphome",
                "available": True,
                "host": "192.168.111.134",
                "port": 6054,
                "power": "open",
                "position": 100,
                "operation": "idle",
            },
            "livingroom_presence": {
                "name": "客厅人体存在",
                "room": "客厅",
                "type": "presence",
                "source": "esphome",
                "available": True,
                "host": "192.168.111.134",
                "port": 6056,
                "power": "on",
                "occupied": True,
            },
            "livingroom_ac": {
                "name": "客厅空调",
                "room": "客厅",
                "type": "air_conditioner",
                "source": "esphome",
                "available": True,
                "host": "192.168.111.134",
                "port": 6055,
                "power": "on",
                "mode": "cool",
                "action": "cooling",
                "temperature": 26.0,
                "current_temperature": 29.4,
            },
        }

    def start(self) -> None:
        return None

    def wait_ready(self, timeout: float) -> bool:
        del timeout
        return True

    def status(self) -> dict:
        return {
            node.device_id: {
                "connected": True,
                "host": node.host,
                "port": node.port,
                "error": "",
            }
            for node in self.nodes
        }

    def device_states(self) -> dict:
        return deepcopy(self._devices)

    def command(self, device_id: str, action: str, value: object = None) -> None:
        self.commands.append((device_id, action, value))
        device = self._devices[device_id]
        if action == "turn_off":
            device["power"] = "off" if device["type"] != "cover" else "closed"
            if device["type"] == "light":
                device["brightness"] = 0
            if device["type"] == "cover":
                device["position"] = 0
        elif action == "turn_on":
            device["power"] = "on" if device["type"] != "cover" else "open"
            if device["type"] == "cover":
                device["position"] = 100
        elif action == "set_brightness":
            device.update(power="on", brightness=int(value))
        elif action == "set_temperature":
            device.update(power="on", mode="cool", temperature=float(value))


def _runtime() -> tuple[HomeRuntime, dict, FakeESPHomeBridge]:
    state = ensure_home_state(None)
    bridge = FakeESPHomeBridge()
    runtime = HomeRuntime(state)
    runtime.add_integration(SimulatorIntegration())
    runtime.add_integration(ESPHomeIntegration(bridge))
    runtime.start()
    return runtime, state, bridge


def test_default_nodes_match_current_vm_port_mapping() -> None:
    ports = {node.expected_name: node.port for node in default_nodes("192.168.111.134")}

    assert ports == {
        "living-room-light": 6053,
        "living-room-curtain": 6054,
        "living-room-ac": 6055,
        "living-room-presence": 6056,
    }


def test_esphome_overlay_registers_real_entities_and_services() -> None:
    runtime, state, _ = _runtime()

    assert runtime.integrations.domains() == ["simulator", "esphome"]
    assert runtime.services.has("esphome.status")
    assert state["devices"]["livingroom_light"]["source"] == "esphome"
    assert state["devices"]["livingroom_tv"]["source"] == "simulator"
    assert state["devices"]["livingroom_curtain"]["position"] == 100
    assert state["sensors"]["客厅"]["temperature"] == 29.4
    assert state["sensors"]["客厅"]["sources"]["temperature"] == "esphome"
    assert state["sensors"]["客厅"]["sources"]["humidity"] == "simulator"
    assert runtime.states.get("binary_sensor.livingroom_presence")["state"] is True


def test_device_control_is_forwarded_to_esphome_and_read_back() -> None:
    runtime, state, bridge = _runtime()

    result = runtime.call_service(
        "device.control",
        {"room": "客厅", "device": "灯", "action": "set_brightness", "value": 20},
    )

    assert result["status"] == "success"
    assert bridge.commands[-1] == ("livingroom_light", "set_brightness", 20)
    assert state["devices"]["livingroom_light"]["brightness"] == 20
    assert runtime.states.get("light.livingroom_light")["attributes"]["source"] == "esphome"


def test_movie_scene_controls_three_real_esphome_nodes() -> None:
    runtime, state, bridge = _runtime()

    result = runtime.call_service("scene.apply", {"scene": "movie"})

    assert result["status"] == "success"
    assert bridge.commands == [
        ("livingroom_curtain", "turn_off", None),
        ("livingroom_light", "set_brightness", 15),
        ("livingroom_ac", "set_temperature", 26),
    ]
    assert state["devices"]["livingroom_tv"]["power"] == "on"


def test_non_esphome_device_and_scene_keep_simulator_fallback() -> None:
    runtime, state, bridge = _runtime()

    control = runtime.call_service(
        "device.control",
        {"device_id": "front_door_lock", "action": "lock"},
    )
    scene = runtime.call_service("scene.apply", {"scene": "child_study"})

    assert control["status"] == "success"
    assert state["devices"]["front_door_lock"]["locked"] is True
    assert scene["status"] == "success"
    assert state["devices"]["kids_room_light"]["brightness"] == 75
    assert bridge.commands == []


def test_router_recognizes_curtain_control() -> None:
    router = LocalRouter(SessionMemory())
    state = ensure_home_state(None)

    intent, _ = router.route("把客厅窗帘关上", state, {"enable_local_llm": False})

    assert intent.name == "device_control"
    assert intent.slots["device"] == "窗帘"
    assert intent.slots["action"] == "turn_off"


def test_agent_natural_language_reaches_esphome_bridge(tmp_path) -> None:
    bridge = FakeESPHomeBridge()
    agent = SmartHomeAgent(
        integration_factories=(
            SimulatorIntegration,
            lambda: ESPHomeIntegration(bridge),
        )
    )

    result = agent.run(
        "把客厅灯调到20%",
        config={
            "enable_local_llm": False,
            "sqlite_path": str(tmp_path / "esphome-agent.db"),
        },
    )

    assert result["intent"]["name"] == "device_control"
    assert result["tool_results"][0]["status"] == "success"
    assert bridge.commands[-1] == ("livingroom_light", "set_brightness", 20)
    assert result["state"]["devices"]["livingroom_light"]["brightness"] == 20


def test_home_status_reply_separates_real_and_simulated_devices(tmp_path) -> None:
    bridge = FakeESPHomeBridge()
    agent = SmartHomeAgent(
        integration_factories=(
            SimulatorIntegration,
            lambda: ESPHomeIntegration(bridge),
        )
    )

    result = agent.run(
        "家里现在状态怎么样？",
        config={
            "enable_local_llm": False,
            "sqlite_path": str(tmp_path / "esphome-status.db"),
        },
    )

    assert "4 个 ESPHome 真实设备" in result["reply"]
    assert "9 个模拟设备" in result["reply"]
