import secrets
import uuid
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import utcnow
from app.core.errors import Conflict, Forbidden, NotFound
from app.modules.users.models import User
from app.modules.workspaces.models import Invite, Membership, Role, Workspace
from app.modules.workspaces.repository import WorkspaceRepository
from app.modules.workspaces.schemas import (
    InviteCreate,
    InvitePreview,
    WorkspaceRead,
)


async def require_role(
    session: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID, min_role: Role
) -> Membership:
    membership = await WorkspaceRepository(session).get_membership(workspace_id, user_id)
    if membership is None:
        raise NotFound("Workspace not found", "workspace_not_found")
    if membership.role.rank < min_role.rank:
        raise Forbidden(f"Requires role {min_role.value} or higher", "insufficient_role")
    return membership


def _is_invite_valid(invite: Invite) -> bool:
    return not invite.revoked and (invite.expires_at is None or invite.expires_at > utcnow())


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = WorkspaceRepository(session)

    @staticmethod
    def _read(workspace: Workspace, role: Role) -> WorkspaceRead:
        return WorkspaceRead(
            id=workspace.id, name=workspace.name, role=role, created_at=workspace.created_at
        )

    async def list_for_user(self, user: User) -> list[WorkspaceRead]:
        return [self._read(w, role) for w, role in await self.repo.list_for_user(user.id)]

    async def create(self, user: User, name: str) -> WorkspaceRead:
        workspace = await self.repo.add(name, user.id)
        await self.session.commit()
        return self._read(workspace, Role.owner)

    async def rename(self, user: User, workspace_id: uuid.UUID, name: str) -> WorkspaceRead:
        membership = await require_role(self.session, workspace_id, user.id, Role.owner)
        workspace = await self._get(workspace_id)
        workspace.name = name
        await self.session.commit()
        return self._read(workspace, membership.role)

    async def delete(self, user: User, workspace_id: uuid.UUID) -> None:
        await require_role(self.session, workspace_id, user.id, Role.owner)
        await self.repo.delete(workspace_id)
        await self.session.commit()

    async def _get(self, workspace_id: uuid.UUID) -> Workspace:
        workspace = await self.repo.get(workspace_id)
        if workspace is None:
            raise NotFound("Workspace not found", "workspace_not_found")
        return workspace

    async def list_members(self, user: User, workspace_id: uuid.UUID) -> list[Membership]:
        await require_role(self.session, workspace_id, user.id, Role.viewer)
        return await self.repo.list_members(workspace_id)

    async def change_role(
        self, user: User, workspace_id: uuid.UUID, target_id: uuid.UUID, new_role: Role
    ) -> Membership:
        actor = await require_role(self.session, workspace_id, user.id, Role.admin)
        target = await self.repo.get_membership(workspace_id, target_id)
        if target is None:
            raise NotFound("Member not found", "member_not_found")
        if target.user_id == actor.user_id:
            raise Forbidden("You cannot change your own role", "cannot_change_own_role")
        if new_role is Role.owner:
            if actor.role is not Role.owner:
                raise Forbidden("Only the owner can transfer ownership", "insufficient_role")
            actor.role = Role.admin
        elif target.role.rank >= actor.role.rank or new_role.rank >= actor.role.rank:
            raise Forbidden("You can only manage roles below your own", "insufficient_role")
        target.role = new_role
        await self.session.commit()
        return await self._member(workspace_id, target_id)

    async def _member(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> Membership:
        member = await self.repo.get_member_with_user(workspace_id, user_id)
        if member is None:
            raise NotFound("Member not found", "member_not_found")
        return member

    async def remove_member(
        self, user: User, workspace_id: uuid.UUID, target_id: uuid.UUID
    ) -> None:
        actor = await require_role(self.session, workspace_id, user.id, Role.viewer)
        target = await self.repo.get_membership(workspace_id, target_id)
        if target is None:
            raise NotFound("Member not found", "member_not_found")
        if target.user_id == actor.user_id:
            if actor.role is Role.owner:
                raise Forbidden("The owner cannot leave the workspace", "owner_cannot_leave")
        else:
            if actor.role.rank < Role.admin.rank:
                raise Forbidden("Requires role admin or higher", "insufficient_role")
            if target.role.rank >= actor.role.rank:
                raise Forbidden("You can only remove members below your role", "insufficient_role")
        await self.repo.remove_member(workspace_id, target_id)
        await self.session.commit()

    async def list_invites(self, user: User, workspace_id: uuid.UUID) -> list[Invite]:
        await require_role(self.session, workspace_id, user.id, Role.admin)
        return await self.repo.list_invites(workspace_id)

    async def create_invite(
        self, user: User, workspace_id: uuid.UUID, data: InviteCreate
    ) -> Invite:
        actor = await require_role(self.session, workspace_id, user.id, Role.admin)
        if data.role.rank >= actor.role.rank:
            raise Forbidden("You can only invite to roles below your own", "insufficient_role")
        expires_at = (
            utcnow() + timedelta(days=data.expires_in_days) if data.expires_in_days else None
        )
        invite = Invite(
            workspace_id=workspace_id,
            token=secrets.token_urlsafe(24),
            role=data.role,
            created_by_id=user.id,
            expires_at=expires_at,
        )
        await self.repo.add_invite(invite)
        await self.session.commit()
        return await self.repo.get_invite_with_user(invite.id)

    async def revoke_invite(
        self, user: User, workspace_id: uuid.UUID, invite_id: uuid.UUID
    ) -> None:
        await require_role(self.session, workspace_id, user.id, Role.admin)
        invite = await self.repo.get_invite(workspace_id, invite_id)
        if invite is None:
            raise NotFound("Invite not found", "invite_not_found")
        invite.revoked = True
        await self.session.commit()

    async def preview_invite(self, token: str) -> InvitePreview:
        invite = await self._invite_by_token(token)
        return InvitePreview(
            workspace_name=invite.workspace.name,
            inviter_name=invite.created_by.full_name,
            role=invite.role,
            valid=_is_invite_valid(invite),
        )

    async def accept_invite(self, user: User, token: str) -> uuid.UUID:
        invite = await self._invite_by_token(token)
        if await self.repo.get_membership(invite.workspace_id, user.id) is not None:
            return invite.workspace_id
        if invite.revoked:
            raise Conflict("This invite has been revoked", "invite_revoked")
        if not _is_invite_valid(invite):
            raise Conflict("This invite has expired", "invite_expired")
        self.session.add(
            Membership(workspace_id=invite.workspace_id, user_id=user.id, role=invite.role)
        )
        await self.session.commit()
        return invite.workspace_id

    async def _invite_by_token(self, token: str) -> Invite:
        invite = await self.repo.get_invite_by_token(token)
        if invite is None:
            raise NotFound("Invite not found", "invite_not_found")
        return invite
