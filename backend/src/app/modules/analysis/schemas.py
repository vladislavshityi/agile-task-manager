import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.schemas import ORMModel
from app.modules.analysis.models import Access, FragmentKind, Visibility
from app.modules.users.schemas import UserRead


class AnalysisCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=200_000)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class AnalysisUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    visibility: Visibility | None = None

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class AnalysisMemberUpdate(BaseModel):
    can_edit: bool


class AnalysisMemberRead(ORMModel):
    user: UserRead
    can_edit: bool


class FragmentRead(ORMModel):
    id: uuid.UUID
    ordinal: int
    kind: FragmentKind
    section: str
    heading_path: str
    context: str
    text: str
    start: int
    end: int


class AnalysisSummary(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    visibility: Visibility
    created_by: UserRead
    created_at: datetime
    fragment_count: int
    access: Access


class AnalysisRead(AnalysisSummary):
    text: str
    fragments: list[FragmentRead]
    members: list[AnalysisMemberRead]
