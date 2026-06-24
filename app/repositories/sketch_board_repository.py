import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sketch_board import SketchBoardModel

logger = logging.getLogger(__name__)


class SketchBoardRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, board_id: UUID):
        return await self.db.get(SketchBoardModel, board_id)

    async def get_by_subtopic(self, subtopic_id: UUID):
        query = select(SketchBoardModel).where(
            SketchBoardModel.subtopic_id == subtopic_id
        ).order_by(SketchBoardModel.order)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, board: SketchBoardModel):
        self.db.add(board)
        await self.db.flush()
        return board

    async def update(self, board: SketchBoardModel):
        await self.db.flush()
        return board

    async def delete(self, board: SketchBoardModel):
        await self.db.delete(board)
        await self.db.flush()
