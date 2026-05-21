"""Small configuration helper for the contest demo."""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"

DEFAULT_CONFIG: dict[str, Any] = {
    "mode": "hybrid",
    "enable_local_llm": True,
    "model_path": os.getenv("LOCAL_LLM_MODEL_PATH", str(DATA_DIR / "qwen2.5-1.5b-instruct-q4_k_m.gguf")),
    "n_ctx": 1024,
    "n_threads": 4,
    "llm_temperature": 0.0,
    "llm_max_tokens": 192,
    "llm_min_confidence": 0.55,
    "force_local_llm": False,
    "sqlite_path": str(DATA_DIR / "smart_home.db"),
    "max_steps": 8,
    "require_confirm": True,
    "enable_embedding_search": False,
    "debug": False,
    "language": "zh-CN",
}


def merge_config(config: dict | None = None) -> dict[str, Any]:
    merged = deepcopy(DEFAULT_CONFIG)
    if config:
        merged.update(config)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return merged
