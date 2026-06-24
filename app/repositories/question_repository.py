import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import Question
from app.models.subtopic import SubTopic
from app.models.topic import Topic
from app.models.subject import Subject


logger = logging.getLogger(__name__)


class QuestionRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, question_id: UUID):
        query = (
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.id == question_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_subtopic(self, subtopic_id: UUID):
        query = (
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.subtopic_id == subtopic_id)
            .order_by(Question.order, Question.created_at)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_subtopic_paginated(self, subtopic_id: UUID, limit: int, offset: int):
        count_query = select(func.count()).select_from(Question).where(Question.subtopic_id == subtopic_id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        query = (
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.subtopic_id == subtopic_id)
            .order_by(Question.order, Question.created_at)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_by_goal_paginated(
        self,
        goal_id,
        limit: int,
        offset: int,
        subject_id=None,
        topic_id=None,
        subtopic_id=None,
        question_type=None,
        difficulty=None,
        is_pyq=None,
    ):
        base = (
            select(Question)
            .join(SubTopic, Question.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(Subject.goal_id == goal_id)
        )

        if subject_id:
            base = base.where(Subject.id == subject_id)
        if topic_id:
            base = base.where(Topic.id == topic_id)
        if subtopic_id:
            base = base.where(SubTopic.id == subtopic_id)
        if question_type:
            base = base.where(Question.question_type == question_type)
        if difficulty:
            base = base.where(Question.difficulty == difficulty)
        if is_pyq is not None:
            base = base.where(Question.is_pyq == is_pyq)

        count_result = await self.db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar()

        # Get paginated question IDs
        ids_query = (
            base.with_only_columns(Question.id)
            .order_by(Question.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        ids_result = await self.db.execute(ids_query)
        question_ids = [r[0] for r in ids_result.all()]

        if not question_ids:
            return [], total

        # Load full questions with options + location info
        query = (
            select(
                Question,
                Subject.id.label("subject_id"),
                Subject.name.label("subject_name"),
                Topic.id.label("topic_id"),
                Topic.name.label("topic_name"),
                SubTopic.name.label("subtopic_name"),
            )
            .join(SubTopic, Question.subtopic_id == SubTopic.id)
            .join(Topic, SubTopic.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .options(selectinload(Question.options))
            .where(Question.id.in_(question_ids))
            .order_by(Question.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.all(), total

    async def create(self, question: Question):
        self.db.add(question)
        await self.db.flush()
        return question

    async def update(self, question: Question):
        await self.db.flush()
        return question

    async def delete(self, question: Question):
        await self.db.delete(question)
        await self.db.flush()
