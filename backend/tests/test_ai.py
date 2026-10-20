import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import AppError, ServiceUnavailable
from app.modules.ai.client import Message, OllamaClient, get_llm
from app.modules.ai.service import parse_drafts, strip_echoed_fields
from app.modules.workspaces.models import Role
from tests.conftest import Account, AddMember, BoardFixture, RegisterUser


class FakeLLM:
    """Records prompts and replays canned answers instead of calling Ollama."""

    model = "fake-model"

    def __init__(self) -> None:
        self.calls: list[tuple[list[Message], dict[str, Any] | None]] = []
        self.reply = ""
        self.chunks: list[str | AppError] = ["Привет", ", мир"]
        self.fail: AppError | None = None

    async def available(self) -> bool:
        return True

    async def complete(
        self, messages: list[Message], *, schema: dict[str, Any] | None = None
    ) -> str:
        self.calls.append((messages, schema))
        if self.fail:
            raise self.fail
        return self.reply

    async def stream(self, messages: list[Message]) -> AsyncIterator[str]:
        self.calls.append((messages, None))
        if self.fail:
            raise self.fail
        for chunk in self.chunks:
            if isinstance(chunk, AppError):
                raise chunk
            yield chunk


@pytest.fixture
def llm(app: FastAPI) -> FakeLLM:
    fake = FakeLLM()
    app.dependency_overrides[get_llm] = lambda: fake
    return fake


async def _task(client: httpx.AsyncClient, account: Account, column_id: str, **body):
    response = await client.post(f"/columns/{column_id}/tasks", json=body, headers=account.headers)
    assert response.status_code == 201, response.text
    return response.json()


def _chat_body(text: str = "Что просрочено?") -> dict:
    return {"messages": [{"role": "user", "content": text}]}


def _lines(response: httpx.Response) -> list[dict]:
    return [json.loads(line) for line in response.text.splitlines()]


# --- status ---------------------------------------------------------------------------


async def test_status_reports_disabled(
    client: httpx.AsyncClient, owner: Account, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(get_settings(), "ai_enabled", False)
    response = await client.get("/ai/status", headers=owner.headers)
    assert response.json() == {
        "enabled": False,
        "available": False,
        "model": get_settings().ollama_model,
    }


async def test_status_reports_unreachable_ollama(
    client: httpx.AsyncClient, owner: Account, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(get_settings(), "ollama_base_url", "http://127.0.0.1:9")
    body = (await client.get("/ai/status", headers=owner.headers)).json()
    assert body["enabled"] is True
    assert body["available"] is False


async def test_status_requires_auth(client: httpx.AsyncClient):
    assert (await client.get("/ai/status")).status_code == 401


async def test_endpoints_return_503_when_disabled(
    client: httpx.AsyncClient,
    owner: Account,
    board: BoardFixture,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(get_settings(), "ai_enabled", False)
    response = await client.post(
        f"/boards/{board.id}/ai/chat", json=_chat_body(), headers=owner.headers
    )
    assert response.status_code == 503
    assert response.json()["code"] == "ai_disabled"


# --- chat -----------------------------------------------------------------------------


async def test_chat_streams_ndjson_with_board_context(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture, llm: FakeLLM
):
    await _task(
        client, owner, board.column_ids[0], title="Сверстать лендинг", due_date="2000-01-01"
    )
    history = [
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "Здравствуйте!"},
        {"role": "user", "content": "Что просрочено?"},
    ]
    response = await client.post(
        f"/boards/{board.id}/ai/chat", json={"messages": history}, headers=owner.headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert _lines(response) == [{"delta": "Привет"}, {"delta": ", мир"}, {"done": True}]
    messages, _ = llm.calls[0]
    assert messages[0]["role"] == "system"
    assert "Доска «Roadmap»" in messages[0]["content"]
    assert "Колонка «To do» — задач: 1." in messages[0]["content"]
    assert "Сверстать лендинг" in messages[0]["content"]
    assert "просрочено" in messages[0]["content"]
    assert messages[1:] == history


async def test_chat_mid_stream_error_is_reported_in_stream(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture, llm: FakeLLM
):
    llm.chunks = ["Начало", ServiceUnavailable("Локальная модель недоступна", "ai_unavailable")]
    response = await client.post(
        f"/boards/{board.id}/ai/chat", json=_chat_body(), headers=owner.headers
    )
    assert response.status_code == 200
    assert _lines(response) == [
        {"delta": "Начало"},
        {"error": "Локальная модель недоступна", "code": "ai_unavailable"},
    ]


async def test_chat_error_before_first_chunk_is_http_error(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture, llm: FakeLLM
):
    llm.fail = ServiceUnavailable("Локальная модель недоступна", "ai_unavailable")
    response = await client.post(
        f"/boards/{board.id}/ai/chat", json=_chat_body(), headers=owner.headers
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Локальная модель недоступна", "code": "ai_unavailable"}


async def test_chat_last_message_must_be_from_user(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture, llm: FakeLLM
):
    response = await client.post(
        f"/boards/{board.id}/ai/chat",
        json={"messages": [{"role": "assistant", "content": "hi"}]},
        headers=owner.headers,
    )
    assert response.status_code == 422
    assert llm.calls == []


async def test_chat_roles(
    client: httpx.AsyncClient,
    register_user: RegisterUser,
    add_member: AddMember,
    owner: Account,
    board: BoardFixture,
    llm: FakeLLM,
):
    stranger = await register_user("stranger")
    viewer = await register_user("viewer")
    await add_member(owner, viewer, Role.viewer)
    url = f"/boards/{board.id}/ai/chat"

    assert (await client.post(url, json=_chat_body(), headers=stranger.headers)).status_code == 404
    assert (await client.post(url, json=_chat_body(), headers=viewer.headers)).status_code == 200


# --- generate tasks -------------------------------------------------------------------


async def test_generate_tasks_returns_drafts_without_creating_tasks(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture, llm: FakeLLM
):
    llm.reply = json.dumps(
        {
            "tasks": [
                {
                    "title": "Собрать требования",
                    "description": "Опросить команду",
                    "priority": "high",
                },
                {"title": "Нарисовать макет", "description": "", "priority": "nonsense"},
                {"title": "Лишняя", "description": "", "priority": "low"},
            ]
        }
    )
    response = await client.post(
        f"/boards/{board.id}/ai/generate-tasks",
        json={"prompt": "Запустить новый сайт", "count": 2},
        headers=owner.headers,
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "tasks": [
            {"title": "Собрать требования", "description": "Опросить команду", "priority": "high"},
            {"title": "Нарисовать макет", "description": "", "priority": "medium"},
        ]
    }
    messages, schema = llm.calls[0]
    assert schema is not None and "tasks" in schema["properties"]
    assert "2 конкретных задач" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "Запустить новый сайт"}
    board_body = (await client.get(f"/boards/{board.id}", headers=owner.headers)).json()
    assert all(c["tasks"] == [] for c in board_body["columns"])


async def test_generate_tasks_bad_model_output_is_502(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture, llm: FakeLLM
):
    llm.reply = "Конечно! Вот задачи: ..."
    response = await client.post(
        f"/boards/{board.id}/ai/generate-tasks",
        json={"prompt": "Запустить новый сайт"},
        headers=owner.headers,
    )
    assert response.status_code == 502
    assert response.json()["code"] == "ai_bad_response"


async def test_generate_tasks_requires_member(
    client: httpx.AsyncClient,
    register_user: RegisterUser,
    add_member: AddMember,
    owner: Account,
    board: BoardFixture,
    llm: FakeLLM,
):
    viewer = await register_user("viewer")
    await add_member(owner, viewer, Role.viewer)
    response = await client.post(
        f"/boards/{board.id}/ai/generate-tasks",
        json={"prompt": "Запустить новый сайт"},
        headers=viewer.headers,
    )
    assert response.status_code == 403
    assert llm.calls == []


async def test_generate_tasks_validates_count(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture, llm: FakeLLM
):
    response = await client.post(
        f"/boards/{board.id}/ai/generate-tasks",
        json={"prompt": "Запустить новый сайт", "count": 50},
        headers=owner.headers,
    )
    assert response.status_code == 422


# --- description ----------------------------------------------------------------------


async def test_suggest_description(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture, llm: FakeLLM
):
    task = await _task(
        client, owner, board.column_ids[0], title="Настроить CI", description="Сейчас нет CI"
    )
    llm.reply = "Название: Настроить CI\n\nНужно настроить CI.\nЧто сделать:\n- GitHub Actions"
    response = await client.post(f"/tasks/{task['id']}/ai/description", headers=owner.headers)

    assert response.status_code == 200, response.text
    assert response.json() == {"description": "Нужно настроить CI.\nЧто сделать:\n- GitHub Actions"}
    prompt = llm.calls[0][0][1]["content"]
    assert "Название: Настроить CI" in prompt
    assert "Сейчас нет CI" in prompt
    unchanged = (await client.get(f"/tasks/{task['id']}", headers=owner.headers)).json()
    assert unchanged["description"] == "Сейчас нет CI"


async def test_suggest_description_roles(
    client: httpx.AsyncClient,
    register_user: RegisterUser,
    add_member: AddMember,
    owner: Account,
    board: BoardFixture,
    llm: FakeLLM,
):
    task = await _task(client, owner, board.column_ids[0], title="Настроить CI")
    stranger = await register_user("stranger")
    viewer = await register_user("viewer")
    await add_member(owner, viewer, Role.viewer)
    url = f"/tasks/{task['id']}/ai/description"

    assert (await client.post(url, headers=stranger.headers)).status_code == 404
    assert (await client.post(url, headers=viewer.headers)).status_code == 403
    assert llm.calls == []


# --- pure helpers ---------------------------------------------------------------------


def test_parse_drafts_clips_long_titles_and_skips_garbage():
    raw = json.dumps({"tasks": [{"title": "x" * 300}, "junk", {"title": "  "}]})
    drafts = parse_drafts(raw, limit=5)
    assert len(drafts) == 1
    assert len(drafts[0].title) == 200


def test_strip_echoed_fields_keeps_body():
    assert strip_echoed_fields("Приоритет: высокий\nСрок: 2030-01-01\n\nТекст") == "Текст"
    assert strip_echoed_fields("Текст\nСрок: позже") == "Текст\nСрок: позже"


# --- Ollama client against a mocked HTTP transport ------------------------------------


def _ollama(handler) -> OllamaClient:
    return OllamaClient("http://ollama", "qwen2.5:3b", 5, transport=httpx.MockTransport(handler))


async def test_ollama_available_checks_installed_model():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": "qwen2.5:3b"}]})

    assert await _ollama(handler).available() is True

    def other(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": "llama3.2:latest"}]})

    assert await _ollama(other).available() is False


async def test_ollama_stream_parses_ndjson():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "qwen2.5:3b"
        lines = [
            {"message": {"content": "При"}, "done": False},
            {"message": {"content": "вет"}, "done": False},
            {"message": {"content": ""}, "done": True},
        ]
        return httpx.Response(200, text="\n".join(json.dumps(line) for line in lines))

    chunks = [c async for c in _ollama(handler).stream([{"role": "user", "content": "hi"}])]
    assert chunks == ["При", "вет"]


async def test_ollama_complete_passes_schema():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["stream"] is False
        assert payload["format"] == {"type": "object"}
        return httpx.Response(200, json={"message": {"content": '{"ok": true}'}})

    reply = await _ollama(handler).complete([], schema={"type": "object"})
    assert reply == '{"ok": true}'


@pytest.mark.parametrize(
    ("response", "code"),
    [
        (httpx.Response(404, json={"error": "model 'qwen2.5:3b' not found"}), "ai_model_missing"),
        (httpx.Response(500, json={"error": "out of memory"}), "ai_error"),
    ],
)
async def test_ollama_http_errors_map_to_app_errors(response: httpx.Response, code: str):
    client = _ollama(lambda _: response)
    with pytest.raises(AppError) as complete_error:
        await client.complete([])
    assert complete_error.value.code == code
    with pytest.raises(AppError) as stream_error:
        _ = [c async for c in client.stream([])]
    assert stream_error.value.code == code


async def test_ollama_connection_and_timeout_errors():
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(AppError) as unavailable:
        await _ollama(refuse).complete([])
    assert unavailable.value.code == "ai_unavailable"
    with pytest.raises(AppError) as timeout:
        _ = [c async for c in _ollama(slow).stream([])]
    assert timeout.value.code == "ai_timeout"
