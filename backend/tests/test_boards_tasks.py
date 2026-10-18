import httpx
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspaces.models import Role
from tests.conftest import Account, AddMember, BoardFixture, RegisterUser


async def _task(client: httpx.AsyncClient, account: Account, column_id: str, title: str, **extra):
    response = await client.post(
        f"/columns/{column_id}/tasks", json={"title": title, **extra}, headers=account.headers
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _column_titles(client: httpx.AsyncClient, account: Account, board_id: str):
    body = (await client.get(f"/boards/{board_id}", headers=account.headers)).json()
    return {c["name"]: [(t["title"], t["position"]) for t in c["tasks"]] for c in body["columns"]}


async def test_create_board_has_default_columns(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    body = (await client.get(f"/boards/{board.id}", headers=owner.headers)).json()
    assert [(c["name"], c["position"]) for c in body["columns"]] == [
        ("To do", 0),
        ("In progress", 1),
        ("Done", 2),
    ]
    assert all(c["tasks"] == [] for c in body["columns"])


async def test_board_load_shape_and_query_count(
    client: httpx.AsyncClient,
    session: AsyncSession,
    register_user: RegisterUser,
    add_member: AddMember,
    owner: Account,
    board: BoardFixture,
):
    teammate = await register_user("teammate")
    await add_member(owner, teammate, Role.member)
    label = (
        await client.post(
            f"/workspaces/{owner.workspace_id}/labels",
            json={"name": "bug", "color": "#FF3B30"},
            headers=owner.headers,
        )
    ).json()
    for column_id in board.column_ids:
        for index in range(3):
            await _task(
                client,
                owner,
                column_id,
                f"t{index}",
                assignee_ids=[owner.id, teammate.id],
                label_ids=[label["id"]],
                priority="high",
                due_date="2030-01-02",
            )

    statements: list[str] = []

    def record(conn, cursor, statement, *args):
        statements.append(statement)

    sync_engine = session.bind.sync_engine if session.bind else session.get_bind()
    event.listen(sync_engine, "before_cursor_execute", record)
    try:
        response = await client.get(f"/boards/{board.id}", headers=owner.headers)
    finally:
        event.remove(sync_engine, "before_cursor_execute", record)

    body = response.json()
    assert set(body) >= {"id", "workspace_id", "name", "description", "columns"}
    first_task = body["columns"][0]["tasks"][0]
    assert set(first_task) >= {
        "id",
        "column_id",
        "title",
        "description",
        "priority",
        "due_date",
        "position",
        "created_at",
        "updated_at",
        "created_by",
        "assignees",
        "labels",
    }
    assert first_task["priority"] == "high"
    assert {u["id"] for u in first_task["assignees"]} == {owner.id, teammate.id}
    assert first_task["labels"] == [label]
    assert [t["position"] for t in body["columns"][1]["tasks"]] == [0, 1, 2]
    select_statements = [s for s in statements if s.lstrip().upper().startswith("SELECT")]
    assert len(select_statements) <= 9, select_statements


async def test_list_boards_has_task_count(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    await _task(client, owner, board.column_ids[0], "a")
    await _task(client, owner, board.column_ids[2], "b")
    boards = (
        await client.get(f"/workspaces/{owner.workspace_id}/boards", headers=owner.headers)
    ).json()
    assert [(b["name"], b["task_count"]) for b in boards] == [("Roadmap", 2)]


async def test_new_tasks_append_to_column_end(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    tasks = [await _task(client, owner, board.column_ids[0], f"t{i}") for i in range(3)]
    assert [t["position"] for t in tasks] == [0, 1, 2]


async def test_move_task_across_columns_renumbers_both(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    todo, doing, _ = board.column_ids
    _, b, _ = [await _task(client, owner, todo, name) for name in "abc"]
    for name in "xy":
        await _task(client, owner, doing, name)

    response = await client.post(
        f"/tasks/{b['id']}/move", json={"column_id": doing, "position": 1}, headers=owner.headers
    )
    assert response.status_code == 200
    assert response.json()["column_id"] == doing
    assert response.json()["position"] == 1

    assert await _column_titles(client, owner, board.id) == {
        "To do": [("a", 0), ("c", 1)],
        "In progress": [("x", 0), ("b", 1), ("y", 2)],
        "Done": [],
    }


async def test_move_task_within_column(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    todo = board.column_ids[0]
    tasks = [await _task(client, owner, todo, name) for name in "abcd"]

    await client.post(
        f"/tasks/{tasks[0]['id']}/move",
        json={"column_id": todo, "position": 2},
        headers=owner.headers,
    )
    assert (await _column_titles(client, owner, board.id))["To do"] == [
        ("b", 0),
        ("c", 1),
        ("a", 2),
        ("d", 3),
    ]

    await client.post(
        f"/tasks/{tasks[3]['id']}/move",
        json={"column_id": todo, "position": 0},
        headers=owner.headers,
    )
    assert (await _column_titles(client, owner, board.id))["To do"] == [
        ("d", 0),
        ("b", 1),
        ("c", 2),
        ("a", 3),
    ]


async def test_move_position_beyond_end_is_clamped(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    todo, doing, _ = board.column_ids
    a = await _task(client, owner, todo, "a")
    await _task(client, owner, doing, "x")
    response = await client.post(
        f"/tasks/{a['id']}/move", json={"column_id": doing, "position": 99}, headers=owner.headers
    )
    assert response.json()["position"] == 1
    assert (await _column_titles(client, owner, board.id))["To do"] == []


async def test_move_to_column_on_another_board_is_rejected(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    other = (
        await client.post(
            f"/workspaces/{owner.workspace_id}/boards",
            json={"name": "Other"},
            headers=owner.headers,
        )
    ).json()
    task = await _task(client, owner, board.column_ids[0], "a")
    response = await client.post(
        f"/tasks/{task['id']}/move",
        json={"column_id": other["columns"][0]["id"], "position": 0},
        headers=owner.headers,
    )
    assert response.status_code == 422
    assert response.json()["code"] == "column_not_in_board"
    assert (await _column_titles(client, owner, board.id))["To do"] == [("a", 0)]


async def test_delete_task_renumbers_column(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    tasks = [await _task(client, owner, board.column_ids[0], name) for name in "abc"]
    assert (
        await client.delete(f"/tasks/{tasks[0]['id']}", headers=owner.headers)
    ).status_code == 204
    assert (await _column_titles(client, owner, board.id))["To do"] == [("b", 0), ("c", 1)]


async def test_move_and_delete_column_keep_positions_contiguous(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    todo, _, done = board.column_ids
    moved = await client.post(f"/columns/{done}/move", json={"position": 0}, headers=owner.headers)
    assert moved.status_code == 200
    body = (await client.get(f"/boards/{board.id}", headers=owner.headers)).json()
    assert [(c["name"], c["position"]) for c in body["columns"]] == [
        ("Done", 0),
        ("To do", 1),
        ("In progress", 2),
    ]
    await client.delete(f"/columns/{todo}", headers=owner.headers)
    body = (await client.get(f"/boards/{board.id}", headers=owner.headers)).json()
    assert [(c["name"], c["position"]) for c in body["columns"]] == [
        ("Done", 0),
        ("In progress", 1),
    ]


async def test_update_task_fields_assignees_and_due_date(
    client: httpx.AsyncClient, owner: Account, board: BoardFixture
):
    task = await _task(client, owner, board.column_ids[0], "a", due_date="2030-05-05")
    updated = await client.patch(
        f"/tasks/{task['id']}",
        json={"title": "renamed", "due_date": None, "assignee_ids": [owner.id]},
        headers=owner.headers,
    )
    body = updated.json()
    assert body["title"] == "renamed"
    assert body["due_date"] is None
    assert [u["id"] for u in body["assignees"]] == [owner.id]


async def test_assignee_must_be_workspace_member(
    client: httpx.AsyncClient, register_user: RegisterUser, owner: Account, board: BoardFixture
):
    stranger = await register_user("stranger")
    response = await client.post(
        f"/columns/{board.column_ids[0]}/tasks",
        json={"title": "a", "assignee_ids": [stranger.id]},
        headers=owner.headers,
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_assignees"


async def test_comments_flow_and_permissions(
    client: httpx.AsyncClient,
    register_user: RegisterUser,
    add_member: AddMember,
    owner: Account,
    board: BoardFixture,
):
    member = await register_user("member")
    other = await register_user("other")
    await add_member(owner, member, Role.member)
    await add_member(owner, other, Role.member)
    task = await _task(client, owner, board.column_ids[0], "a")

    comment = await client.post(
        f"/tasks/{task['id']}/comments", json={"body": "hello"}, headers=member.headers
    )
    assert comment.status_code == 201
    assert comment.json()["author"]["id"] == member.id

    detail = (await client.get(f"/tasks/{task['id']}", headers=owner.headers)).json()
    assert [c["body"] for c in detail["comments"]] == ["hello"]

    comment_id = comment.json()["id"]
    assert (
        await client.delete(f"/comments/{comment_id}", headers=other.headers)
    ).status_code == 403
    assert (
        await client.delete(f"/comments/{comment_id}", headers=owner.headers)
    ).status_code == 204


async def test_my_tasks_filters(
    client: httpx.AsyncClient,
    owner: Account,
    register_user: RegisterUser,
    add_member: AddMember,
    board: BoardFixture,
):
    todo = board.column_ids[0]
    await _task(client, owner, todo, "early", assignee_ids=[owner.id], due_date="2030-01-10")
    await _task(client, owner, todo, "late", assignee_ids=[owner.id], due_date="2030-03-10")
    await _task(client, owner, todo, "undated", assignee_ids=[owner.id])
    await _task(client, owner, todo, "unassigned", due_date="2030-01-10")

    everything = (await client.get("/me/tasks", headers=owner.headers)).json()
    assert [t["title"] for t in everything] == ["early", "late", "undated"]
    assert everything[0]["board_name"] == "Roadmap"
    assert everything[0]["column_name"] == "To do"
    assert everything[0]["board_id"] == board.id

    ranged = (
        await client.get(
            "/me/tasks",
            params={"due_from": "2030-02-01", "due_to": "2030-12-31"},
            headers=owner.headers,
        )
    ).json()
    assert [t["title"] for t in ranged] == ["late"]

    other_workspace = (
        await client.post("/workspaces", json={"name": "Other"}, headers=owner.headers)
    ).json()
    scoped = (
        await client.get(
            "/me/tasks", params={"workspace_id": other_workspace["id"]}, headers=owner.headers
        )
    ).json()
    assert scoped == []

    teammate = await register_user("teammate")
    assert (await client.get("/me/tasks", headers=teammate.headers)).json() == []


async def test_removed_member_loses_assignments(
    client: httpx.AsyncClient,
    register_user: RegisterUser,
    add_member: AddMember,
    owner: Account,
    board: BoardFixture,
):
    member = await register_user("member")
    await add_member(owner, member, Role.member)
    await _task(client, owner, board.column_ids[0], "a", assignee_ids=[member.id])
    await client.delete(
        f"/workspaces/{owner.workspace_id}/members/{member.id}", headers=owner.headers
    )
    body = (await client.get(f"/boards/{board.id}", headers=owner.headers)).json()
    assert body["columns"][0]["tasks"][0]["assignees"] == []
