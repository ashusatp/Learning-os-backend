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

    async def get_mistakes_by_goal(self, goal_id: UUID, resolved: bool | None = None):
        return await self.mistake_repository.get_by_goal(goal_id, resolved)

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
