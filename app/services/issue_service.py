import logging
from uuid import UUID

from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import NotFoundException
from app.models.issue import Issue
from app.repositories.issue_repository import IssueRepository

logger = logging.getLogger(__name__)


class IssueService:

    def __init__(self, issue_repository: IssueRepository):
        self.issue_repository = issue_repository

    async def create_issue(
        self,
        user_id: UUID,
        title: str,
        description: str,
        page_url: str | None = None,
        category: str = "bug",
        attachments: list[dict] | None = None,
    ):
        db = self.issue_repository.db

        try:
            issue = Issue(
                user_id=user_id,
                title=title,
                description=description,
                page_url=page_url,
                category=category,
                attachments=attachments or [],
            )

            await self.issue_repository.create(issue)
            await db.commit()
            await db.refresh(issue)

            logger.info(f"Issue created: '{title}' by user {user_id}")

            return issue

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while creating issue: {title}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while creating issue: {title}")
            raise

    async def get_all_issues(self):
        return await self.issue_repository.get_all()

    async def get_issues_by_user(self, user_id: UUID):
        return await self.issue_repository.get_by_user(user_id)

    async def resolve_issue(self, issue_id: UUID):
        db = self.issue_repository.db
        try:
            issue = await self.issue_repository.get_by_id(issue_id)
            if not issue:
                raise NotFoundException(f"Issue not found: {issue_id}")
            issue.status = "resolved"
            issue.resolved_at = datetime.now(timezone.utc)
            await self.issue_repository.update(issue)
            await db.commit()
            await db.refresh(issue)
            logger.info(f"Issue resolved: {issue_id}")
            return issue
        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while resolving issue: {issue_id}")
            raise

    async def reopen_issue(self, issue_id: UUID):
        db = self.issue_repository.db
        try:
            issue = await self.issue_repository.get_by_id(issue_id)
            if not issue:
                raise NotFoundException(f"Issue not found: {issue_id}")
            issue.status = "open"
            issue.resolved_at = None
            await self.issue_repository.update(issue)
            await db.commit()
            await db.refresh(issue)
            logger.info(f"Issue reopened: {issue_id}")
            return issue
        except NotFoundException:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while reopening issue: {issue_id}")
            raise
