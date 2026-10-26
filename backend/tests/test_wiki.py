import httpx

from app.modules.workspaces.models import Role
from tests.conftest import Account, AddMember, RegisterUser


async def _page(client: httpx.AsyncClient, account: Account, title: str, **extra):
    response = await client.post(
        f"/workspaces/{account.workspace_id}/wiki",
        json={"title": title, **extra},
        headers=account.headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _tree(client: httpx.AsyncClient, account: Account, **query):
    response = await client.get(
        f"/workspaces/{account.workspace_id}/wiki", params=query, headers=account.headers
    )
    assert response.status_code == 200, response.text
    return [(p["title"], p["parent_id"], p["position"]) for p in response.json()]


async def test_create_read_update_page(client: httpx.AsyncClient, owner: Account):
    page = await _page(client, owner, "Onboarding", content="# Hello")
    assert page["content"] == "# Hello"
    assert page["created_by"]["id"] == owner.id
    assert page["parent_id"] is None

    response = await client.patch(
        f"/wiki/{page['id']}", json={"content": "Updated"}, headers=owner.headers
    )
    assert response.status_code == 200, response.text
    body = (await client.get(f"/wiki/{page['id']}", headers=owner.headers)).json()
    assert (body["title"], body["content"]) == ("Onboarding", "Updated")
    assert body["updated_at"] >= page["updated_at"]


async def test_tree_positions_and_cascade_delete(client: httpx.AsyncClient, owner: Account):
    root = await _page(client, owner, "Root")
    other = await _page(client, owner, "Other")
    child = await _page(client, owner, "Child", parent_id=root["id"])
    await _page(client, owner, "Grandchild", parent_id=child["id"])
    assert await _tree(client, owner) == [
        ("Root", None, 0),
        ("Child", root["id"], 0),
        ("Grandchild", child["id"], 0),
        ("Other", None, 1),
    ]

    response = await client.delete(f"/wiki/{root['id']}", headers=owner.headers)
    assert response.status_code == 204
    assert await _tree(client, owner) == [("Other", None, 0)]
    assert (await client.get(f"/wiki/{child['id']}", headers=owner.headers)).status_code == 404
    assert other["id"]


async def test_move_page_and_reject_cycles(client: httpx.AsyncClient, owner: Account):
    a = await _page(client, owner, "A")
    b = await _page(client, owner, "B")
    a_child = await _page(client, owner, "A1", parent_id=a["id"])

    response = await client.post(
        f"/wiki/{a['id']}/move",
        json={"parent_id": a_child["id"], "position": 0},
        headers=owner.headers,
    )
    assert response.status_code == 422
    assert response.json()["code"] == "wiki_cyclic_parent"

    response = await client.post(
        f"/wiki/{b['id']}/move", json={"parent_id": a["id"], "position": 0}, headers=owner.headers
    )
    assert response.status_code == 200, response.text
    assert await _tree(client, owner) == [
        ("A", None, 0),
        ("B", a["id"], 0),
        ("A1", a["id"], 1),
    ]


async def test_search(client: httpx.AsyncClient, owner: Account):
    await _page(client, owner, "Deploy", content="Run docker compose up")
    await _page(client, owner, "Holidays", content="Office closed")
    assert [t for t, _, _ in await _tree(client, owner, q="DOCKER")] == ["Deploy"]


async def test_roles_and_isolation(
    client: httpx.AsyncClient, register_user: RegisterUser, add_member: AddMember, owner: Account
):
    page = await _page(client, owner, "Secret")
    viewer = await register_user("viewer")
    stranger = await register_user("stranger")
    await add_member(owner, viewer, Role.viewer)

    assert (await client.get(f"/wiki/{page['id']}", headers=viewer.headers)).status_code == 200
    response = await client.patch(
        f"/wiki/{page['id']}", json={"title": "Hacked"}, headers=viewer.headers
    )
    assert response.status_code == 403
    response = await client.post(
        f"/workspaces/{owner.workspace_id}/wiki", json={"title": "x"}, headers=viewer.headers
    )
    assert response.status_code == 403

    assert (await client.get(f"/wiki/{page['id']}", headers=stranger.headers)).status_code == 404
    response = await client.post(
        f"/workspaces/{stranger.workspace_id}/wiki",
        json={"title": "x", "parent_id": page["id"]},
        headers=stranger.headers,
    )
    assert response.status_code == 404
