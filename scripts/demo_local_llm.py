"""Stable local-LLM defense demo.

This script forces the router through the embedded Qwen model so a reviewer can
verify that the GGUF model is actually loaded and used instead of rule-only
matching.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import run  # noqa: E402


PROMPTS = [
    "老人那边视频总是一顿一顿的，先看看是不是网络问题。",
]


def main() -> None:
    state = None
    config = {"mode": "llm", "force_local_llm": True, "enable_local_llm": True, "llm_max_tokens": 96}
    for prompt in PROMPTS:
        result = run(prompt, state=state, config=config)
        state = result["state"]
        print("=" * 80)
        print("User:", prompt)
        print("Reply:", result["reply"])
        print("Intent:", result["intent"]["name"], "source=", result["intent"]["source"])
        print("Reason:", result["intent"]["reasoning"])
        print("Model metrics:", json.dumps({
            "attempted": result["metrics"]["model_attempted"],
            "available": result["metrics"]["model_available"],
            "latency_ms": result["metrics"]["model_latency_ms"],
            "error": result["metrics"]["model_error"],
            "raw": result["metrics"]["model_raw_output"],
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
