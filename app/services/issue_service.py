import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

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
