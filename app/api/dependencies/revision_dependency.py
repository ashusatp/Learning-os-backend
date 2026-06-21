from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.revision_repository import RevisionRepository
from app.repositories.subtopic_repository import SubTopicRepository
from app.services.revision_service import RevisionService


def get_revision_repository(
    db: AsyncSession = Depends(get_db),
):
    return RevisionRepository(db)


def get_subtopic_repository_for_revisions(
    db: AsyncSession = Depends(get_db),
):
    return SubTopicRepository(db)


def get_revision_service(
    revision_repository: RevisionRepository = Depends(get_revision_repository),
    subtopic_repository: SubTopicRepository = Depends(get_subtopic_repository_for_revisions),
):
    return RevisionService(revision_repository, subtopic_repository)
