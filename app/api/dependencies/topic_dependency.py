from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.subject_repository import SubjectRepository
from app.repositories.topic_repository import TopicRepository
from app.services.topic_service import TopicService


def get_topic_repository(
    db: AsyncSession = Depends(get_db),
):
    return TopicRepository(db)


def get_subject_repository(
    db: AsyncSession = Depends(get_db),
):
    return SubjectRepository(db)


def get_topic_service(
    topic_repository: TopicRepository = Depends(get_topic_repository),
    subject_repository: SubjectRepository = Depends(get_subject_repository),
):
    return TopicService(topic_repository, subject_repository)
