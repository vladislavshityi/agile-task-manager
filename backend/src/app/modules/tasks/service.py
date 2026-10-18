import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import utcnow
from app.core.errors import Forbidden, NotFound, ValidationError
from app.modules.tasks.models import Comment, Label, Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import (
    LabelCreate,
    LabelUpdate,
    MyTask,
    TaskCreate,
    TaskMove,
    TaskRead,
    TaskUpdate,
)
from app.modules.users.models import User
from app.modules.workspaces.models import Role
from app.modules.workspaces.service import require_role


def _renumber(tasks: list[Task]) -> None:
    for index, task in enumerate(tasks):
        task.position = index


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TaskRepository(session)

    async def _workspace_of_task(self, user: User, task_id: uuid.UUID, min_role: Role) -> uuid.UUID:
        workspace_id = await self.repo.workspace_id_of_task(task_id)
        if workspace_id is None:
            raise NotFound("Task not found", "task_not_found")
        await require_role(self.session, workspace_id, user.id, min_role)
        return workspace_id

    async def _loaded(self, task_id: uuid.UUID, *, with_comments: bool = False) -> Task:
        task = await self.repo.get_task(task_id, with_comments=with_comments)
        if task is None:
            raise NotFound("Task not found", "task_not_found")
        return task

    async def _assignees(self, workspace_id: uuid.UUID, ids: list[uuid.UUID]) -> list[User]:
        unique = list(set(ids))
        users = await self.repo.workspace_members(workspace_id, unique) if unique else []
        if len(users) != len(unique):
            raise ValidationError("Assignees must be workspace members", "invalid_assignees")
        return users

    async def _labels(self, workspace_id: uuid.UUID, ids: list[uuid.UUID]) -> list[Label]:
        unique = list(set(ids))
        labels = await self.repo.workspace_labels(workspace_id, unique) if unique else []
        if len(labels) != len(unique):
            raise ValidationError("Labels must belong to the workspace", "invalid_labels")
        return labels

    async def create(self, user: User, column_id: uuid.UUID, data: TaskCreate) -> Task:
        workspace_id = await self.repo.workspace_id_of_column(column_id)
        if workspace_id is None:
            raise NotFound("Column not found", "column_not_found")
        await require_role(self.session, workspace_id, user.id, Role.member)
        task = Task(
            column_id=column_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            position=await self.repo.count_in_column(column_id),
            created_by_id=user.id,
            assignees=await self._assignees(workspace_id, data.assignee_ids),
            labels=await self._labels(workspace_id, data.label_ids),
        )
        await self.repo.add(task)
        await self.session.commit()
        return await self._loaded(task.id)

    async def get(self, user: User, task_id: uuid.UUID) -> Task:
        await self._workspace_of_task(user, task_id, Role.viewer)
        return await self._loaded(task_id, with_comments=True)

    async def update(self, user: User, task_id: uuid.UUID, data: TaskUpdate) -> Task:
        workspace_id = await self._workspace_of_task(user, task_id, Role.member)
        task = await self._loaded(task_id)
        changes = data.model_fields_set
        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.priority is not None:
            task.priority = data.priority
        if "due_date" in changes:
            task.due_date = data.due_date
        if data.assignee_ids is not None:
            task.assignees = await self._assignees(workspace_id, data.assignee_ids)
        if data.label_ids is not None:
            task.labels = await self._labels(workspace_id, data.label_ids)
        task.updated_at = utcnow()
        await self.session.commit()
        return await self._loaded(task_id)

    async def move(self, user: User, task_id: uuid.UUID, data: TaskMove) -> Task:
        await self._workspace_of_task(user, task_id, Role.member)
        task = await self._loaded(task_id)
        source = await self.repo.get_column(task.column_id)
        target = await self.repo.get_column(data.column_id)
        if source is None or target is None or target.board_id != source.board_id:
            raise ValidationError("Target column must be on the same board", "column_not_in_board")

        source_tasks = [t for t in await self.repo.list_in_column(source.id) if t.id != task.id]
        if target.id == source.id:
            source_tasks.insert(min(data.position, len(source_tasks)), task)
            _renumber(source_tasks)
        else:
            _renumber(source_tasks)
            target_tasks = await self.repo.list_in_column(target.id)
            target_tasks.insert(min(data.position, len(target_tasks)), task)
            task.column_id = target.id
            _renumber(target_tasks)
        task.updated_at = utcnow()
        await self.session.commit()
        return await self._loaded(task_id)

    async def delete(self, user: User, task_id: uuid.UUID) -> None:
        await self._workspace_of_task(user, task_id, Role.member)
        task = await self._loaded(task_id)
        column_id = task.column_id
        await self.repo.delete(task_id)
        _renumber([t for t in await self.repo.list_in_column(column_id) if t.id != task_id])
        await self.session.commit()

    async def my_tasks(
        self,
        user: User,
        workspace_id: uuid.UUID | None,
        due_from: date | None,
        due_to: date | None,
    ) -> list[MyTask]:
        rows = await self.repo.list_assigned(user.id, workspace_id, due_from, due_to)
        return [
            MyTask(
                **TaskRead.model_validate(task).model_dump(),
                board_id=board_id,
                board_name=board_name,
                column_name=column_name,
            )
            for task, board_id, board_name, column_name in rows
        ]

    async def add_comment(self, user: User, task_id: uuid.UUID, body: str) -> Comment:
        await self._workspace_of_task(user, task_id, Role.member)
        comment = await self.repo.add_comment(Comment(task_id=task_id, author=user, body=body))
        await self.session.commit()
        return comment

    async def delete_comment(self, user: User, comment_id: uuid.UUID) -> None:
        workspace_id = await self.repo.workspace_id_of_comment(comment_id)
        comment = await self.repo.get_comment(comment_id)
        if workspace_id is None or comment is None:
            raise NotFound("Comment not found", "comment_not_found")
        min_role = Role.member if comment.author_id == user.id else Role.admin
        membership = await require_role(self.session, workspace_id, user.id, Role.viewer)
        if membership.role.rank < min_role.rank:
            raise Forbidden(
                "Only the author or an admin can delete this comment", "insufficient_role"
            )
        await self.repo.delete_comment(comment_id)
        await self.session.commit()

    async def list_labels(self, user: User, workspace_id: uuid.UUID) -> list[Label]:
        await require_role(self.session, workspace_id, user.id, Role.viewer)
        return await self.repo.list_labels(workspace_id)

    async def create_label(self, user: User, workspace_id: uuid.UUID, data: LabelCreate) -> Label:
        await require_role(self.session, workspace_id, user.id, Role.admin)
        label = await self.repo.add_label(
            Label(workspace_id=workspace_id, name=data.name, color=data.color)
        )
        await self.session.commit()
        return label

    async def _label(self, user: User, label_id: uuid.UUID) -> Label:
        label = await self.repo.get_label(label_id)
        if label is None:
            raise NotFound("Label not found", "label_not_found")
        await require_role(self.session, label.workspace_id, user.id, Role.admin)
        return label

    async def update_label(self, user: User, label_id: uuid.UUID, data: LabelUpdate) -> Label:
        label = await self._label(user, label_id)
        if data.name is not None:
            label.name = data.name
        if data.color is not None:
            label.color = data.color
        await self.session.commit()
        return label

    async def delete_label(self, user: User, label_id: uuid.UUID) -> None:
        await self._label(user, label_id)
        await self.repo.delete_label(label_id)
        await self.session.commit()
