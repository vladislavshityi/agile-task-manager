"""End-to-end checks against a real Ollama: OLLAMA_LIVE=1 uv run pytest tests/test_ai_live.py"""

import json
import os

import httpx
import pytest

from tests.conftest import Account, BoardFixture

pytestmark = pytest.mark.skipif(
    os.environ.get("OLLAMA_LIVE") != "1", reason="set OLLAMA_LIVE=1 to call the local model"
)


async def test_live_status(client: httpx.AsyncClient, owner: Account):
    body = (await client.get("/ai/status", headers=owner.headers)).json()
    assert body["available"] is True, f"pull the model first: ollama pull {body['model']}"


async def test_live_chat_mentions_board_task(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    await client.post(
        f"/columns/{board.column_ids[0]}/tasks",
        json={"title": "Обновить политику конфиденциальности", "due_date": "2000-01-01"},
        headers=owner.headers,
    )
    response = await client.post(
        f"/boards/{board.id}/ai/chat",
        json={"messages": [{"role": "user", "content": "Какая задача просрочена?"}]},
        headers=owner.headers,
        timeout=180,
    )
    lines = [json.loads(line) for line in response.text.splitlines()]
    assert lines[-1] == {"done": True}
    reply = "".join(line.get("delta", "") for line in lines).lower()
    assert "политик" in reply


async def test_live_generate_tasks(client: httpx.AsyncClient, owner: Account, board: BoardFixture):
    response = await client.post(
        f"/boards/{board.id}/ai/generate-tasks",
        json={"prompt": "Провести опрос пользователей о новом дизайне", "count": 3},
        headers=owner.headers,
        timeout=180,
    )
    assert response.status_code == 200, response.text
    tasks = response.json()["tasks"]
    assert 1 <= len(tasks) <= 3
    assert all(t["title"] and t["priority"] in {"low", "medium", "high", "urgent"} for t in tasks)
