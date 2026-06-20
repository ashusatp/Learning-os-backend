import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import Question


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
