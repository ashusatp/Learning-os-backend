import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import NotFoundException
from app.models.mistake import Mistake
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.subtopic_repository import SubTopicRepository

logger = logging.getLogger(__name__)


class MistakeService:

    def __init__(
        self,
        mistake_repository: MistakeRepository,
        subtopic_repository: SubTopicRepository,
    ):
        self.mistake_repository = mistake_repository
        self.subtopic_repository = subtopic_repository

    async def create_mistake(self, subtopic_id: UUID, **kwargs):
        db = self.mistake_repository.db

        try:
            subtopic = await self.subtopic_repository.get_by_id(subtopic_id)
            if not subtopic:
                raise NotFoundException(f"Subtopic not found: {subtopic_id}")

            # Auto-resolve if correction is provided
            correction = kwargs.get("correction_html")
            if correction and correction.strip():
                kwargs["is_resolved"] = True
                kwargs["resolved_at"] = datetime.now(timezone.utc)

            mistake = Mistake(subtopic_id=subtopic_id, **kwargs)
            await self.mistake_repository.create(mistake)
            await db.commit()
            await db.refresh(mistake)

            logger.info(f"Mistake created for subtopic {subtopic_id}")
            return mistake

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while creating mistake for subtopic: {subtopic_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while creating mistake for subtopic: {subtopic_id}")
            raise

    async def get_mistake(self, mistake_id: UUID):
        mistake = await self.mistake_repository.get_by_id(mistake_id)
        if not mistake:
            raise NotFoundException(f"Mistake not found: {mistake_id}")
        return mistake

    async def get_mistakes_by_subtopic(self, subtopic_id: UUID, resolved: bool | None = None):
        subtopic = await self.subtopic_repository.get_by_id(subtopic_id)
        if not subtopic:
            raise NotFoundException(f"Subtopic not found: {subtopic_id}")
        return await self.mistake_repository.get_by_subtopic(subtopic_id, resolved)

    async def get_mistakes_by_subtopic_paginated(
        self, subtopic_id: UUID, resolved: bool | None, page: int, page_size: int
    ):
        subtopic = await self.subtopic_repository.get_by_id(subtopic_id)
        if not subtopic:
            raise NotFoundException(f"Subtopic not found: {subtopic_id}")
        offset = (page - 1) * page_size
        items, total = await self.mistake_repository.get_by_subtopic_paginated(subtopic_id, resolved, page_size, offset)
        total_pages = (total + page_size - 1) // page_size
        return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

    async def get_mistakes_by_goal(self, goal_id: UUID, resolved: bool | None = None):
        return await self.mistake_repository.get_by_goal(goal_id, resolved)

    async def get_mistakes_by_goal_paginated(self, goal_id: UUID, page: int, page_size: int, **filters):
        offset = (page - 1) * page_size
        rows, total = await self.mistake_repository.get_by_goal_paginated(
            goal_id, page_size, offset, **filters
        )
        total_pages = (total + page_size - 1) // page_size

        items = []
        for row in rows:
            mistake = row[0]
            item = {
                "id": mistake.id,
                "subtopic_id": mistake.subtopic_id,
                "question_id": mistake.question_id,
                "mistake_type": mistake.mistake_type,
                "description_html": mistake.description_html,
                "correction_html": mistake.correction_html,
                "tags": mistake.tags or [],
                "is_resolved": mistake.is_resolved,
                "resolved_at": mistake.resolved_at,
                "revision_count": mistake.revision_count,
                "last_revised_at": mistake.last_revised_at,
                "created_at": mistake.created_at,
                "updated_at": mistake.updated_at,
                "subject_id": row[1],
                "subject_name": row[2],
                "topic_id": row[3],
                "topic_name": row[4],
                "subtopic_name": row[5],
            }
            items.append(item)

        return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

    async def update_mistake(self, mistake_id: UUID, **kwargs):
        db = self.mistake_repository.db

        try:
            mistake = await self.get_mistake(mistake_id)

            for key, value in kwargs.items():
                if value is not None:
                    setattr(mistake, key, value)

            # Auto-resolve if correction is provided, un-resolve if removed
            correction = kwargs.get("correction_html")
            if correction is not None:
                if correction and correction.strip():
                    mistake.is_resolved = True
                    mistake.resolved_at = datetime.now(timezone.utc)
                else:
                    mistake.is_resolved = False
                    mistake.resolved_at = None

            await self.mistake_repository.update(mistake)
            await db.commit()
            await db.refresh(mistake)

            logger.info(f"Mistake updated: {mistake_id}")
            return mistake

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while updating mistake: {mistake_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while updating mistake: {mistake_id}")
            raise

    async def resolve_mistake(self, mistake_id: UUID):
        db = self.mistake_repository.db

        try:
            mistake = await self.get_mistake(mistake_id)
            mistake.is_resolved = not mistake.is_resolved
            mistake.resolved_at = datetime.now(timezone.utc) if mistake.is_resolved else None

            await self.mistake_repository.update(mistake)
            await db.commit()
            await db.refresh(mistake)

            logger.info(f"Mistake {'resolved' if mistake.is_resolved else 'unresolved'}: {mistake_id}")
            return mistake

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while resolving mistake: {mistake_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while resolving mistake: {mistake_id}")
            raise

    async def revise_mistake(self, mistake_id: UUID):
        db = self.mistake_repository.db

        try:
            mistake = await self.get_mistake(mistake_id)
            mistake.revision_count += 1
            mistake.last_revised_at = datetime.now(timezone.utc)

            await self.mistake_repository.update(mistake)
            await db.commit()
            await db.refresh(mistake)

            logger.info(f"Mistake revised ({mistake.revision_count}x): {mistake_id}")
            return mistake

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while revising mistake: {mistake_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while revising mistake: {mistake_id}")
            raise

    async def delete_mistake(self, mistake_id: UUID):
        db = self.mistake_repository.db

        try:
            mistake = await self.get_mistake(mistake_id)
            await self.mistake_repository.delete(mistake)
            await db.commit()

            logger.info(f"Mistake deleted: {mistake_id}")

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while deleting mistake: {mistake_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while deleting mistake: {mistake_id}")
            raise
