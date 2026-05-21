"""Contest-side wrapper for environments that import algorithm/main.py."""

from __future__ import annotations

try:
    from .smart_home_agent import run
except ImportError:  # pragma: no cover
    from smart_home_agent import run  # type: ignore


__all__ = ["run"]
