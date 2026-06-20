from fastapi import APIRouter, Depends

from app.api.dependencies.auth_dependency import get_current_user
from app.api.dependencies.account_dependency import get_account_service
from app.models.user import User
from app.schema.account_schema import AccountResponse, UpdateAccountRequest
from app.services.account_service import AccountService

router = APIRouter(
    prefix="/account",
    tags=["Account"],
)


@router.get("/me", response_model=AccountResponse)
async def get_my_account(
    current_user: User = Depends(get_current_user),
    service: AccountService = Depends(get_account_service),
):
    return await service.get_account(current_user.id)


@router.patch("/me", response_model=AccountResponse)
async def update_my_account(
    payload: UpdateAccountRequest,
    current_user: User = Depends(get_current_user),
    service: AccountService = Depends(get_account_service),
):
    return await service.update_account(
        current_user.id,
        **payload.model_dump(exclude_unset=True),
    )
