import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.boards.models import Board, Column
from app.modules.tasks.models import TASK_LOAD_OPTIONS, Task


class BoardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, board: Board) -> Board:
        self.session.add(board)
        await self.session.flush()
        return board

    async def get(self, board_id: uuid.UUID) -> Board | None:
        return await self.session.get(Board, board_id)

    async def get_full(self, board_id: uuid.UUID) -> Board | None:
        result = await self.session.execute(
            select(Board)
            .where(Board.id == board_id)
            .options(
                selectinload(Board.columns).selectinload(Column.tasks).options(*TASK_LOAD_OPTIONS)
            )
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def delete(self, board_id: uuid.UUID) -> None:
        await self.session.execute(delete(Board).where(Board.id == board_id))

    async def list_with_task_counts(self, workspace_id: uuid.UUID) -> list[tuple[Board, int]]:
        task_count = func.count(Task.id)
        result = await self.session.execute(
            select(Board, task_count)
            .outerjoin(Column, Column.board_id == Board.id)
            .outerjoin(Task, Task.column_id == Column.id)
            .where(Board.workspace_id == workspace_id)
            .group_by(Board.id)
            .order_by(Board.created_at)
        )
        return [(board, count) for board, count in result.all()]

    async def get_column(self, column_id: uuid.UUID) -> Column | None:
        return await self.session.get(Column, column_id)

    async def list_columns(self, board_id: uuid.UUID) -> list[Column]:
        result = await self.session.execute(
            select(Column).where(Column.board_id == board_id).order_by(Column.position)
        )
        return list(result.scalars())

    async def add_column(self, column: Column) -> Column:
        self.session.add(column)
        await self.session.flush()
        return column

    async def delete_column(self, column_id: uuid.UUID) -> None:
        await self.session.execute(delete(Column).where(Column.id == column_id))
