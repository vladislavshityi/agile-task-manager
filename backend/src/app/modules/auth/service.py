import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, Unauthorized
from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserRead
from app.modules.workspaces.repository import WorkspaceRepository

AVATAR_COLORS = ("#FF3B30", "#FF9500", "#34C759", "#007AFF", "#AF52DE", "#8E8E93")


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id), user=UserRead.model_validate(user)
    )


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.workspaces = WorkspaceRepository(session)

    async def register(self, data: RegisterRequest) -> TokenResponse:
        email = data.email.lower()
        if await self.users.get_by_email(email) is not None:
            raise Conflict("Email is already registered", "email_taken")
        user = await self.users.add(
            User(
                email=email,
                password_hash=hash_password(data.password),
                full_name=data.full_name.strip(),
                avatar_color=secrets.choice(AVATAR_COLORS),
            )
        )
        await self.workspaces.add(f"{user.full_name}'s workspace", user.id)
        await self.session.commit()
        return _token_response(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(data.email.lower())
        password_hash = user.password_hash if user else DUMMY_HASH
        if not verify_password(data.password, password_hash) or user is None:
            raise Unauthorized("Invalid email or password", "invalid_credentials")
        return _token_response(user)
