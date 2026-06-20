from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.subtopic_repository import SubTopicRepository
from app.services.mistake_service import MistakeService


def get_mistake_repository(
    db: AsyncSession = Depends(get_db),
):
    return MistakeRepository(db)


def get_subtopic_repository_for_mistakes(
    db: AsyncSession = Depends(get_db),
):
    return SubTopicRepository(db)


def get_mistake_service(
    mistake_repository: MistakeRepository = Depends(get_mistake_repository),
    subtopic_repository: SubTopicRepository = Depends(get_subtopic_repository_for_mistakes),
):
    return MistakeService(mistake_repository, subtopic_repository)
