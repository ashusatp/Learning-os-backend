from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.exceptions.custom_exceptions import UnauthorizedException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.utils.jwt import decode_access_token

security = HTTPBearer()


def get_user_repository(
    db: AsyncSession = Depends(get_db),
):
    return UserRepository(db)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
):
    return AuthService(user_repository)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    token = credentials.credentials

    user_id = decode_access_token(token)

    if not user_id:
        raise UnauthorizedException("Invalid or expired token")

    user = await user_repository.get_by_id(UUID(user_id))

    if not user:
        raise UnauthorizedException("User not found")

    return user
