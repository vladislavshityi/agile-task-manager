import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.schemas import ORMModel
from app.modules.tasks.models import Priority
from app.modules.users.schemas import HEX_COLOR, UserRead


class LabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(pattern=HEX_COLOR)


class LabelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, pattern=HEX_COLOR)


class LabelRead(ORMModel):
    id: uuid.UUID
    name: str
    color: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: Priority = Priority.medium
    due_date: date | None = None
    assignee_ids: list[uuid.UUID] = []
    label_ids: list[uuid.UUID] = []


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: Priority | None = None
    due_date: date | None = None
    assignee_ids: list[uuid.UUID] | None = None
    label_ids: list[uuid.UUID] | None = None


class TaskMove(BaseModel):
    column_id: uuid.UUID
    position: int = Field(ge=0)


class TaskRead(ORMModel):
    id: uuid.UUID
    column_id: uuid.UUID
    title: str
    description: str
    priority: Priority
    due_date: date | None
    position: int
    created_at: datetime
    updated_at: datetime
    created_by: UserRead
    assignees: list[UserRead]
    labels: list[LabelRead]


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class CommentRead(ORMModel):
    id: uuid.UUID
    body: str
    created_at: datetime
    author: UserRead


class TaskDetail(TaskRead):
    comments: list[CommentRead]


class MyTask(TaskRead):
    board_id: uuid.UUID
    board_name: str
    column_name: str
