"""Local LLM provider using llama-cpp-python for embedded edge inference."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any


_CLIENT_CACHE: dict[tuple[Any, ...], "LocalLLMClient"] = {}
_CLIENT_CACHE_LOCK = threading.Lock()


class LocalLLMClient:
    """Lazy-loading local LLM client backed by llama-cpp-python.

    Falls back gracefully if the library or model file is missing.
    """

    def __init__(
        self,
        *,
        model_path: str,
        n_ctx: int = 1024,
        n_threads: int = 4,
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> None:
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_threads = n_threads
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._model: Any = None
        self._lock = threading.Lock()
        self._load_failed = False
        self._load_error = ""
        self._load_latency_ms = 0
        self._library_version = ""
        self.last_raw_output = ""
        self.last_cache_hit = False
        self._classify_cache: dict[str, tuple[str, dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Public API (compatible with former OllamaClient)
    # ------------------------------------------------------------------

    def classify_intent(self, text: str, context: str = "") -> dict[str, Any] | None:
        cache_key = text.strip()
        if cache_key in self._classify_cache:
            raw, parsed = self._classify_cache[cache_key]
            self.last_cache_hit = True
            self.last_raw_output = raw
            return dict(parsed)
        self.last_cache_hit = False
        prompt = (
            "<|im_start|>system\n"
            "你是家庭端侧智能体的轻量意图识别器。只输出 JSON，不要解释。"
            "字段为 name, confidence, slots。name 只能是 scene_mode_apply, device_control, "
            "network_diagnose, network_apply_qos, reminder_create, reminder_query, "
            "reminder_complete, reminder_cancel, knowledge_query, home_status_query, child_mode_apply, energy_query, "
            "sensor_query, proactive_alert, unknown。\n"
            "<|im_end|>\n"
            f"<|im_start|>user\n会话上下文：{context}\n用户输入：{text}\n<|im_end|>\n"
            "<|im_start|>assistant\n"
        )
        raw = self._generate(prompt, stop=["<|im_end|>", "\n\n"], max_tokens=80)
        self.last_raw_output = raw or ""
        if not raw:
            return None
        parsed = _parse_json_object(raw)
        if parsed is not None and str(parsed.get("name") or "") != "unknown":
            self._classify_cache[cache_key] = (raw, dict(parsed))
        return parsed

    def generate_reply(self, prompt: str) -> str | None:
        raw = self._generate(prompt, stop=["<|im_end|>"])
        self.last_raw_output = raw or ""
        return raw

    def embed(self, texts: list[str]) -> list[list[float]] | None:
        """Generate embeddings for a list of strings using llama.cpp.

        Returns None when the model is unavailable so that callers can fall back.
        """
        if not texts:
            return []
        model = self._ensure_model()
        if model is None:
            return None
        try:
            result = model.create_embedding(texts)
        except Exception:
            return None
        data = result.get("data") if isinstance(result, dict) else None
        if not data:
            return None
        out: list[list[float]] = []
        for item in data:
            vec = item.get("embedding") if isinstance(item, dict) else None
            if vec is None:
                return None
            # llama.cpp can return [[...]] for pooled output
            if vec and isinstance(vec[0], list):
                vec = vec[0]
            out.append([float(x) for x in vec])
        return out

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_model(self) -> Any:
        if self._model is not None or self._load_failed:
            return self._model
        with self._lock:
            if self._model is not None or self._load_failed:
                return self._model
            start = time.perf_counter()
            path = Path(self._model_path)
            if not path.exists():
                self._load_failed = True
                self._load_error = f"model file not found: {path}"
                return None
            try:
                import llama_cpp
                from llama_cpp import Llama

                self._library_version = getattr(llama_cpp, "__version__", "")
            except Exception as exc:
                self._load_failed = True
                self._load_error = f"{type(exc).__name__}: {exc}"
                return None
            try:
                self._model = Llama(
                    model_path=str(path),
                    n_ctx=self._n_ctx,
                    n_threads=self._n_threads,
                    n_gpu_layers=0,
                    verbose=False,
                )
            except Exception as exc:
                self._load_failed = True
                self._load_error = f"{type(exc).__name__}: {exc}"
                return None
            finally:
                self._load_latency_ms = int((time.perf_counter() - start) * 1000)
            return self._model

    def _generate(self, prompt: str, stop: list[str] | None = None, max_tokens: int | None = None) -> str | None:
        model = self._ensure_model()
        if model is None:
            return None
        try:
            result = model(
                prompt,
                max_tokens=max_tokens or self._max_tokens,
                temperature=self._temperature,
                stop=stop or ["<|im_end|>"],
            )
            choices = result.get("choices", [])
            if not choices:
                return None
            return choices[0].get("text", "").strip()
        except Exception:
            return None

    def status(self, *, load: bool = False) -> dict[str, Any]:
        """Return a small, UI-friendly status snapshot for defense demos."""
        if load:
            self._ensure_model()
        return {
            "available": self._model is not None,
            "load_failed": self._load_failed,
            "load_error": self._load_error,
            "load_latency_ms": self._load_latency_ms,
            "model_path": self._model_path,
            "library_version": self._library_version,
        }


def _parse_json_object(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


def get_cached_local_llm_client(config: dict[str, Any]) -> LocalLLMClient:
    key = (
        config.get("model_path"),
        int(config.get("n_ctx", 1024)),
        int(config.get("n_threads", 4)),
        float(config.get("llm_temperature", 0.0)),
        int(config.get("llm_max_tokens", 256)),
    )
    with _CLIENT_CACHE_LOCK:
        client = _CLIENT_CACHE.get(key)
        if client is None:
            client = LocalLLMClient(
                model_path=str(config["model_path"]),
                n_ctx=int(config.get("n_ctx", 1024)),
                n_threads=int(config.get("n_threads", 4)),
                temperature=float(config.get("llm_temperature", 0.0)),
                max_tokens=int(config.get("llm_max_tokens", 256)),
            )
            _CLIENT_CACHE[key] = client
        return client
