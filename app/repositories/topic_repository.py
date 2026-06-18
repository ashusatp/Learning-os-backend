import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic

logger = logging.getLogger(__name__)


class TopicRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, topic_id: UUID):
        result = await self.db.get(Topic, topic_id)
        return result

    async def get_by_subject(self, subject_id: UUID):
        query = select(Topic).where(
            Topic.subject_id == subject_id
        ).order_by(Topic.order, Topic.created_at)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, topic: Topic):
        self.db.add(topic)
        await self.db.flush()
        return topic

    async def update(self, topic: Topic):
        await self.db.flush()
        return topic

    async def delete(self, topic: Topic):
        await self.db.delete(topic)
        await self.db.flush()
