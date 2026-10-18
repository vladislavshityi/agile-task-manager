from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ValidationError
from app.core.security import hash_password, verify_password
from app.modules.users.models import User
from app.modules.users.schemas import PasswordChange, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.avatar_color is not None:
            user.avatar_color = data.avatar_color
        await self.session.commit()
        return user

    async def change_password(self, user: User, data: PasswordChange) -> None:
        if not verify_password(data.current_password, user.password_hash):
            raise ValidationError("Current password is incorrect", "wrong_password")
        user.password_hash = hash_password(data.new_password)
        await self.session.commit()
