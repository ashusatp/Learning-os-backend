import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal

logger = logging.getLogger(__name__)


class GoalRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, goal_id: UUID):
        result = await self.db.get(Goal, goal_id)
        return result

    async def get_by_user(self, user_id: UUID, include_archived: bool = False):
        query = select(Goal).where(Goal.user_id == user_id)
        if not include_archived:
            query = query.where(Goal.is_archived == False)
        query = query.order_by(Goal.created_at)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, goal: Goal):
        self.db.add(goal)
        await self.db.flush()
        return goal

    async def update(self, goal: Goal):
        await self.db.flush()
        return goal

    async def delete(self, goal: Goal):
        await self.db.delete(goal)
        await self.db.flush()
