import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import NotFoundException
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user(self, user_id: UUID):

        user = await self.user_repository.get_by_id(user_id)

        if not user:
            raise NotFoundException(f"User not found: {user_id}")

        return user

    async def get_all_users(self):
        return await self.user_repository.get_all()

    async def update_user(self, user_id: UUID, **kwargs):

        db = self.user_repository.db

        try:
            user = await self.get_user(user_id)

            for key, value in kwargs.items():
                if value is not None:
                    setattr(user, key, value)

            await self.user_repository.update(user)

            await db.commit()
            await db.refresh(user)

            logger.info(f"User updated: {user_id}")

            return user

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while updating user: {user_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while updating user: {user_id}")
            raise

    async def delete_user(self, user_id: UUID):

        db = self.user_repository.db

        try:
            user = await self.get_user(user_id)

            await self.user_repository.delete(user)

            await db.commit()

            logger.info(f"User deleted: {user_id}")

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while deleting user: {user_id}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while deleting user: {user_id}")
            raise
