import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import NotFoundException
from app.models.goal import Goal
from app.repositories.goal_repository import GoalRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class GoalService:

    def __init__(self, goal_repository: GoalRepository, user_repository: UserRepository):
        self.goal_repository = goal_repository
        self.user_repository = user_repository

    async def create_goal(
        self,
        user_id: UUID,
        title: str,
        description: str | None = None,
        target_exam: str | None = None,
        target_year: int | None = None,
    ):

        db = self.goal_repository.db

        try:
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                raise NotFoundException(f"User not found: {user_id}")

            goal = Goal(
                user_id=user_id,
                title=title,
                description=description,
                target_exam=target_exam,
                target_year=target_year,
            )

            await self.goal_repository.create(goal)

            await db.commit()
            await db.refresh(goal)

            logger.info(f"Goal created: {title} for user {user_id}")

            return goal

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while creating goal: {title}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while creating goal: {title}")
            raise

    async def get_goal(self, goal_id: UUID):

        goal = await self.goal_repository.get_by_id(goal_id)

        if not goal:
            raise NotFoundException(f"Goal not found: {goal_id}")

        return goal

    async def get_goals_by_user(self, user_id: UUID):

        user = await self.user_repository.get_by_id(user_id)

        if not user:
            raise NotFoundException(f"User not found: {user_id}")

        return await self.goal_repository.get_by_user(user_id)

    async def update_goal(self, goal_id: UUID, **kwargs):

        db = self.goal_repository.db

        try:
            goal = await self.get_goal(goal_id)

            for key, value in kwargs.items():
                if value is not None:
                    setattr(goal, key, value)

            await self.goal_repository.update(goal)

            await db.commit()
            await db.refresh(goal)

            logger.info(f"Goal updated: {goal_id}")

            return goal

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while updating goal: {goal_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while updating goal: {goal_id}")
            raise

    async def delete_goal(self, goal_id: UUID):

        db = self.goal_repository.db

        try:
            goal = await self.get_goal(goal_id)

            await self.goal_repository.delete(goal)

            await db.commit()

            logger.info(f"Goal deleted: {goal_id}")

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while deleting goal: {goal_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while deleting goal: {goal_id}")
            raise
