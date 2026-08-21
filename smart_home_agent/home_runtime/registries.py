"""Entity, device and area registries persisted in the returned state."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import AreaRecord, DeviceRecord, EntityRecord


class EntityRegistry:
    def __init__(self, records: dict[str, dict[str, Any]]) -> None:
        self._records = records

    def register(self, record: EntityRecord) -> None:
        self._records[record.entity_id] = record.to_dict()

    def get(self, entity_id: str) -> dict[str, Any] | None:
        value = self._records.get(entity_id)
        return deepcopy(value) if value else None

    def all(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._records)


class DeviceRegistry:
    def __init__(self, records: dict[str, dict[str, Any]]) -> None:
        self._records = records

    def register(self, record: DeviceRecord) -> None:
        self._records[record.device_id] = record.to_dict()

    def all(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._records)


class AreaRegistry:
    def __init__(self, records: dict[str, dict[str, Any]]) -> None:
        self._records = records

    def register(self, record: AreaRecord) -> None:
        self._records[record.area_id] = record.to_dict()

    def all(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._records)
