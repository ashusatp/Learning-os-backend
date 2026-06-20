import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subtopic_file import SubtopicFile

logger = logging.getLogger(__name__)


class SubtopicFileRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, file_id: UUID):
        return await self.db.get(SubtopicFile, file_id)

    async def get_by_subtopic(self, subtopic_id: UUID):
        query = select(SubtopicFile).where(
            SubtopicFile.subtopic_id == subtopic_id
        ).order_by(SubtopicFile.created_at)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, file: SubtopicFile):
        self.db.add(file)
        await self.db.flush()
        return file

    async def delete(self, file: SubtopicFile):
        await self.db.delete(file)
        await self.db.flush()
