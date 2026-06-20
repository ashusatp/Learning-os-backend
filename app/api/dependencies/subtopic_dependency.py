from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.subtopic_repository import SubTopicRepository
from app.repositories.subtopic_file_repository import SubtopicFileRepository
from app.repositories.subtopic_folder_repository import SubtopicFolderRepository
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


def get_subtopic_file_repository(
    db: AsyncSession = Depends(get_db),
):
    return SubtopicFileRepository(db)


def get_subtopic_folder_repository(
    db: AsyncSession = Depends(get_db),
):
    return SubtopicFolderRepository(db)


def get_subtopic_service(
    subtopic_repository: SubTopicRepository = Depends(get_subtopic_repository),
    topic_repository: TopicRepository = Depends(get_topic_repository),
    file_repository: SubtopicFileRepository = Depends(get_subtopic_file_repository),
    folder_repository: SubtopicFolderRepository = Depends(get_subtopic_folder_repository),
):
    return SubTopicService(subtopic_repository, topic_repository, file_repository, folder_repository)
