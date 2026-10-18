import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CreatedAt, UuidPk, str_enum
from app.modules.users.models import User


class Role(StrEnum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"

    @property
    def rank(self) -> int:
        return _RANKS[self]


_RANKS = {Role.viewer: 0, Role.member: 1, Role.admin: 2, Role.owner: 3}


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[UuidPk]
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[CreatedAt]


class Membership(Base):
    __tablename__ = "memberships"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    role: Mapped[Role] = mapped_column(str_enum(Role))
    created_at: Mapped[CreatedAt]

    user: Mapped[User] = relationship(lazy="raise")


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[UuidPk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    role: Mapped[Role] = mapped_column(str_enum(Role), default=Role.member)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[CreatedAt]
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    workspace: Mapped[Workspace] = relationship(lazy="raise")
    created_by: Mapped[User] = relationship(lazy="raise")
