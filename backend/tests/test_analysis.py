import httpx

from app.modules.workspaces.models import Role
from tests.conftest import Account, AddMember, RegisterUser

SPEC = """# Требования

Система хранит задачи.

## Роли
Поддерживаются роли:
- владелец
- участник
"""


async def _create(client: httpx.AsyncClient, account: Account, text: str = SPEC, title="ТЗ"):
    response = await client.post(
        f"/workspaces/{account.workspace_id}/analyses",
        json={"title": title, "text": text},
        headers=account.headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _teammate(
    register_user: RegisterUser, add_member: AddMember, owner: Account, name: str, role: Role
) -> Account:
    account = await register_user(name)
    await add_member(owner, account, role)
    # users act inside the owner's workspace
    return Account(account.id, account.email, account.headers, owner.workspace_id)


async def _ids(client: httpx.AsyncClient, account: Account) -> dict[str, str]:
    response = await client.get(
        f"/workspaces/{account.workspace_id}/analyses", headers=account.headers
    )
    assert response.status_code == 200, response.text
    return {a["id"]: a["access"] for a in response.json()}


async def test_create_and_get_with_fragments(client: httpx.AsyncClient, owner: Account):
    created = await _create(client, owner, title="  Мой проект  ")
    assert created["title"] == "Мой проект"
    assert created["visibility"] == "private"
    assert created["access"] == "manage"
    assert created["created_by"]["id"] == owner.id
    assert created["fragment_count"] == 5

    body = (await client.get(f"/analyses/{created['id']}", headers=owner.headers)).json()
    fragments = body["fragments"]
    assert [f["ordinal"] for f in fragments] == [1, 2, 3, 4, 5]
    assert [f["kind"] for f in fragments] == [
        "heading",
        "paragraph",
        "heading",
        "list_item",
        "list_item",
    ]
    assert fragments[3]["context"] == "Поддерживаются роли:"
    assert fragments[3]["section"] == "1.1"
    assert fragments[3]["heading_path"] == "Требования → Роли"
    for f in fragments:
        assert body["text"][f["start"] : f["end"]] == f["text"]

    summary = (
        await client.get(f"/workspaces/{owner.workspace_id}/analyses", headers=owner.headers)
    ).json()
    assert [(a["id"], a["fragment_count"]) for a in summary] == [(created["id"], 5)]
    assert "text" not in summary[0]


async def test_viewer_cannot_create(
    client: httpx.AsyncClient, owner: Account, register_user: RegisterUser, add_member: AddMember
):
    viewer = await _teammate(register_user, add_member, owner, "viewer", Role.viewer)
    response = await client.post(
        f"/workspaces/{owner.workspace_id}/analyses",
        json={"title": "X", "text": "Текст."},
        headers=viewer.headers,
    )
    assert response.status_code == 403
    assert response.json()["code"] == "insufficient_role"


async def test_private_analysis_hidden_from_other_member(
    client: httpx.AsyncClient, owner: Account, register_user: RegisterUser, add_member: AddMember
):
    member = await _teammate(register_user, add_member, owner, "member", Role.member)
    analysis = await _create(client, member)
    other = await _teammate(register_user, add_member, owner, "other", Role.member)

    response = await client.get(f"/analyses/{analysis['id']}", headers=other.headers)
    assert (response.status_code, response.json()["code"]) == (404, "analysis_not_found")
    assert await _ids(client, other) == {}
    assert await _ids(client, member) == {analysis["id"]: "manage"}


async def test_workspace_visibility_gives_read_to_viewer(
    client: httpx.AsyncClient, owner: Account, register_user: RegisterUser, add_member: AddMember
):
    viewer = await _teammate(register_user, add_member, owner, "viewer", Role.viewer)
    analysis = await _create(client, owner)
    assert await _ids(client, viewer) == {}

    patched = await client.patch(
        f"/analyses/{analysis['id']}", json={"visibility": "workspace"}, headers=owner.headers
    )
    assert patched.status_code == 200, patched.text
    assert await _ids(client, viewer) == {analysis["id"]: "read"}
    body = (await client.get(f"/analyses/{analysis['id']}", headers=viewer.headers)).json()
    assert body["access"] == "read"

    denied = await client.patch(
        f"/analyses/{analysis['id']}", json={"title": "Взлом"}, headers=viewer.headers
    )
    assert (denied.status_code, denied.json()["code"]) == (403, "analysis_access_denied")


async def test_member_with_can_edit_gets_edit_but_not_manage(
    client: httpx.AsyncClient, owner: Account, register_user: RegisterUser, add_member: AddMember
):
    member = await _teammate(register_user, add_member, owner, "member", Role.member)
    analysis = await _create(client, owner)

    response = await client.put(
        f"/analyses/{analysis['id']}/members/{member.id}",
        json={"can_edit": True},
        headers=owner.headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["can_edit"] is True
    assert response.json()["user"]["id"] == member.id
    assert await _ids(client, member) == {analysis["id"]: "edit"}

    patch = await client.patch(
        f"/analyses/{analysis['id']}", json={"title": "Новое"}, headers=member.headers
    )
    assert (patch.status_code, patch.json()["code"]) == (403, "analysis_access_denied")
    delete = await client.delete(f"/analyses/{analysis['id']}", headers=member.headers)
    assert (delete.status_code, delete.json()["code"]) == (403, "analysis_access_denied")

    body = (await client.get(f"/analyses/{analysis['id']}", headers=owner.headers)).json()
    assert [(m["user"]["id"], m["can_edit"]) for m in body["members"]] == [(member.id, True)]

    await client.put(
        f"/analyses/{analysis['id']}/members/{member.id}",
        json={"can_edit": False},
        headers=owner.headers,
    )
    assert await _ids(client, member) == {analysis["id"]: "read"}

    removed = await client.delete(
        f"/analyses/{analysis['id']}/members/{member.id}", headers=owner.headers
    )
    assert removed.status_code == 204
    assert await _ids(client, member) == {}
    again = await client.delete(
        f"/analyses/{analysis['id']}/members/{member.id}", headers=owner.headers
    )
    assert (again.status_code, again.json()["code"]) == (404, "analysis_member_not_found")


async def test_viewer_with_can_edit_only_reads(
    client: httpx.AsyncClient, owner: Account, register_user: RegisterUser, add_member: AddMember
):
    viewer = await _teammate(register_user, add_member, owner, "viewer", Role.viewer)
    analysis = await _create(client, owner)
    await client.put(
        f"/analyses/{analysis['id']}/members/{viewer.id}",
        json={"can_edit": True},
        headers=owner.headers,
    )
    assert await _ids(client, viewer) == {analysis["id"]: "read"}


async def test_admin_sees_foreign_private_and_manages(
    client: httpx.AsyncClient, owner: Account, register_user: RegisterUser, add_member: AddMember
):
    author = await _teammate(register_user, add_member, owner, "author", Role.member)
    admin = await _teammate(register_user, add_member, owner, "admin", Role.admin)
    analysis = await _create(client, author)

    assert await _ids(client, admin) == {analysis["id"]: "manage"}
    patched = await client.patch(
        f"/analyses/{analysis['id']}", json={"title": "Правка"}, headers=admin.headers
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["title"] == "Правка"
    assert (
        await client.delete(f"/analyses/{analysis['id']}", headers=admin.headers)
    ).status_code == 204
    assert (
        await client.get(f"/analyses/{analysis['id']}", headers=owner.headers)
    ).status_code == 404


async def test_member_validation(
    client: httpx.AsyncClient, owner: Account, register_user: RegisterUser
):
    outsider = await register_user("outsider")
    analysis = await _create(client, owner)

    response = await client.put(
        f"/analyses/{analysis['id']}/members/{outsider.id}",
        json={"can_edit": True},
        headers=owner.headers,
    )
    assert (response.status_code, response.json()["code"]) == (422, "user_not_member")

    response = await client.put(
        f"/analyses/{analysis['id']}/members/{owner.id}",
        json={"can_edit": True},
        headers=owner.headers,
    )
    assert (response.status_code, response.json()["code"]) == (422, "author_is_member")


async def test_patch_cannot_change_text(client: httpx.AsyncClient, owner: Account):
    analysis = await _create(client, owner)
    response = await client.patch(
        f"/analyses/{analysis['id']}",
        json={"title": "Другое", "text": "Подмена."},
        headers=owner.headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["title"] == "Другое"
    assert response.json()["text"] == analysis["text"]
    assert response.json()["fragments"] == analysis["fragments"]


async def test_empty_specs_are_rejected(client: httpx.AsyncClient, owner: Account):
    for text in ("   \n\n\t ", "# Только заголовок\n\n## Ещё один"):
        response = await client.post(
            f"/workspaces/{owner.workspace_id}/analyses",
            json={"title": "T", "text": text},
            headers=owner.headers,
        )
        assert (response.status_code, response.json()["code"]) == (422, "spec_empty")


async def test_too_many_fragments(client: httpx.AsyncClient, owner: Account):
    response = await client.post(
        f"/workspaces/{owner.workspace_id}/analyses",
        json={"title": "T", "text": "\n\n".join(["Абзац."] * 2001)},
        headers=owner.headers,
    )
    assert (response.status_code, response.json()["code"]) == (422, "spec_too_many_fragments")


async def test_non_member_gets_404(
    client: httpx.AsyncClient, owner: Account, register_user: RegisterUser
):
    stranger = await register_user("stranger")
    analysis = await _create(client, owner)

    assert (
        await client.get(f"/analyses/{analysis['id']}", headers=stranger.headers)
    ).status_code == 404
    assert (
        await client.patch(
            f"/analyses/{analysis['id']}", json={"title": "X"}, headers=stranger.headers
        )
    ).status_code == 404
    assert (
        await client.get(f"/workspaces/{owner.workspace_id}/analyses", headers=stranger.headers)
    ).status_code == 404
    created = await client.post(
        f"/workspaces/{owner.workspace_id}/analyses",
        json={"title": "X", "text": "Текст."},
        headers=stranger.headers,
    )
    assert created.status_code == 404
