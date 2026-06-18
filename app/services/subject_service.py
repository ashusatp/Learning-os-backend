import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import NotFoundException
from app.models.subject import Subject
from app.repositories.goal_repository import GoalRepository
from app.repositories.subject_repository import SubjectRepository

logger = logging.getLogger(__name__)


class SubjectService:

    def __init__(self, subject_repository: SubjectRepository, goal_repository: GoalRepository):
        self.subject_repository = subject_repository
        self.goal_repository = goal_repository

    async def create_subject(
        self,
        goal_id: UUID,
        name: str,
        description: str | None = None,
        order: int = 0,
    ):

        db = self.subject_repository.db

        try:
            goal = await self.goal_repository.get_by_id(goal_id)

            if not goal:
                raise NotFoundException(f"Goal not found: {goal_id}")

            subject = Subject(
                goal_id=goal_id,
                name=name,
                description=description,
                order=order,
            )

            await self.subject_repository.create(subject)

            await db.commit()
            await db.refresh(subject)

            logger.info(f"Subject created: {name} for goal {goal_id}")

            return subject

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while creating subject: {name}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while creating subject: {name}")
            raise

    async def get_subject(self, subject_id: UUID):

        subject = await self.subject_repository.get_by_id(subject_id)

        if not subject:
            raise NotFoundException(f"Subject not found: {subject_id}")

        return subject

    async def get_subjects_by_goal(self, goal_id: UUID):

        goal = await self.goal_repository.get_by_id(goal_id)

        if not goal:
            raise NotFoundException(f"Goal not found: {goal_id}")

        return await self.subject_repository.get_by_goal(goal_id)

    async def update_subject(self, subject_id: UUID, **kwargs):

        db = self.subject_repository.db

        try:
            subject = await self.get_subject(subject_id)

            for key, value in kwargs.items():
                if value is not None:
                    setattr(subject, key, value)

            await self.subject_repository.update(subject)

            await db.commit()
            await db.refresh(subject)

            logger.info(f"Subject updated: {subject_id}")

            return subject

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while updating subject: {subject_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while updating subject: {subject_id}")
            raise

    async def delete_subject(self, subject_id: UUID):

        db = self.subject_repository.db

        try:
            subject = await self.get_subject(subject_id)

            await self.subject_repository.delete(subject)

            await db.commit()

            logger.info(f"Subject deleted: {subject_id}")

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while deleting subject: {subject_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while deleting subject: {subject_id}")
            raise
