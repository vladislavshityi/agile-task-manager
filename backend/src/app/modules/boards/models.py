import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CreatedAt, UuidPk

if TYPE_CHECKING:
    from app.modules.tasks.models import Task

DEFAULT_COLUMN_COLOR = "#8E8E93"


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[UuidPk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_at: Mapped[CreatedAt]

    columns: Mapped[list["Column"]] = relationship(
        order_by="Column.position", lazy="raise", passive_deletes=True
    )


class Column(Base):
    __tablename__ = "columns"

    id: Mapped[UuidPk]
    board_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(
        String(7), default=DEFAULT_COLUMN_COLOR, server_default=DEFAULT_COLUMN_COLOR
    )
    position: Mapped[int] = mapped_column(Integer)

    tasks: Mapped[list["Task"]] = relationship(
        order_by="Task.position", lazy="raise", passive_deletes=True
    )
