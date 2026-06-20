import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import configs
from app.exceptions.custom_exceptions import ForbiddenException, NotFoundException
from app.models.account import Account
from app.repositories.account_repository import AccountRepository

logger = logging.getLogger(__name__)


class AccountService:

    def __init__(self, account_repository: AccountRepository):
        self.account_repository = account_repository

    async def get_account(self, user_id: UUID):
        account = await self.account_repository.get_by_user_id(user_id)

        if not account:
            raise NotFoundException(f"Account not found for user: {user_id}")

        return account

    async def create_account(self, user_id: UUID):
        db = self.account_repository.db

        try:
            account = Account(user_id=user_id)
            account = await self.account_repository.create(account)
            await db.commit()
            await db.refresh(account)

            logger.info(f"Account created for user: {user_id}")
            return account

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error creating account for user: {user_id}")
            raise

    async def update_account(self, user_id: UUID, **kwargs):
        db = self.account_repository.db

        try:
            account = await self.get_account(user_id)

            for key, value in kwargs.items():
                if value is not None:
                    setattr(account, key, value)

            await self.account_repository.update(account)
            await db.commit()
            await db.refresh(account)

            logger.info(f"Account updated for user: {user_id}")
            return account

        except NotFoundException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error updating account for user: {user_id}")
            raise

    async def validate_ai_access(self, user_id: UUID):
        """Validates that the user's account has AI enabled and is within rate limits."""
        db = self.account_repository.db
        account = await self.get_account(user_id)

        if not account.ai_enabled:
            raise ForbiddenException("AI features are not enabled for your account")

        # Reset daily counter if it's a new day
        now = datetime.now(timezone.utc)
        if account.ai_requests_last_reset is None or account.ai_requests_last_reset.date() < now.date():
            account.ai_requests_today = 0
            account.ai_requests_last_reset = now
            await self.account_repository.update(account)
            await db.commit()

        if account.ai_requests_today >= configs.AI_RATE_LIMIT_PER_DAY:
            raise ForbiddenException(
                f"Daily AI request limit reached ({configs.AI_RATE_LIMIT_PER_DAY}). Resets tomorrow."
            )

        return account

    async def increment_ai_usage(self, user_id: UUID):
        """Increments the daily AI request counter after a successful call."""
        db = self.account_repository.db

        try:
            account = await self.get_account(user_id)
            account.ai_requests_today = (account.ai_requests_today or 0) + 1
            account.ai_requests_last_reset = datetime.now(timezone.utc)
            await self.account_repository.update(account)
            await db.commit()

        except Exception:
            await db.rollback()
            logger.exception(f"Error incrementing AI usage for user: {user_id}")
