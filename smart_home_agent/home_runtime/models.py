"""Serializable runtime models shared by the embedded home kernel."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class RuntimeEvent:
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EntityRecord:
    entity_id: str
    domain: str
    name: str
    device_id: str | None = None
    area_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DeviceRecord:
    device_id: str
    name: str
    manufacturer: str = "simulator"
    model: str = "virtual"
    area_id: str | None = None
    integration: str = "simulator"
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AreaRecord:
    area_id: str
    name: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
