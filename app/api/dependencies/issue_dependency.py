from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.issue_repository import IssueRepository
from app.services.issue_service import IssueService


def get_issue_repository(
    db: AsyncSession = Depends(get_db),
):
    return IssueRepository(db)


def get_issue_service(
    issue_repository: IssueRepository = Depends(get_issue_repository),
):
    return IssueService(issue_repository)
