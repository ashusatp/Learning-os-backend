from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.goal_dependency import get_goal_service
from app.schema.goal_schema import CreateGoalRequest, UpdateGoalRequest, GoalResponse
from app.services.goal_service import GoalService

router = APIRouter(
    prefix="/users/{user_id}/goals",
    tags=["Goals"],
)


@router.post("", response_model=GoalResponse, status_code=201)
async def create_goal(
    user_id: UUID,
    payload: CreateGoalRequest,
    service: GoalService = Depends(get_goal_service),
):
    return await service.create_goal(
        user_id=user_id,
        title=payload.title,
        description=payload.description,
        target_exam=payload.target_exam,
        target_year=payload.target_year,
    )


@router.get("", response_model=list[GoalResponse])
async def get_goals(
    user_id: UUID,
    include_archived: bool = False,
    service: GoalService = Depends(get_goal_service),
):
    return await service.get_goals_by_user(user_id, include_archived=include_archived)


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    user_id: UUID,
    goal_id: UUID,
    service: GoalService = Depends(get_goal_service),
):
    return await service.get_goal(goal_id)


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    user_id: UUID,
    goal_id: UUID,
    payload: UpdateGoalRequest,
    service: GoalService = Depends(get_goal_service),
):
    return await service.update_goal(
        goal_id,
        **payload.model_dump(exclude_unset=True),
    )


@router.patch("/{goal_id}/archive", response_model=GoalResponse)
async def archive_goal(
    user_id: UUID,
    goal_id: UUID,
    archive: bool = True,
    service: GoalService = Depends(get_goal_service),
):
    return await service.archive_goal(goal_id, archive)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    user_id: UUID,
    goal_id: UUID,
    service: GoalService = Depends(get_goal_service),
):
    await service.delete_goal(goal_id)
