import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.schemas import ORMModel
from app.modules.users.schemas import UserRead
from app.modules.workspaces.models import Role


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WorkspaceRead(BaseModel):
    id: uuid.UUID
    name: str
    role: Role
    created_at: datetime


class MemberRead(ORMModel):
    user: UserRead
    role: Role
    joined_at: datetime = Field(validation_alias="created_at")


class MemberRoleUpdate(BaseModel):
    role: Role


class InviteCreate(BaseModel):
    role: Role = Role.member
    expires_in_days: int | None = Field(default=None, gt=0, le=365)


class InviteRead(ORMModel):
    id: uuid.UUID
    token: str
    role: Role
    created_at: datetime
    expires_at: datetime | None
    revoked: bool
    created_by: UserRead


class InvitePreview(BaseModel):
    workspace_name: str
    inviter_name: str
    role: Role
    valid: bool


class InviteAccepted(BaseModel):
    workspace_id: uuid.UUID
