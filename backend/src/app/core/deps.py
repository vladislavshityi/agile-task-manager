from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import Unauthorized
from app.core.security import decode_access_token
from app.modules.users.models import User
from app.modules.users.repository import UserRepository

SessionDep = Annotated[AsyncSession, Depends(get_session)]
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise Unauthorized("Not authenticated", "not_authenticated")
    user = await UserRepository(session).get(decode_access_token(credentials.credentials))
    if user is None:
        raise Unauthorized("User no longer exists", "invalid_token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
