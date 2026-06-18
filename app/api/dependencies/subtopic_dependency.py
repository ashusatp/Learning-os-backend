from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.subtopic_repository import SubTopicRepository
from app.repositories.topic_repository import TopicRepository
from app.services.subtopic_service import SubTopicService


def get_subtopic_repository(
    db: AsyncSession = Depends(get_db),
):
    return SubTopicRepository(db)


def get_topic_repository(
    db: AsyncSession = Depends(get_db),
):
    return TopicRepository(db)


def get_subtopic_service(
    subtopic_repository: SubTopicRepository = Depends(get_subtopic_repository),
    topic_repository: TopicRepository = Depends(get_topic_repository),
):
    return SubTopicService(subtopic_repository, topic_repository)
