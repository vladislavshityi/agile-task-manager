import asyncio
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.core.config import get_settings
from app.core.db import get_session
from app.main import create_app
from app.modules.workspaces.models import Membership, Role

BACKEND_DIR = Path(__file__).resolve().parents[1]


@dataclass
class Account:
    id: str
    email: str
    headers: dict[str, str]
    workspace_id: str


def _test_url() -> str:
    url = make_url(get_settings().database_url)
    return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    test_url = make_url(_test_url())
    admin = create_async_engine(test_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{test_url.database}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{test_url.database}"'))
    await admin.dispose()

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", test_url.render_as_string(hide_password=False))
    await asyncio.to_thread(command.upgrade, config, "head")

    engine = create_async_engine(test_url)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        ) as db_session:
            yield db_session
        await transaction.rollback()


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest_asyncio.fixture
async def client(app: FastAPI, session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    async def override_session() -> AsyncIterator[AsyncSession]:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

    app.dependency_overrides[get_session] = override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/api") as http:
        yield http


RegisterUser = Callable[[str], Awaitable[Account]]


@pytest.fixture
def register_user(client: httpx.AsyncClient) -> RegisterUser:
    async def register(name: str) -> Account:
        email = f"{name}@example.com"
        response = await client.post(
            "/auth/register",
            json={"email": email, "password": "password123", "full_name": name.title()},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        headers = {"Authorization": f"Bearer {body['access_token']}"}
        workspaces = (await client.get("/workspaces", headers=headers)).json()
        return Account(body["user"]["id"], email, headers, workspaces[0]["id"])

    return register


@pytest_asyncio.fixture
async def owner(register_user: RegisterUser) -> Account:
    return await register_user("owner")


AddMember = Callable[[Account, Account, Role], Awaitable[None]]


@pytest.fixture
def add_member(session: AsyncSession) -> AddMember:
    async def add(workspace_owner: Account, user: Account, role: Role) -> None:
        session.add(
            Membership(
                workspace_id=uuid.UUID(workspace_owner.workspace_id),
                user_id=uuid.UUID(user.id),
                role=role,
            )
        )
        await session.commit()

    return add


@dataclass
class BoardFixture:
    id: str
    column_ids: list[str]


@pytest_asyncio.fixture
async def board(client: httpx.AsyncClient, owner: Account) -> BoardFixture:
    response = await client.post(
        f"/workspaces/{owner.workspace_id}/boards", json={"name": "Roadmap"}, headers=owner.headers
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return BoardFixture(body["id"], [c["id"] for c in body["columns"]])
