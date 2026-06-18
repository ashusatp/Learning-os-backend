import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID):
        result = await self.db.get(User, user_id)
        return result

    async def get_by_email(self, email: str):
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self):
        query = select(User).order_by(User.created_at)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_provider(self, provider: str, provider_id: str):
        result = await self.db.execute(
            select(User).where(
                User.auth_provider == provider,
                User.auth_provider_id == provider_id,
            )
        )
        return result.scalars().first()

    async def create(self, user: User):
        self.db.add(user)
        await self.db.flush()
        return user

    async def update(self, user: User):
        await self.db.flush()
        return user

    async def delete(self, user: User):
        await self.db.delete(user)
        await self.db.flush()
