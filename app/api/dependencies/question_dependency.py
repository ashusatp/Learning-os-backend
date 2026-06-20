from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.question_repository import QuestionRepository
from app.repositories.subtopic_repository import SubTopicRepository
from app.services.question_service import QuestionService


def get_question_repository(
    db: AsyncSession = Depends(get_db),
):
    return QuestionRepository(db)


def get_subtopic_repository(
    db: AsyncSession = Depends(get_db),
):
    return SubTopicRepository(db)


def get_question_service(
    question_repository: QuestionRepository = Depends(get_question_repository),
    subtopic_repository: SubTopicRepository = Depends(get_subtopic_repository),
):
    return QuestionService(question_repository, subtopic_repository)
