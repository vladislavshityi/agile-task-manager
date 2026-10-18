import uuid

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.boards.schemas import (
    BoardCreate,
    BoardDetail,
    BoardSummary,
    BoardUpdate,
    ColumnCreate,
    ColumnMove,
    ColumnRead,
    ColumnUpdate,
)
from app.modules.boards.service import BoardService

router = APIRouter(tags=["boards"])
NO_CONTENT = status.HTTP_204_NO_CONTENT


@router.get("/workspaces/{workspace_id}/boards", response_model=list[BoardSummary])
async def list_boards(
    workspace_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> list[BoardSummary]:
    return await BoardService(session).list_boards(user, workspace_id)


@router.post(
    "/workspaces/{workspace_id}/boards",
    response_model=BoardDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_board(
    workspace_id: uuid.UUID, data: BoardCreate, user: CurrentUser, session: SessionDep
) -> BoardDetail:
    board = await BoardService(session).create_board(user, workspace_id, data)
    return BoardDetail.model_validate(board)


@router.get("/boards/{board_id}", response_model=BoardDetail)
async def get_board(board_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> BoardDetail:
    return BoardDetail.model_validate(await BoardService(session).get_board(user, board_id))


@router.patch("/boards/{board_id}", response_model=BoardDetail)
async def update_board(
    board_id: uuid.UUID, data: BoardUpdate, user: CurrentUser, session: SessionDep
) -> BoardDetail:
    board = await BoardService(session).update_board(user, board_id, data)
    return BoardDetail.model_validate(board)


@router.delete("/boards/{board_id}", status_code=NO_CONTENT)
async def delete_board(board_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    await BoardService(session).delete_board(user, board_id)
    return Response(status_code=NO_CONTENT)


@router.post(
    "/boards/{board_id}/columns", response_model=ColumnRead, status_code=status.HTTP_201_CREATED
)
async def add_column(
    board_id: uuid.UUID, data: ColumnCreate, user: CurrentUser, session: SessionDep
) -> ColumnRead:
    return ColumnRead.model_validate(await BoardService(session).add_column(user, board_id, data))


@router.patch("/columns/{column_id}", response_model=ColumnRead)
async def update_column(
    column_id: uuid.UUID, data: ColumnUpdate, user: CurrentUser, session: SessionDep
) -> ColumnRead:
    column = await BoardService(session).update_column(user, column_id, data)
    return ColumnRead.model_validate(column)


@router.post("/columns/{column_id}/move", response_model=ColumnRead)
async def move_column(
    column_id: uuid.UUID, data: ColumnMove, user: CurrentUser, session: SessionDep
) -> ColumnRead:
    column = await BoardService(session).move_column(user, column_id, data.position)
    return ColumnRead.model_validate(column)


@router.delete("/columns/{column_id}", status_code=NO_CONTENT)
async def delete_column(column_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    await BoardService(session).delete_column(user, column_id)
    return Response(status_code=NO_CONTENT)
