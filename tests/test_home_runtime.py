"""Contract tests for the embedded single-process home runtime."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from smart_home_agent.home_runtime import HomeRuntime  # noqa: E402
from smart_home_agent.home_runtime.integrations import SimulatorIntegration  # noqa: E402
from smart_home_agent.tools.home_tools import ensure_home_state  # noqa: E402


def _runtime() -> tuple[HomeRuntime, dict]:
    state = ensure_home_state(None)
    runtime = HomeRuntime(state)
    runtime.add_integration(SimulatorIntegration())
    runtime.start()
    return runtime, state


def test_runtime_registers_simulator_capabilities() -> None:
    runtime, state = _runtime()
    snapshot = runtime.snapshot()

    assert snapshot["loaded_integrations"] == ["simulator"]
    assert snapshot["service_count"] == 18
    assert snapshot["device_count"] == len(state["devices"])
    assert snapshot["entity_count"] == len(state["devices"]) + len(state["sensors"])
    assert runtime.services.has("device.control")
    assert runtime.services.has("sensor.update")


def test_sensor_state_change_drives_alert_lifecycle() -> None:
    runtime, state = _runtime()
    initial_types = {item["type"] for item in runtime.care_policy.active_alerts()}
    assert {"elderly_inactive", "elderly_low_temperature", "child_noise"} <= initial_types

    updated = runtime.call_service(
        "sensor.update",
        {"room": "老人房", "temperature": 24, "motion": True, "last_motion_min": 0},
    )
    assert updated["status"] == "success"
    active_types = {item["type"] for item in runtime.care_policy.active_alerts()}
    assert "elderly_inactive" not in active_types
    assert "elderly_low_temperature" not in active_types

    runtime.call_service(
        "sensor.update",
        {"room": "老人房", "motion": False, "last_motion_min": 130},
    )
    active_types = {item["type"] for item in runtime.care_policy.active_alerts()}
    assert "elderly_inactive" in active_types
    event_types = [item["event_type"] for item in state["runtime"]["events"]]
    assert "state_changed" in event_types
    assert "care_alert_resolved" in event_types
    assert "care_alert" in event_types


def test_scheduler_executes_due_device_action() -> None:
    runtime, state = _runtime()
    created = runtime.call_service(
        "device.set_timer",
        {"device_id": "livingroom_light", "minutes": 5, "action": "turn_off"},
    )
    assert created["status"] == "success"
    job_id = created["data"]["timer"]["job_id"]
    job = next(item for item in state["runtime"]["scheduled_jobs"] if item["id"] == job_id)
    job["run_at"] = "2000-01-01T00:00:00+00:00"

    executed = runtime.tick()

    assert executed and executed[0]["status"] == "completed"
    assert state["devices"]["livingroom_light"]["power"] == "off"
    assert runtime.states.get("light.livingroom_light")["state"] == "off"


def test_completing_reminder_cancels_retry_job() -> None:
    runtime, state = _runtime()
    created = runtime.call_service(
        "reminder.create",
        {"member": "爷爷", "task": "吃药", "retry_after_min": 10},
    )
    reminder = created["data"]["reminder"]
    assert reminder["retry_job_id"]

    completed = runtime.call_service("reminder.complete", {"reminder_id": reminder["id"]})

    assert completed["status"] == "success"
    job = next(
        item for item in state["runtime"]["scheduled_jobs"] if item["id"] == reminder["retry_job_id"]
    )
    assert job["status"] == "canceled"


if __name__ == "__main__":
    test_runtime_registers_simulator_capabilities()
    test_sensor_state_change_drives_alert_lifecycle()
    test_scheduler_executes_due_device_action()
    test_completing_reminder_cancels_retry_job()
    print("all home runtime tests passed")
