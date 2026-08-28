"""Contest-side wrapper for environments that import algorithm/main.py."""

from __future__ import annotations

import sys

try:
    from .smart_home_agent import run
except ImportError:  # pragma: no cover
    from smart_home_agent import run  # type: ignore


__all__ = ["run"]


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]).strip() or "家里现在状态怎么样？"
    print(run(prompt)["reply"])
