import httpx

from app.modules.workspaces.models import Role
from tests.conftest import Account, AddMember, BoardFixture, RegisterUser


async def _create_task(client: httpx.AsyncClient, account: Account, column_id: str):
    return await client.post(
        f"/columns/{column_id}/tasks", json={"title": "Task"}, headers=account.headers
    )


async def test_non_member_gets_404_everywhere(
    client: httpx.AsyncClient, register_user: RegisterUser, owner: Account, board: BoardFixture
):
    stranger = await register_user("stranger")
    task = (await _create_task(client, owner, board.column_ids[0])).json()
    h = stranger.headers
    ws = owner.workspace_id

    responses = [
        await client.get(f"/workspaces/{ws}/boards", headers=h),
        await client.get(f"/workspaces/{ws}/members", headers=h),
        await client.get(f"/boards/{board.id}", headers=h),
        await client.get(f"/tasks/{task['id']}", headers=h),
        await client.post(f"/columns/{board.column_ids[0]}/tasks", json={"title": "x"}, headers=h),
        await client.delete(f"/workspaces/{ws}", headers=h),
    ]
    assert [r.status_code for r in responses] == [404] * len(responses)


async def test_viewer_can_read_but_not_write_tasks(
    client: httpx.AsyncClient,
    register_user: RegisterUser,
    add_member: AddMember,
    owner: Account,
    board: BoardFixture,
):
    viewer = await register_user("viewer")
    await add_member(owner, viewer, Role.viewer)
    task = (await _create_task(client, owner, board.column_ids[0])).json()

    assert (await client.get(f"/boards/{board.id}", headers=viewer.headers)).status_code == 200
    assert (await client.get(f"/tasks/{task['id']}", headers=viewer.headers)).status_code == 200

    created = await _create_task(client, viewer, board.column_ids[0])
    assert created.status_code == 403
    assert created.json()["code"] == "insufficient_role"
    moved = await client.post(
        f"/tasks/{task['id']}/move",
        json={"column_id": board.column_ids[1], "position": 0},
        headers=viewer.headers,
    )
    assert moved.status_code == 403
    assert (await client.delete(f"/tasks/{task['id']}", headers=viewer.headers)).status_code == 403


async def test_member_can_manage_tasks_but_not_columns_or_invites(
    client: httpx.AsyncClient,
    register_user: RegisterUser,
    add_member: AddMember,
    owner: Account,
    board: BoardFixture,
):
    member = await register_user("member")
    await add_member(owner, member, Role.member)

    assert (await _create_task(client, member, board.column_ids[0])).status_code == 201
    column = await client.post(
        f"/boards/{board.id}/columns", json={"name": "QA"}, headers=member.headers
    )
    invite = await client.post(
        f"/workspaces/{owner.workspace_id}/invites", json={}, headers=member.headers
    )
    new_board = await client.post(
        f"/workspaces/{owner.workspace_id}/boards", json={"name": "B"}, headers=member.headers
    )
    assert [column.status_code, invite.status_code, new_board.status_code] == [403, 403, 403]


async def test_admin_manages_columns_and_invites(
    client: httpx.AsyncClient,
    register_user: RegisterUser,
    add_member: AddMember,
    owner: Account,
    board: BoardFixture,
):
    admin = await register_user("admin")
    await add_member(owner, admin, Role.admin)

    column = await client.post(
        f"/boards/{board.id}/columns",
        json={"name": "QA", "color": "#FF3B30"},
        headers=admin.headers,
    )
    assert column.status_code == 201
    assert column.json()["position"] == 3
    renamed = await client.patch(
        f"/columns/{column.json()['id']}", json={"name": "Review"}, headers=admin.headers
    )
    assert renamed.json()["name"] == "Review"
    invite = await client.post(
        f"/workspaces/{owner.workspace_id}/invites", json={"role": "viewer"}, headers=admin.headers
    )
    assert invite.status_code == 201
    revoked = await client.delete(
        f"/workspaces/{owner.workspace_id}/invites/{invite.json()['id']}", headers=admin.headers
    )
    assert revoked.status_code == 204
    deleted = await client.delete(f"/columns/{column.json()['id']}", headers=admin.headers)
    assert deleted.status_code == 204


async def test_admin_cannot_invite_as_admin_or_owner(
    client: httpx.AsyncClient, register_user: RegisterUser, add_member: AddMember, owner: Account
):
    admin = await register_user("admin")
    await add_member(owner, admin, Role.admin)
    for role in ("admin", "owner"):
        response = await client.post(
            f"/workspaces/{owner.workspace_id}/invites", json={"role": role}, headers=admin.headers
        )
        assert response.status_code == 403


async def test_only_owner_renames_and_deletes_workspace(
    client: httpx.AsyncClient, register_user: RegisterUser, add_member: AddMember, owner: Account
):
    admin = await register_user("admin")
    await add_member(owner, admin, Role.admin)
    ws = owner.workspace_id

    assert (
        await client.patch(f"/workspaces/{ws}", json={"name": "X"}, headers=admin.headers)
    ).status_code == 403
    assert (await client.delete(f"/workspaces/{ws}", headers=admin.headers)).status_code == 403

    renamed = await client.patch(
        f"/workspaces/{ws}", json={"name": "Renamed"}, headers=owner.headers
    )
    assert renamed.json()["name"] == "Renamed"
    assert (await client.delete(f"/workspaces/{ws}", headers=owner.headers)).status_code == 204
    assert (await client.get(f"/workspaces/{ws}/members", headers=owner.headers)).status_code == 404


async def test_role_changes_respect_hierarchy(
    client: httpx.AsyncClient, register_user: RegisterUser, add_member: AddMember, owner: Account
):
    admin = await register_user("admin")
    member = await register_user("member")
    await add_member(owner, admin, Role.admin)
    await add_member(owner, member, Role.member)
    ws = owner.workspace_id

    promote_by_admin = await client.patch(
        f"/workspaces/{ws}/members/{member.id}", json={"role": "admin"}, headers=admin.headers
    )
    assert promote_by_admin.status_code == 403
    demote_admin_by_admin = await client.patch(
        f"/workspaces/{ws}/members/{owner.id}", json={"role": "viewer"}, headers=admin.headers
    )
    assert demote_admin_by_admin.status_code == 403

    viewer = await client.patch(
        f"/workspaces/{ws}/members/{member.id}", json={"role": "viewer"}, headers=admin.headers
    )
    assert viewer.status_code == 200
    assert viewer.json()["role"] == "viewer"
    promoted = await client.patch(
        f"/workspaces/{ws}/members/{member.id}", json={"role": "admin"}, headers=owner.headers
    )
    assert promoted.json()["role"] == "admin"


async def test_ownership_transfer_and_leaving(
    client: httpx.AsyncClient, register_user: RegisterUser, add_member: AddMember, owner: Account
):
    admin = await register_user("admin")
    await add_member(owner, admin, Role.admin)
    ws = owner.workspace_id

    owner_leave = await client.delete(f"/workspaces/{ws}/members/{owner.id}", headers=owner.headers)
    assert owner_leave.status_code == 403
    assert owner_leave.json()["code"] == "owner_cannot_leave"

    transfer = await client.patch(
        f"/workspaces/{ws}/members/{admin.id}", json={"role": "owner"}, headers=owner.headers
    )
    assert transfer.json()["role"] == "owner"
    members = {
        m["user"]["id"]: m["role"]
        for m in (await client.get(f"/workspaces/{ws}/members", headers=admin.headers)).json()
    }
    assert members == {owner.id: "admin", admin.id: "owner"}

    leave = await client.delete(f"/workspaces/{ws}/members/{owner.id}", headers=owner.headers)
    assert leave.status_code == 204
    assert (await client.get(f"/workspaces/{ws}/boards", headers=owner.headers)).status_code == 404
