from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

from travel_agent.agent.prompts import TRAVEL_REQUEST_SYSTEM_PROMPT
from travel_agent.config import AppConfig
from travel_agent.models import ModelValidationError, TravelRequest


class LLMClientError(RuntimeError):
    """Raised when a natural-language request cannot be parsed safely."""


JSONRequester = Callable[[str, Mapping[str, str], bytes, float], Mapping[str, Any]]


class OpenAICompatibleClient:
    """Minimal OpenAI-compatible chat-completions client using urllib."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        *,
        timeout: float = 30.0,
        requester: JSONRequester | None = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.strip().rstrip("/")
        self.model = model.strip()
        self.timeout = timeout
        if not self.api_key or not self.base_url or not self.model:
            raise ValueError("LLM api_key, base_url and model are required")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._requester = requester or self._request_json

    @classmethod
    def from_config(cls, config: AppConfig, **kwargs: Any) -> OpenAICompatibleClient:
        if not config.llm_api_key or not config.llm_base_url or not config.llm_model:
            raise LLMClientError(
                "请在 .env 中同时配置 LLM_API_KEY、LLM_BASE_URL 和 LLM_MODEL"
            )
        return cls(
            config.llm_api_key,
            config.llm_base_url,
            config.llm_model,
            **kwargs,
        )

    @property
    def endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def parse_travel_request(self, user_text: str) -> TravelRequest:
        text = user_text.strip()
        if not text:
            raise LLMClientError("旅行需求不能为空")
        payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": TRAVEL_REQUEST_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            response = self._requester(
                self.endpoint,
                headers,
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                self.timeout,
            )
            content = response["choices"][0]["message"]["content"]
            raw_request = self._extract_json(content)
            if not isinstance(raw_request, Mapping):
                raise LLMClientError("大模型返回的旅行需求不是 JSON 对象")
            return TravelRequest.from_mapping(raw_request)
        except LLMClientError:
            raise
        except (KeyError, IndexError, TypeError, ModelValidationError) as exc:
            raise LLMClientError(f"无法解析大模型返回的旅行需求：{exc}") from exc

    @staticmethod
    def _extract_json(content: Any) -> Mapping[str, Any]:
        if not isinstance(content, str):
            raise LLMClientError("大模型响应 content 不是字符串")
        candidate = content.strip()
        if candidate.startswith("```"):
            lines = candidate.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            candidate = "\n".join(lines).strip()
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            start, end = candidate.find("{"), candidate.rfind("}")
            if start < 0 or end <= start:
                raise LLMClientError("大模型没有返回有效 JSON")
            try:
                parsed = json.loads(candidate[start : end + 1])
            except json.JSONDecodeError as exc:
                raise LLMClientError(f"大模型返回的 JSON 无法解析：{exc}") from exc
        if not isinstance(parsed, Mapping):
            raise LLMClientError("大模型返回的顶层 JSON 必须是对象")
        return parsed

    @staticmethod
    def _request_json(
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> Mapping[str, Any]:
        request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout,
                context=ssl.create_default_context(),
            ) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise LLMClientError(f"LLM HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise LLMClientError(f"LLM 网络请求失败：{exc}") from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMClientError("LLM 接口没有返回有效 JSON") from exc
        if not isinstance(payload, Mapping):
            raise LLMClientError("LLM 接口响应必须是 JSON 对象")
        return payload
