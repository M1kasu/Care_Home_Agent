"""Integration lifecycle for the embedded home runtime."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .runtime import HomeRuntime


class Integration(Protocol):
    domain: str

    def setup(self, runtime: "HomeRuntime") -> None: ...


class IntegrationManager:
    def __init__(self) -> None:
        self._integrations: dict[str, Integration] = {}

    def register(self, integration: Integration) -> None:
        if integration.domain in self._integrations:
            raise ValueError(f"integration already registered: {integration.domain}")
        self._integrations[integration.domain] = integration

    def setup_all(self, runtime: "HomeRuntime") -> list[str]:
        loaded: list[str] = []
        for domain, integration in self._integrations.items():
            integration.setup(runtime)
            loaded.append(domain)
        return loaded

    def domains(self) -> list[str]:
        return list(self._integrations)
