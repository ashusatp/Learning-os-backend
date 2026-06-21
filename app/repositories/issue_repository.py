import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import Issue

logger = logging.getLogger(__name__)


class IssueRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, issue: Issue):
        self.db.add(issue)
        await self.db.flush()
        return issue

    async def get_by_id(self, issue_id: UUID):
        result = await self.db.get(Issue, issue_id)
        return result

    async def get_by_user(self, user_id: UUID):
        query = select(Issue).where(Issue.user_id == user_id).order_by(Issue.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all(self):
        query = select(Issue).order_by(Issue.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, issue: Issue):
        await self.db.flush()
        return issue
