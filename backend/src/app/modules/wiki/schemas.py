import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.schemas import ORMModel
from app.modules.users.schemas import UserRead


class WikiPageCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default="", max_length=200_000)
    parent_id: uuid.UUID | None = None


class WikiPageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=200_000)


class WikiPageMove(BaseModel):
    parent_id: uuid.UUID | None = None
    position: int = Field(ge=0)


class WikiPageSummary(ORMModel):
    id: uuid.UUID
    parent_id: uuid.UUID | None
    title: str
    position: int
    updated_at: datetime


class WikiPageRead(WikiPageSummary):
    workspace_id: uuid.UUID
    content: str
    created_at: datetime
    created_by: UserRead
    updated_by: UserRead
