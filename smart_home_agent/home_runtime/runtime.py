"""Composition root for the embedded home runtime."""

from __future__ import annotations

from typing import Any

from .care_policy import CarePolicyEngine
from .event_bus import EventBus
from .integration import Integration, IntegrationManager
from .models import utc_now
from .registries import AreaRegistry, DeviceRegistry, EntityRegistry
from .scheduler import Scheduler
from .service_registry import ServiceRegistry
from .state_machine import StateMachine


class HomeRuntimeFacade:
    """Narrow API exposed to Agent tools and application services."""

    def __init__(self, runtime: HomeRuntime) -> None:
        self._runtime = runtime

    @property
    def root_state(self) -> dict[str, Any]:
        return self._runtime.root_state

    @property
    def state_machine(self) -> StateMachine:
        return self._runtime.states

    @property
    def states(self) -> StateMachine:
        return self._runtime.states

    @property
    def entities(self) -> EntityRegistry:
        return self._runtime.entities

    @property
    def devices(self) -> DeviceRegistry:
        return self._runtime.devices

    @property
    def areas(self) -> AreaRegistry:
        return self._runtime.areas

    @property
    def scheduler(self) -> Scheduler:
        return self._runtime.scheduler

    @property
    def care_policy(self) -> CarePolicyEngine:
        return self._runtime.care_policy

    def call_service(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._runtime.call_service(name, args or {})

    def subscribe(self, event_type: str, handler: Any) -> Any:
        return self._runtime.events.subscribe(event_type, handler)

    def schedule(self, service: str, args: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return self._runtime.scheduler.schedule(service, args, **kwargs)


class HomeRuntime:
    def __init__(self, root_state: dict[str, Any]) -> None:
        self.root_state = root_state
        runtime_state = root_state.setdefault("runtime", {})
        runtime_state.setdefault("schema_version", 1)
        self.events = EventBus(runtime_state.setdefault("events", []))
        self.services = ServiceRegistry(runtime_state.setdefault("service_calls", []))
        self.states = StateMachine(runtime_state.setdefault("entity_states", {}), self.events)
        self.entities = EntityRegistry(runtime_state.setdefault("entities", {}))
        self.devices = DeviceRegistry(runtime_state.setdefault("devices", {}))
        self.areas = AreaRegistry(runtime_state.setdefault("areas", {}))
        self.scheduler = Scheduler(runtime_state.setdefault("scheduled_jobs", []), self.services)
        self.integrations = IntegrationManager()
        self.facade = HomeRuntimeFacade(self)
        self.care_policy = CarePolicyEngine(self)
        self._started = False

    @property
    def context(self) -> dict[str, Any]:
        return {
            "state": self.root_state,
            "runtime": self.facade,
            "event_bus": self.events,
            "state_machine": self.states,
            "scheduler": self.scheduler,
        }

    def add_integration(self, integration: Integration) -> None:
        self.integrations.register(integration)

    def start(self) -> None:
        if self._started:
            return
        self.care_policy.install()
        loaded = self.integrations.setup_all(self)
        runtime_state = self.root_state["runtime"]
        runtime_state["loaded_integrations"] = loaded
        runtime_state["started_at"] = utc_now()
        self._started = True
        self.events.fire("runtime_ready", {"integrations": loaded})
        self.tick()

    def tick(self) -> list[dict[str, Any]]:
        executed = self.scheduler.run_due(self.context)
        if executed:
            self.events.fire("scheduled_jobs_executed", {"jobs": executed})
        return executed

    def call_service(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        result = self.services.call(name, args, self.context)
        self.events.fire(
            "service_called",
            {"service": name, "args": dict(args), "status": result.get("status", "success")},
        )
        return result

    def snapshot(self) -> dict[str, Any]:
        runtime_state = self.root_state.get("runtime", {})
        return {
            "loaded_integrations": list(runtime_state.get("loaded_integrations", [])),
            "service_count": len(self.services.list_services()),
            "entity_count": len(self.entities.all()),
            "device_count": len(self.devices.all()),
            "pending_jobs": len(self.scheduler.pending()),
            "event_count": len(runtime_state.get("events", [])),
        }
