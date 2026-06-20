import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account

logger = logging.getLogger(__name__)


class AccountRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: UUID):
        query = select(Account).where(Account.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, account: Account):
        self.db.add(account)
        await self.db.flush()
        return account

    async def update(self, account: Account):
        await self.db.flush()
        return account
