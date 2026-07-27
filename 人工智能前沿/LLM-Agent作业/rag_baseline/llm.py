from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any

from .prompt import build_prompt
from .retriever import RetrievedDocument


class RAGLLMError(RuntimeError):
    pass


def _load_env() -> None:
    path = os.environ.get("RAG_PROJECT_ROOT")
    if path:
        env_path = os.path.join(path, ".env")
    else:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    for raw_line in open(env_path, encoding="utf-8"):
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class RAGLLMClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout: float = 45.0) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.strip().rstrip("/")
        self.model = model.strip()
        self.timeout = timeout
        if not self.api_key or not self.base_url or not self.model:
            raise RAGLLMError("需要配置 LLM_API_KEY、LLM_BASE_URL 和 LLM_MODEL")

    @classmethod
    def from_env(cls) -> RAGLLMClient:
        _load_env()
        return cls(
            os.environ.get("LLM_API_KEY", ""),
            os.environ.get("LLM_BASE_URL", ""),
            os.environ.get("LLM_MODEL", ""),
        )

    @property
    def endpoint(self) -> str:
        return self.base_url if self.base_url.endswith("/chat/completions") else f"{self.base_url}/chat/completions"

    def generate(self, user_text: str, retrieved: list[RetrievedDocument]) -> Any:
        payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "你只输出有效 JSON，不输出 Markdown。"},
                {"role": "user", "content": build_prompt(user_text, retrieved)},
            ],
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
                context=ssl.create_default_context(),
            ) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            raise RAGLLMError(f"RAG LLM request failed: {exc}") from exc
        try:
            content = response_payload["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("content is not text")
            candidate = content.strip()
            if candidate.startswith("```"):
                candidate = "\n".join(candidate.splitlines()[1:-1]).strip()
            return json.loads(candidate)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RAGLLMError(f"RAG LLM response is not valid JSON: {exc}") from exc
