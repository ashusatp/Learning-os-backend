import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subtopic import SubTopic

logger = logging.getLogger(__name__)


class SubTopicRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, subtopic_id: UUID):
        query = (
            select(SubTopic)
            .options(selectinload(SubTopic.files))
            .where(SubTopic.id == subtopic_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_topic(self, topic_id: UUID):
        query = (
            select(SubTopic)
            .options(selectinload(SubTopic.files))
            .where(SubTopic.topic_id == topic_id)
            .order_by(SubTopic.order, SubTopic.created_at)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, subtopic: SubTopic):
        self.db.add(subtopic)
        await self.db.flush()
        return subtopic

    async def update(self, subtopic: SubTopic):
        await self.db.flush()
        return subtopic

    async def delete(self, subtopic: SubTopic):
        await self.db.delete(subtopic)
        await self.db.flush()
