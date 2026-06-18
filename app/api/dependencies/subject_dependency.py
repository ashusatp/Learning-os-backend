from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.repositories.goal_repository import GoalRepository
from app.repositories.subject_repository import SubjectRepository
from app.services.subject_service import SubjectService


def get_subject_repository(
    db: AsyncSession = Depends(get_db),
):
    return SubjectRepository(db)


def get_goal_repository(
    db: AsyncSession = Depends(get_db),
):
    return GoalRepository(db)


def get_subject_service(
    subject_repository: SubjectRepository = Depends(get_subject_repository),
    goal_repository: GoalRepository = Depends(get_goal_repository),
):
    return SubjectService(subject_repository, goal_repository)
