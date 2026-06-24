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

    async def get_by_goal_paginated(
        self,
        goal_id,
        limit: int,
        offset: int,
        resolved: bool | None = None,
        subject_id=None,
        topic_id=None,
        subtopic_id=None,
        mistake_type=None,
    ):
        base = (
            select(Mistake)
            .join(SubTopic, Mistake.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(Subject.goal_id == goal_id)
        )

        if resolved is not None:
            base = base.where(Mistake.is_resolved == resolved)
        if subject_id:
            base = base.where(Subject.id == subject_id)
        if topic_id:
            base = base.where(Topic.id == topic_id)
        if subtopic_id:
            base = base.where(SubTopic.id == subtopic_id)
        if mistake_type:
            base = base.where(Mistake.mistake_type == mistake_type)

        count_result = await self.db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar()

        ids_query = (
            base.with_only_columns(Mistake.id)
            .order_by(Mistake.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        ids_result = await self.db.execute(ids_query)
        mistake_ids = [r[0] for r in ids_result.all()]

        if not mistake_ids:
            return [], total

        query = (
            select(
                Mistake,
                Subject.id.label("subject_id"),
                Subject.name.label("subject_name"),
                Topic.id.label("topic_id"),
                Topic.name.label("topic_name"),
                SubTopic.name.label("subtopic_name"),
            )
            .join(SubTopic, Mistake.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(Mistake.id.in_(mistake_ids))
            .order_by(Mistake.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.all(), total

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
