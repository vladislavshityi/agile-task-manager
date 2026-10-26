import uuid

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.wiki.schemas import (
    WikiPageCreate,
    WikiPageMove,
    WikiPageRead,
    WikiPageSummary,
    WikiPageUpdate,
)
from app.modules.wiki.service import WikiService

router = APIRouter(tags=["wiki"])
NO_CONTENT = status.HTTP_204_NO_CONTENT


@router.get("/workspaces/{workspace_id}/wiki", response_model=list[WikiPageSummary])
async def list_pages(
    workspace_id: uuid.UUID, user: CurrentUser, session: SessionDep, q: str | None = None
) -> list[WikiPageSummary]:
    pages = await WikiService(session).list_pages(user, workspace_id, q)
    return [WikiPageSummary.model_validate(p) for p in pages]


@router.post(
    "/workspaces/{workspace_id}/wiki",
    response_model=WikiPageRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_page(
    workspace_id: uuid.UUID, data: WikiPageCreate, user: CurrentUser, session: SessionDep
) -> WikiPageRead:
    page = await WikiService(session).create_page(user, workspace_id, data)
    return WikiPageRead.model_validate(page)


@router.get("/wiki/{page_id}", response_model=WikiPageRead)
async def get_page(page_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> WikiPageRead:
    return WikiPageRead.model_validate(await WikiService(session).get_page(user, page_id))


@router.patch("/wiki/{page_id}", response_model=WikiPageRead)
async def update_page(
    page_id: uuid.UUID, data: WikiPageUpdate, user: CurrentUser, session: SessionDep
) -> WikiPageRead:
    page = await WikiService(session).update_page(user, page_id, data)
    return WikiPageRead.model_validate(page)


@router.post("/wiki/{page_id}/move", response_model=WikiPageRead)
async def move_page(
    page_id: uuid.UUID, data: WikiPageMove, user: CurrentUser, session: SessionDep
) -> WikiPageRead:
    page = await WikiService(session).move_page(user, page_id, data.parent_id, data.position)
    return WikiPageRead.model_validate(page)


@router.delete("/wiki/{page_id}", status_code=NO_CONTENT)
async def delete_page(page_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    await WikiService(session).delete_page(user, page_id)
    return Response(status_code=NO_CONTENT)
