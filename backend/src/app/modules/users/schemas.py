import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.schemas import ORMModel

HEX_COLOR = r"^#[0-9A-Fa-f]{6}$"


class UserRead(ORMModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    avatar_color: str
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_color: str | None = Field(default=None, pattern=HEX_COLOR)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
