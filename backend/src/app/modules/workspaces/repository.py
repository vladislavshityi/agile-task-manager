import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.modules.boards.models import Board, Column
from app.modules.tasks.models import Task, TaskAssignee
from app.modules.workspaces.models import Invite, Membership, Role, Workspace


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, name: str, owner_id: uuid.UUID) -> Workspace:
        workspace = Workspace(name=name)
        self.session.add(workspace)
        await self.session.flush()
        self.session.add(Membership(workspace_id=workspace.id, user_id=owner_id, role=Role.owner))
        await self.session.flush()
        return workspace

    async def get(self, workspace_id: uuid.UUID) -> Workspace | None:
        return await self.session.get(Workspace, workspace_id)

    async def delete(self, workspace_id: uuid.UUID) -> None:
        await self.session.execute(delete(Workspace).where(Workspace.id == workspace_id))

    async def list_for_user(self, user_id: uuid.UUID) -> list[tuple[Workspace, Role]]:
        result = await self.session.execute(
            select(Workspace, Membership.role)
            .join(Membership, Membership.workspace_id == Workspace.id)
            .where(Membership.user_id == user_id)
            .order_by(Workspace.created_at)
        )
        return [(workspace, role) for workspace, role in result.all()]

    async def get_membership(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> Membership | None:
        return await self.session.get(Membership, (workspace_id, user_id))

    async def get_member_with_user(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> Membership | None:
        result = await self.session.execute(
            select(Membership)
            .where(Membership.workspace_id == workspace_id, Membership.user_id == user_id)
            .options(joinedload(Membership.user))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def list_members(self, workspace_id: uuid.UUID) -> list[Membership]:
        result = await self.session.execute(
            select(Membership)
            .where(Membership.workspace_id == workspace_id)
            .options(joinedload(Membership.user))
            .order_by(Membership.created_at)
        )
        return list(result.scalars())

    async def remove_member(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
        workspace_tasks = (
            select(Task.id)
            .join(Column, Column.id == Task.column_id)
            .join(Board, Board.id == Column.board_id)
            .where(Board.workspace_id == workspace_id)
        )
        await self.session.execute(
            delete(TaskAssignee).where(
                TaskAssignee.c.user_id == user_id, TaskAssignee.c.task_id.in_(workspace_tasks)
            )
        )
        await self.session.execute(
            delete(Membership).where(
                Membership.workspace_id == workspace_id, Membership.user_id == user_id
            )
        )

    async def add_invite(self, invite: Invite) -> None:
        self.session.add(invite)
        await self.session.flush()

    async def get_invite(self, workspace_id: uuid.UUID, invite_id: uuid.UUID) -> Invite | None:
        result = await self.session.execute(
            select(Invite).where(Invite.id == invite_id, Invite.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_invite_with_user(self, invite_id: uuid.UUID) -> Invite:
        result = await self.session.execute(
            select(Invite)
            .where(Invite.id == invite_id)
            .options(joinedload(Invite.created_by))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one()

    async def list_invites(self, workspace_id: uuid.UUID) -> list[Invite]:
        result = await self.session.execute(
            select(Invite)
            .where(Invite.workspace_id == workspace_id, Invite.revoked.is_(False))
            .options(joinedload(Invite.created_by))
            .order_by(Invite.created_at.desc())
        )
        return list(result.scalars())

    async def get_invite_by_token(self, token: str) -> Invite | None:
        result = await self.session.execute(
            select(Invite)
            .where(Invite.token == token)
            .options(joinedload(Invite.created_by), selectinload(Invite.workspace))
        )
        return result.scalar_one_or_none()
