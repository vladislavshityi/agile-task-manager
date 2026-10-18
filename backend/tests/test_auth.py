import httpx

from tests.conftest import Account, RegisterUser

PAYLOAD = {"email": "Ann@Example.com", "password": "password123", "full_name": "Ann"}


async def test_register_returns_token_user_and_personal_workspace(client: httpx.AsyncClient):
    response = await client.post("/auth/register", json=PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "ann@example.com"
    assert "password_hash" not in body["user"]

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    workspaces = (await client.get("/workspaces", headers=headers)).json()
    assert [w["role"] for w in workspaces] == ["owner"]


async def test_register_validates_password_length(client: httpx.AsyncClient):
    response = await client.post("/auth/register", json={**PAYLOAD, "password": "short"})
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_duplicate_email_conflicts(client: httpx.AsyncClient):
    await client.post("/auth/register", json=PAYLOAD)
    response = await client.post("/auth/register", json={**PAYLOAD, "email": "ann@example.com"})
    assert response.status_code == 409
    assert response.json() == {"detail": "Email is already registered", "code": "email_taken"}


async def test_login_and_me(client: httpx.AsyncClient):
    await client.post("/auth/register", json=PAYLOAD)
    response = await client.post(
        "/auth/login", json={"email": "ann@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    me = await client.get("/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "ann@example.com"


async def test_login_with_bad_credentials_is_401(client: httpx.AsyncClient):
    await client.post("/auth/register", json=PAYLOAD)
    wrong_password = await client.post(
        "/auth/login", json={"email": "ann@example.com", "password": "nope-nope"}
    )
    unknown_user = await client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "password123"}
    )
    for response in (wrong_password, unknown_user):
        assert response.status_code == 401
        assert response.json()["code"] == "invalid_credentials"


async def test_me_requires_valid_token(client: httpx.AsyncClient):
    missing = await client.get("/users/me")
    invalid = await client.get("/users/me", headers={"Authorization": "Bearer garbage"})
    assert missing.status_code == 401
    assert missing.json()["code"] == "not_authenticated"
    assert invalid.status_code == 401
    assert invalid.json()["code"] == "invalid_token"


async def test_update_profile_and_change_password(client: httpx.AsyncClient, owner: Account):
    updated = await client.patch(
        "/users/me",
        json={"full_name": "New Name", "avatar_color": "#34C759"},
        headers=owner.headers,
    )
    assert updated.json()["full_name"] == "New Name"
    assert updated.json()["avatar_color"] == "#34C759"

    wrong = await client.post(
        "/users/me/password",
        json={"current_password": "bad-bad-bad", "new_password": "brand-new-pass"},
        headers=owner.headers,
    )
    assert wrong.status_code == 422

    changed = await client.post(
        "/users/me/password",
        json={"current_password": "password123", "new_password": "brand-new-pass"},
        headers=owner.headers,
    )
    assert changed.status_code == 204
    login = await client.post(
        "/auth/login", json={"email": owner.email, "password": "brand-new-pass"}
    )
    assert login.status_code == 200


async def test_workspaces_are_isolated_between_users(
    client: httpx.AsyncClient, register_user: RegisterUser
):
    ann = await register_user("ann")
    bob = await register_user("bob")
    assert ann.workspace_id != bob.workspace_id
    workspaces = (await client.get("/workspaces", headers=ann.headers)).json()
    assert [w["id"] for w in workspaces] == [ann.workspace_id]
