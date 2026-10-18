import uuid
from datetime import timedelta

import httpx
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import utcnow
from app.modules.workspaces.models import Invite
from tests.conftest import Account, RegisterUser


async def _create_invite(client: httpx.AsyncClient, owner: Account, **body) -> dict:
    response = await client.post(
        f"/workspaces/{owner.workspace_id}/invites", json=body, headers=owner.headers
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_invite_defaults(client: httpx.AsyncClient, owner: Account):
    invite = await _create_invite(client, owner)
    assert invite["role"] == "member"
    assert invite["revoked"] is False
    assert invite["expires_at"] is None
    assert invite["created_by"]["id"] == owner.id
    assert len(invite["token"]) >= 16

    with_expiry = await _create_invite(client, owner, role="viewer", expires_in_days=7)
    assert with_expiry["role"] == "viewer"
    assert with_expiry["expires_at"] is not None

    listed = (
        await client.get(f"/workspaces/{owner.workspace_id}/invites", headers=owner.headers)
    ).json()
    assert len(listed) == 2


async def test_preview_does_not_require_auth(client: httpx.AsyncClient, owner: Account):
    invite = await _create_invite(client, owner)
    response = await client.get(f"/invites/{invite['token']}")
    assert response.status_code == 200
    assert response.json() == {
        "workspace_name": "Owner's workspace",
        "inviter_name": "Owner",
        "role": "member",
        "valid": True,
    }
    assert (await client.get("/invites/does-not-exist")).status_code == 404


async def test_accept_adds_membership_and_is_idempotent(
    client: httpx.AsyncClient, register_user: RegisterUser, owner: Account
):
    guest = await register_user("guest")
    invite = await _create_invite(client, owner, role="viewer")

    first = await client.post(f"/invites/{invite['token']}/accept", headers=guest.headers)
    second = await client.post(f"/invites/{invite['token']}/accept", headers=guest.headers)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == {"workspace_id": owner.workspace_id}

    members = (
        await client.get(f"/workspaces/{owner.workspace_id}/members", headers=owner.headers)
    ).json()
    roles = {m["user"]["id"]: m["role"] for m in members}
    assert roles == {owner.id: "owner", guest.id: "viewer"}


async def test_accept_requires_authentication(client: httpx.AsyncClient, owner: Account):
    invite = await _create_invite(client, owner)
    assert (await client.post(f"/invites/{invite['token']}/accept")).status_code == 401


async def test_existing_member_keeps_role_when_accepting(client: httpx.AsyncClient, owner: Account):
    invite = await _create_invite(client, owner)
    response = await client.post(f"/invites/{invite['token']}/accept", headers=owner.headers)
    assert response.status_code == 200
    workspaces = (await client.get("/workspaces", headers=owner.headers)).json()
    assert [w["role"] for w in workspaces] == ["owner"]


async def test_revoked_invite_cannot_be_accepted(
    client: httpx.AsyncClient, register_user: RegisterUser, owner: Account
):
    guest = await register_user("guest")
    invite = await _create_invite(client, owner)
    revoke = await client.delete(
        f"/workspaces/{owner.workspace_id}/invites/{invite['id']}", headers=owner.headers
    )
    assert revoke.status_code == 204

    preview = await client.get(f"/invites/{invite['token']}")
    assert preview.json()["valid"] is False
    accept = await client.post(f"/invites/{invite['token']}/accept", headers=guest.headers)
    assert accept.status_code == 409
    assert accept.json()["code"] == "invite_revoked"


async def test_expired_invite_cannot_be_accepted(
    client: httpx.AsyncClient, session: AsyncSession, register_user: RegisterUser, owner: Account
):
    guest = await register_user("guest")
    invite = await _create_invite(client, owner, expires_in_days=1)
    await session.execute(
        update(Invite)
        .where(Invite.id == uuid.UUID(invite["id"]))
        .values(expires_at=utcnow() - timedelta(hours=1))
    )

    preview = await client.get(f"/invites/{invite['token']}")
    assert preview.json()["valid"] is False
    accept = await client.post(f"/invites/{invite['token']}/accept", headers=guest.headers)
    assert accept.status_code == 409
    assert accept.json()["code"] == "invite_expired"
