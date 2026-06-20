import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mistake import Mistake
from app.models.subtopic import SubTopic
from app.models.topic import Topic
from app.models.subject import Subject


logger = logging.getLogger(__name__)


class MistakeRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, mistake_id: UUID):
        query = select(Mistake).where(Mistake.id == mistake_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_subtopic(self, subtopic_id: UUID, resolved: bool | None = None):
        query = (
            select(Mistake)
            .where(Mistake.subtopic_id == subtopic_id)
            .order_by(Mistake.created_at.desc())
        )
        if resolved is not None:
            query = query.where(Mistake.is_resolved == resolved)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_subtopic_paginated(
        self, subtopic_id: UUID, resolved: bool | None, limit: int, offset: int
    ):
        base = select(Mistake).where(Mistake.subtopic_id == subtopic_id)
        if resolved is not None:
            base = base.where(Mistake.is_resolved == resolved)

        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar()

        query = base.order_by(Mistake.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_by_goal(self, goal_id: UUID, resolved: bool | None = None):
        query = (
            select(Mistake)
            .join(SubTopic, Mistake.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(Subject.goal_id == goal_id)
            .order_by(Mistake.created_at.desc())
        )
        if resolved is not None:
            query = query.where(Mistake.is_resolved == resolved)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, mistake: Mistake):
        self.db.add(mistake)
        await self.db.flush()
        return mistake

    async def update(self, mistake: Mistake):
        await self.db.flush()
        return mistake

    async def delete(self, mistake: Mistake):
        await self.db.delete(mistake)
        await self.db.flush()
