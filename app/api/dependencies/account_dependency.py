from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependency import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.services.account_service import AccountService


def get_account_repository(
    db: AsyncSession = Depends(get_db),
):
    return AccountRepository(db)


def get_account_service(
    account_repository: AccountRepository = Depends(get_account_repository),
):
    return AccountService(account_repository)


async def require_ai_access(
    current_user: User = Depends(get_current_user),
    account_service: AccountService = Depends(get_account_service),
) -> User:
    """Dependency that validates JWT + checks ai_enabled + rate limits."""
    await account_service.validate_ai_access(current_user.id)
    return current_user
