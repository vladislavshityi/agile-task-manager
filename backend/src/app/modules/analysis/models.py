import uuid
from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CreatedAt, UuidPk, str_enum
from app.modules.users.models import User


class Visibility(StrEnum):
    private = "private"
    workspace = "workspace"


class FragmentKind(StrEnum):
    heading = "heading"
    paragraph = "paragraph"
    list_item = "list_item"


class Access(StrEnum):
    read = "read"
    edit = "edit"
    manage = "manage"

    @property
    def rank(self) -> int:
        return _ACCESS_RANKS[self]


_ACCESS_RANKS = {Access.read: 0, Access.edit: 1, Access.manage: 2}


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[UuidPk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text)
    visibility: Mapped[Visibility] = mapped_column(str_enum(Visibility), default=Visibility.private)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[CreatedAt]

    created_by: Mapped[User] = relationship(lazy="raise")
    fragments: Mapped[list["SpecFragment"]] = relationship(
        order_by="SpecFragment.ordinal", lazy="raise", passive_deletes=True
    )
    members: Mapped[list["AnalysisMember"]] = relationship(
        order_by="AnalysisMember.created_at", lazy="raise", passive_deletes=True
    )


class AnalysisMember(Base):
    __tablename__ = "analysis_members"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[CreatedAt]

    user: Mapped[User] = relationship(lazy="raise")


class SpecFragment(Base):
    __tablename__ = "spec_fragments"
    __table_args__ = (UniqueConstraint("analysis_id", "ordinal"),)

    id: Mapped[UuidPk]
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    kind: Mapped[FragmentKind] = mapped_column(str_enum(FragmentKind))
    section: Mapped[str] = mapped_column(String(32), default="", server_default="")
    heading_path: Mapped[str] = mapped_column(Text, default="", server_default="")
    context: Mapped[str] = mapped_column(Text, default="", server_default="")
    text: Mapped[str] = mapped_column(Text)
    start: Mapped[int] = mapped_column(Integer)
    end: Mapped[int] = mapped_column(Integer)
