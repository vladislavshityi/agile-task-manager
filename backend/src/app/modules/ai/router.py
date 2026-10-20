import json
import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.deps import CurrentUser, SessionDep
from app.core.errors import AppError
from app.modules.ai.client import LLMClient, OllamaClient, get_llm
from app.modules.ai.schemas import (
    AIStatus,
    ChatRequest,
    DescriptionSuggestion,
    GenerateTasksRequest,
    GenerateTasksResponse,
)
from app.modules.ai.service import AIService

router = APIRouter(tags=["ai"])
LLMDep = Annotated[LLMClient, Depends(get_llm)]


def _line(payload: dict[str, str | bool]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode()


async def _ndjson(first: str, rest: AsyncIterator[str]) -> AsyncIterator[bytes]:
    """NDJSON: `{"delta": ...}` lines, then `{"done": true}` or `{"error": ..., "code": ...}`."""
    yield _line({"delta": first})
    try:
        async for chunk in rest:
            yield _line({"delta": chunk})
    except AppError as exc:
        yield _line({"error": exc.detail, "code": exc.code})
        return
    yield _line({"done": True})


@router.get("/ai/status", response_model=AIStatus)
async def ai_status(_: CurrentUser) -> AIStatus:
    settings = get_settings()
    if not settings.ai_enabled:
        return AIStatus(enabled=False, available=False, model=settings.ollama_model)
    llm = get_llm()
    available = await llm.available() if isinstance(llm, OllamaClient) else True
    return AIStatus(enabled=True, available=available, model=llm.model)


@router.post("/boards/{board_id}/ai/chat")
async def board_chat(
    board_id: uuid.UUID, data: ChatRequest, user: CurrentUser, session: SessionDep, llm: LLMDep
) -> StreamingResponse:
    chunks = await AIService(session, llm).chat(user, board_id, data.messages)
    # Pull the first chunk before answering so connection/model errors become proper 5xx.
    first = await anext(aiter(chunks), "")
    return StreamingResponse(
        _ndjson(first, chunks),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/boards/{board_id}/ai/generate-tasks", response_model=GenerateTasksResponse)
async def generate_tasks(
    board_id: uuid.UUID,
    data: GenerateTasksRequest,
    user: CurrentUser,
    session: SessionDep,
    llm: LLMDep,
) -> GenerateTasksResponse:
    return await AIService(session, llm).generate_tasks(user, board_id, data.prompt, data.count)


@router.post("/tasks/{task_id}/ai/description", response_model=DescriptionSuggestion)
async def suggest_description(
    task_id: uuid.UUID, user: CurrentUser, session: SessionDep, llm: LLMDep
) -> DescriptionSuggestion:
    description = await AIService(session, llm).suggest_description(user, task_id)
    return DescriptionSuggestion(description=description)
