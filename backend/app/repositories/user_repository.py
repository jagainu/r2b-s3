import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        username: str,
        password_hash: str | None = None,
        google_id: str | None = None,
    ) -> User:
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            google_id=google_id,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_google_id(self, user_id: uuid.UUID, google_id: str) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.google_id = google_id
        await self.db.flush()
        await self.db.refresh(user)
        return user
