from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.goal_repository import GoalRepository
from app.repositories.revision_repository import RevisionRepository
from app.repositories.user_repository import UserRepository
from app.services.goal_service import GoalService


def get_goal_repository(
    db: AsyncSession = Depends(get_db),
):
    return GoalRepository(db)


def get_user_repository(
    db: AsyncSession = Depends(get_db),
):
    return UserRepository(db)


def get_revision_repository(
    db: AsyncSession = Depends(get_db),
):
    return RevisionRepository(db)


def get_goal_service(
    goal_repository: GoalRepository = Depends(get_goal_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    revision_repository: RevisionRepository = Depends(get_revision_repository),
):
    return GoalService(goal_repository, user_repository, revision_repository)
