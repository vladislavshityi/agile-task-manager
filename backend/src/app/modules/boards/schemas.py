import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.schemas import ORMModel
from app.modules.tasks.schemas import TaskRead
from app.modules.users.schemas import HEX_COLOR


class BoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""


class BoardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class BoardSummary(ORMModel):
    id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    task_count: int


class ColumnCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=HEX_COLOR)


class ColumnUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=HEX_COLOR)


class ColumnMove(BaseModel):
    position: int = Field(ge=0)


class ColumnRead(ORMModel):
    id: uuid.UUID
    board_id: uuid.UUID
    name: str
    color: str
    position: int


class ColumnWithTasks(ColumnRead):
    tasks: list[TaskRead]


class BoardRead(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str
    created_at: datetime


class BoardDetail(BoardRead):
    columns: list[ColumnWithTasks]
