import uuid
from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.boards.models import Board, Column
from app.modules.tasks.models import (
    TASK_LOAD_OPTIONS,
    Comment,
    Label,
    Task,
    TaskAssignee,
)
from app.modules.users.models import User
from app.modules.workspaces.models import Membership


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def workspace_id_of_column(self, column_id: uuid.UUID) -> uuid.UUID | None:
        result = await self.session.execute(
            select(Board.workspace_id)
            .join(Column, Column.board_id == Board.id)
            .where(Column.id == column_id)
        )
        return result.scalar_one_or_none()

    async def workspace_id_of_task(self, task_id: uuid.UUID) -> uuid.UUID | None:
        result = await self.session.execute(
            select(Board.workspace_id)
            .join(Column, Column.board_id == Board.id)
            .join(Task, Task.column_id == Column.id)
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def workspace_id_of_comment(self, comment_id: uuid.UUID) -> uuid.UUID | None:
        result = await self.session.execute(
            select(Board.workspace_id)
            .join(Column, Column.board_id == Board.id)
            .join(Task, Task.column_id == Column.id)
            .join(Comment, Comment.task_id == Task.id)
            .where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def get_column(self, column_id: uuid.UUID) -> Column | None:
        return await self.session.get(Column, column_id)

    async def get_task(self, task_id: uuid.UUID, *, with_comments: bool = False) -> Task | None:
        options = list(TASK_LOAD_OPTIONS)
        if with_comments:
            options.append(selectinload(Task.comments).selectinload(Comment.author))
        result = await self.session.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(*options)
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def list_in_column(self, column_id: uuid.UUID) -> list[Task]:
        result = await self.session.execute(
            select(Task).where(Task.column_id == column_id).order_by(Task.position)
        )
        return list(result.scalars())

    async def count_in_column(self, column_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Task).where(Task.column_id == column_id)
        )
        return result.scalar_one()

    async def add(self, task: Task) -> Task:
        self.session.add(task)
        await self.session.flush()
        return task

    async def delete(self, task_id: uuid.UUID) -> None:
        await self.session.execute(delete(Task).where(Task.id == task_id))

    async def workspace_members(
        self, workspace_id: uuid.UUID, user_ids: list[uuid.UUID]
    ) -> list[User]:
        result = await self.session.execute(
            select(User)
            .join(Membership, Membership.user_id == User.id)
            .where(Membership.workspace_id == workspace_id, User.id.in_(user_ids))
        )
        return list(result.scalars())

    async def workspace_labels(
        self, workspace_id: uuid.UUID, label_ids: list[uuid.UUID]
    ) -> list[Label]:
        result = await self.session.execute(
            select(Label).where(Label.workspace_id == workspace_id, Label.id.in_(label_ids))
        )
        return list(result.scalars())

    async def list_assigned(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID | None,
        due_from: date | None,
        due_to: date | None,
    ) -> list[tuple[Task, uuid.UUID, str, str]]:
        query = (
            select(Task, Board.id, Board.name, Column.name)
            .join(TaskAssignee, TaskAssignee.c.task_id == Task.id)
            .join(Column, Column.id == Task.column_id)
            .join(Board, Board.id == Column.board_id)
            .join(
                Membership,
                (Membership.workspace_id == Board.workspace_id) & (Membership.user_id == user_id),
            )
            .where(TaskAssignee.c.user_id == user_id)
            .options(*TASK_LOAD_OPTIONS)
            .order_by(Task.due_date.asc().nulls_last(), Task.created_at)
        )
        if workspace_id is not None:
            query = query.where(Board.workspace_id == workspace_id)
        if due_from is not None:
            query = query.where(Task.due_date >= due_from)
        if due_to is not None:
            query = query.where(Task.due_date <= due_to)
        result = await self.session.execute(query)
        return [
            (task, board_id, board_name, column_name)
            for task, board_id, board_name, column_name in result.all()
        ]

    async def add_comment(self, comment: Comment) -> Comment:
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def get_comment(self, comment_id: uuid.UUID) -> Comment | None:
        return await self.session.get(Comment, comment_id)

    async def delete_comment(self, comment_id: uuid.UUID) -> None:
        await self.session.execute(delete(Comment).where(Comment.id == comment_id))

    async def list_labels(self, workspace_id: uuid.UUID) -> list[Label]:
        result = await self.session.execute(
            select(Label).where(Label.workspace_id == workspace_id).order_by(Label.name)
        )
        return list(result.scalars())

    async def get_label(self, label_id: uuid.UUID) -> Label | None:
        return await self.session.get(Label, label_id)

    async def add_label(self, label: Label) -> Label:
        self.session.add(label)
        await self.session.flush()
        return label

    async def delete_label(self, label_id: uuid.UUID) -> None:
        await self.session.execute(delete(Label).where(Label.id == label_id))
