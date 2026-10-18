import uuid

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.workspaces.schemas import (
    InviteAccepted,
    InviteCreate,
    InvitePreview,
    InviteRead,
    MemberRead,
    MemberRoleUpdate,
    WorkspaceCreate,
    WorkspaceRead,
)
from app.modules.workspaces.service import WorkspaceService

router = APIRouter(tags=["workspaces"])
NO_CONTENT = status.HTTP_204_NO_CONTENT


@router.get("/workspaces", response_model=list[WorkspaceRead])
async def list_workspaces(user: CurrentUser, session: SessionDep) -> list[WorkspaceRead]:
    return await WorkspaceService(session).list_for_user(user)


@router.post("/workspaces", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate, user: CurrentUser, session: SessionDep
) -> WorkspaceRead:
    return await WorkspaceService(session).create(user, data.name)


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceRead)
async def rename_workspace(
    workspace_id: uuid.UUID, data: WorkspaceCreate, user: CurrentUser, session: SessionDep
) -> WorkspaceRead:
    return await WorkspaceService(session).rename(user, workspace_id, data.name)


@router.delete("/workspaces/{workspace_id}", status_code=NO_CONTENT)
async def delete_workspace(
    workspace_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> Response:
    await WorkspaceService(session).delete(user, workspace_id)
    return Response(status_code=NO_CONTENT)


@router.get("/workspaces/{workspace_id}/members", response_model=list[MemberRead])
async def list_members(
    workspace_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> list[MemberRead]:
    members = await WorkspaceService(session).list_members(user, workspace_id)
    return [MemberRead.model_validate(m) for m in members]


@router.patch("/workspaces/{workspace_id}/members/{user_id}", response_model=MemberRead)
async def change_member_role(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MemberRoleUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> MemberRead:
    member = await WorkspaceService(session).change_role(user, workspace_id, user_id, data.role)
    return MemberRead.model_validate(member)


@router.delete("/workspaces/{workspace_id}/members/{user_id}", status_code=NO_CONTENT)
async def remove_member(
    workspace_id: uuid.UUID, user_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> Response:
    await WorkspaceService(session).remove_member(user, workspace_id, user_id)
    return Response(status_code=NO_CONTENT)


@router.get("/workspaces/{workspace_id}/invites", response_model=list[InviteRead])
async def list_invites(
    workspace_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> list[InviteRead]:
    invites = await WorkspaceService(session).list_invites(user, workspace_id)
    return [InviteRead.model_validate(i) for i in invites]


@router.post(
    "/workspaces/{workspace_id}/invites",
    response_model=InviteRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    workspace_id: uuid.UUID, data: InviteCreate, user: CurrentUser, session: SessionDep
) -> InviteRead:
    invite = await WorkspaceService(session).create_invite(user, workspace_id, data)
    return InviteRead.model_validate(invite)


@router.delete("/workspaces/{workspace_id}/invites/{invite_id}", status_code=NO_CONTENT)
async def revoke_invite(
    workspace_id: uuid.UUID, invite_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> Response:
    await WorkspaceService(session).revoke_invite(user, workspace_id, invite_id)
    return Response(status_code=NO_CONTENT)


@router.get("/invites/{token}", response_model=InvitePreview)
async def preview_invite(token: str, session: SessionDep) -> InvitePreview:
    return await WorkspaceService(session).preview_invite(token)


@router.post("/invites/{token}/accept", response_model=InviteAccepted)
async def accept_invite(token: str, user: CurrentUser, session: SessionDep) -> InviteAccepted:
    workspace_id = await WorkspaceService(session).accept_invite(user, token)
    return InviteAccepted(workspace_id=workspace_id)
