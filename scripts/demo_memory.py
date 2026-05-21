"""Quick demo for multi-turn fallback memory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import run  # noqa: E402


def main() -> None:
    state = None
    for text in ["怎么做可乐鸡翅", "什么步骤"]:
        result = run(text, state=state)
        state = result["state"]
        print("=" * 60)
        print("User:", text)
        print("Intent:", result["intent"]["name"], "source=", result["intent"]["source"])
        print("Reply:", result["reply"])


if __name__ == "__main__":
    main()
