import logging

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

    async def get_all(self):
        query = select(Issue).order_by(Issue.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()
