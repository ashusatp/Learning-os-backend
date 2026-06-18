from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth_dependency import get_current_user
from app.api.dependencies.user_dependency import get_user_service
from app.models.user import User
from app.schema.user_schema import UpdateUserRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("", response_model=list[UserResponse])
async def get_all_users(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.update_user(
        user_id,
        **payload.model_dump(exclude_unset=True),
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    await service.delete_user(user_id)
