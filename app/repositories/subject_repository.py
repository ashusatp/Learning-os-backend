import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject

logger = logging.getLogger(__name__)


class SubjectRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, subject_id: UUID):
        result = await self.db.get(Subject, subject_id)
        return result

    async def get_by_goal(self, goal_id: UUID):
        query = select(Subject).where(
            Subject.goal_id == goal_id
        ).order_by(Subject.order, Subject.created_at)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, subject: Subject):
        self.db.add(subject)
        await self.db.flush()
        return subject

    async def update(self, subject: Subject):
        await self.db.flush()
        return subject

    async def delete(self, subject: Subject):
        await self.db.delete(subject)
        await self.db.flush()
