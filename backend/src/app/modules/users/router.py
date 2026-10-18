from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.users.schemas import PasswordChange, UserRead, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdate, user: CurrentUser, session: SessionDep) -> UserRead:
    return UserRead.model_validate(await UserService(session).update_profile(user, data))


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(data: PasswordChange, user: CurrentUser, session: SessionDep) -> Response:
    await UserService(session).change_password(user, data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
