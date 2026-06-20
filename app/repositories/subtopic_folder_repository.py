import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subtopic_folder import SubtopicFolder

logger = logging.getLogger(__name__)


class SubtopicFolderRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, folder_id: UUID):
        return await self.db.get(SubtopicFolder, folder_id)

    async def get_by_subtopic(self, subtopic_id: UUID, parent_id: UUID | None = None):
        query = select(SubtopicFolder).where(
            SubtopicFolder.subtopic_id == subtopic_id,
        )
        if parent_id is None:
            query = query.where(SubtopicFolder.parent_id.is_(None))
        else:
            query = query.where(SubtopicFolder.parent_id == parent_id)
        query = query.order_by(SubtopicFolder.name)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, folder: SubtopicFolder):
        self.db.add(folder)
        await self.db.flush()
        return folder

    async def update(self, folder: SubtopicFolder):
        await self.db.flush()
        return folder

    async def delete(self, folder: SubtopicFolder):
        await self.db.delete(folder)
        await self.db.flush()
