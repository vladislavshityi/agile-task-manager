import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Column as SAColumn
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from app.core.db import Base, CreatedAt, UuidPk, str_enum, utcnow
from app.modules.users.models import User


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[UuidPk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(7))


TaskAssignee = Table(
    "task_assignees",
    Base.metadata,
    SAColumn("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    SAColumn("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True),
)

TaskLabel = Table(
    "task_labels",
    Base.metadata,
    SAColumn("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    SAColumn("label_id", ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True, index=True),
)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UuidPk]
    column_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("columns.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    priority: Mapped[Priority] = mapped_column(
        str_enum(Priority), default=Priority.medium, server_default=Priority.medium.value
    )
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    position: Mapped[int] = mapped_column(Integer)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    created_by: Mapped[User] = relationship(lazy="raise")
    assignees: Mapped[list[User]] = relationship(secondary=TaskAssignee, lazy="raise")
    labels: Mapped[list[Label]] = relationship(secondary=TaskLabel, lazy="raise")
    comments: Mapped[list["Comment"]] = relationship(
        order_by="Comment.created_at", lazy="raise", passive_deletes=True
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[UuidPk]
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[CreatedAt]

    author: Mapped[User] = relationship(lazy="raise")


TASK_LOAD_OPTIONS = (
    selectinload(Task.assignees),
    selectinload(Task.labels),
    selectinload(Task.created_by),
)
