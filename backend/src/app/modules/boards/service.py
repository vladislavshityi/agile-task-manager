import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound
from app.modules.boards.models import Board, Column
from app.modules.boards.repository import BoardRepository
from app.modules.boards.schemas import (
    BoardCreate,
    BoardSummary,
    BoardUpdate,
    ColumnCreate,
    ColumnUpdate,
)
from app.modules.users.models import User
from app.modules.workspaces.models import Role
from app.modules.workspaces.service import require_role

DEFAULT_COLUMNS = ("To do", "In progress", "Done")


class BoardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = BoardRepository(session)

    async def _board(self, user: User, board_id: uuid.UUID, min_role: Role) -> Board:
        board = await self.repo.get(board_id)
        if board is None:
            raise NotFound("Board not found", "board_not_found")
        await require_role(self.session, board.workspace_id, user.id, min_role)
        return board

    async def _column(self, user: User, column_id: uuid.UUID, min_role: Role) -> Column:
        column = await self.repo.get_column(column_id)
        if column is None:
            raise NotFound("Column not found", "column_not_found")
        await self._board(user, column.board_id, min_role)
        return column

    async def list_boards(self, user: User, workspace_id: uuid.UUID) -> list[BoardSummary]:
        await require_role(self.session, workspace_id, user.id, Role.viewer)
        return [
            BoardSummary(
                id=b.id,
                name=b.name,
                description=b.description,
                created_at=b.created_at,
                task_count=count,
            )
            for b, count in await self.repo.list_with_task_counts(workspace_id)
        ]

    async def create_board(self, user: User, workspace_id: uuid.UUID, data: BoardCreate) -> Board:
        await require_role(self.session, workspace_id, user.id, Role.admin)
        board = await self.repo.add(
            Board(workspace_id=workspace_id, name=data.name, description=data.description)
        )
        for position, name in enumerate(DEFAULT_COLUMNS):
            await self.repo.add_column(Column(board_id=board.id, name=name, position=position))
        await self.session.commit()
        return await self._full(board.id)

    async def _full(self, board_id: uuid.UUID) -> Board:
        board = await self.repo.get_full(board_id)
        if board is None:
            raise NotFound("Board not found", "board_not_found")
        return board

    async def get_board(self, user: User, board_id: uuid.UUID) -> Board:
        await self._board(user, board_id, Role.viewer)
        return await self._full(board_id)

    async def update_board(self, user: User, board_id: uuid.UUID, data: BoardUpdate) -> Board:
        board = await self._board(user, board_id, Role.admin)
        if data.name is not None:
            board.name = data.name
        if data.description is not None:
            board.description = data.description
        await self.session.commit()
        return await self._full(board_id)

    async def delete_board(self, user: User, board_id: uuid.UUID) -> None:
        await self._board(user, board_id, Role.admin)
        await self.repo.delete(board_id)
        await self.session.commit()

    async def add_column(self, user: User, board_id: uuid.UUID, data: ColumnCreate) -> Column:
        await self._board(user, board_id, Role.admin)
        position = len(await self.repo.list_columns(board_id))
        column = Column(board_id=board_id, name=data.name, position=position)
        if data.color:
            column.color = data.color
        await self.repo.add_column(column)
        await self.session.commit()
        return column

    async def update_column(self, user: User, column_id: uuid.UUID, data: ColumnUpdate) -> Column:
        column = await self._column(user, column_id, Role.admin)
        if data.name is not None:
            column.name = data.name
        if data.color is not None:
            column.color = data.color
        await self.session.commit()
        return column

    async def move_column(self, user: User, column_id: uuid.UUID, position: int) -> Column:
        column = await self._column(user, column_id, Role.admin)
        siblings = [c for c in await self.repo.list_columns(column.board_id) if c.id != column.id]
        siblings.insert(min(position, len(siblings)), column)
        for index, sibling in enumerate(siblings):
            sibling.position = index
        await self.session.commit()
        return column

    async def delete_column(self, user: User, column_id: uuid.UUID) -> None:
        column = await self._column(user, column_id, Role.admin)
        await self.repo.delete_column(column_id)
        for index, sibling in enumerate(await self.repo.list_columns(column.board_id)):
            sibling.position = index
        await self.session.commit()
