from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.core.config import get_settings
from app.core.db import get_engine
from app.core.errors import register_exception_handlers
from app.modules.ai.router import router as ai_router
from app.modules.auth.router import router as auth_router
from app.modules.boards.router import router as boards_router
from app.modules.tasks.router import router as tasks_router
from app.modules.users.router import router as users_router
from app.modules.workspaces.router import router as workspaces_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await get_engine().dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Agile Task Manager API", version="2.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    api = APIRouter(prefix="/api")
    for router in (
        auth_router,
        users_router,
        workspaces_router,
        boards_router,
        tasks_router,
        ai_router,
    ):
        api.include_router(router)

    @api.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api)
    return app


app = create_app()
