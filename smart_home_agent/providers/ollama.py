"""Minimal optional Ollama adapter using the native API, not /v1."""

from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from typing import Any


class OllamaClient:
    def __init__(
        self,
        *,
        base_url: str,
        chat_model: str,
        embedding_model: str,
        timeout_s: float = 1.2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.timeout_s = timeout_s

    def classify_intent(self, text: str, context: str = "") -> dict[str, Any] | None:
        prompt = (
            "你是家庭端侧智能体的轻量意图识别器。只输出 JSON，不要解释。"
            "字段为 name, confidence, slots。name 只能是 scene_mode_apply, device_control, "
            "network_diagnose, network_apply_qos, reminder_create, reminder_query, "
            "knowledge_query, home_status_query, unknown。\n"
            f"会话上下文：{context}\n用户输入：{text}"
        )
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_ctx": 1024},
        }
        try:
            response = self._post_json("/api/chat", payload)
            content = response.get("message", {}).get("content", "")
            return self._parse_json_object(content)
        except (OSError, ValueError, urllib.error.URLError, TimeoutError):
            return None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = {"model": self.embedding_model, "input": texts}
        response = self._post_json("/api/embed", payload)
        embeddings = response.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise ValueError("Ollama embed response missing embeddings")
        return [self._normalize(vec) for vec in embeddings]

    def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{endpoint}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("no json object found")
        parsed = json.loads(text[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("json is not an object")
        return parsed

    @staticmethod
    def _normalize(vec: Any) -> list[float]:
        if not isinstance(vec, list):
            raise ValueError("embedding is not a list")
        sanitized = [float(value) if isinstance(value, (int, float)) and math.isfinite(value) else 0.0 for value in vec]
        magnitude = math.sqrt(sum(value * value for value in sanitized))
        if magnitude < 1e-10:
            return sanitized
        return [value / magnitude for value in sanitized]
