"""Built-in embedded runtime integrations."""

from .esphome import ESPHomeIntegration
from .simulator import SimulatorIntegration

__all__ = ["ESPHomeIntegration", "SimulatorIntegration"]
