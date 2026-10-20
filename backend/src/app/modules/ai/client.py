import json
from collections.abc import AsyncIterator
from typing import Any, Protocol

import httpx

from app.core.config import Settings, get_settings
from app.core.errors import BadGateway, GatewayTimeout, ServiceUnavailable

Message = dict[str, str]


class LLMClient(Protocol):
    model: str

    async def available(self) -> bool: ...

    async def complete(
        self, messages: list[Message], *, schema: dict[str, Any] | None = None
    ) -> str: ...

    def stream(self, messages: list[Message]) -> AsyncIterator[str]: ...


def _model_matches(installed: str, wanted: str) -> bool:
    """Ollama reports untagged models as `name:latest`."""
    return installed == wanted or installed == f"{wanted}:latest"


class OllamaClient:
    """Thin async wrapper over the Ollama HTTP API (https://docs.ollama.com/api)."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = httpx.Timeout(timeout, connect=5.0)
        self.transport = transport

    def _client(self, timeout: httpx.Timeout | None = None) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url, timeout=timeout or self.timeout, transport=self.transport
        )

    async def available(self) -> bool:
        try:
            async with self._client(httpx.Timeout(3.0)) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
        except httpx.HTTPError:
            return False
        names = [m.get("name", "") for m in response.json().get("models", [])]
        return any(_model_matches(name, self.model) for name in names)

    def _payload(self, messages: list[Message], **extra: Any) -> dict[str, Any]:
        return {"model": self.model, "messages": messages, **extra}

    def _raise_for_status(self, response: httpx.Response, body: bytes) -> None:
        if response.is_success:
            return
        try:
            error = json.loads(body).get("error", "")
        except ValueError:
            error = body.decode(errors="replace")[:200]
        if response.status_code == 404:
            raise ServiceUnavailable(
                f"Модель «{self.model}» не установлена. Выполните: ollama pull {self.model}",
                "ai_model_missing",
            )
        raise BadGateway(f"Ollama вернула ошибку: {error or response.status_code}", "ai_error")

    async def complete(
        self, messages: list[Message], *, schema: dict[str, Any] | None = None
    ) -> str:
        payload = self._payload(messages, stream=False)
        if schema is not None:
            payload["format"] = schema
            payload["options"] = {"temperature": 0.2}
        try:
            async with self._client() as client:
                response = await client.post("/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            raise GatewayTimeout("Модель не ответила вовремя", "ai_timeout") from exc
        except httpx.HTTPError as exc:
            raise ServiceUnavailable("Локальная модель недоступна", "ai_unavailable") from exc
        self._raise_for_status(response, response.content)
        return response.json().get("message", {}).get("content", "")

    async def stream(self, messages: list[Message]) -> AsyncIterator[str]:
        try:
            async with (
                self._client() as client,
                client.stream("POST", "/api/chat", json=self._payload(messages)) as response,
            ):
                if not response.is_success:
                    self._raise_for_status(response, await response.aread())
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    if error := chunk.get("error"):
                        raise BadGateway(f"Ollama вернула ошибку: {error}", "ai_error")
                    if content := chunk.get("message", {}).get("content"):
                        yield content
        except httpx.TimeoutException as exc:
            raise GatewayTimeout("Модель не ответила вовремя", "ai_timeout") from exc
        except httpx.HTTPError as exc:
            raise ServiceUnavailable("Локальная модель недоступна", "ai_unavailable") from exc


def get_llm() -> LLMClient:
    settings: Settings = get_settings()
    if not settings.ai_enabled:
        raise ServiceUnavailable("ИИ-ассистент отключён", "ai_disabled")
    return OllamaClient(
        settings.ollama_base_url, settings.ollama_model, settings.ollama_timeout_seconds
    )
