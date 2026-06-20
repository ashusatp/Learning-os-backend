from fastapi import APIRouter, Depends

from app.api.dependencies.auth_dependency import get_auth_service, get_current_user
from app.models.user import User
from app.schema.auth_schema import SignupRequest, SigninRequest, AuthResponse, AuthUserResponse, OAuthCallbackRequest
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    payload: SignupRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.register(
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )

    return result


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: SigninRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.login(
        email=payload.email,
        password=payload.password,
    )

    return result


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    payload: OAuthCallbackRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.google_auth(code=payload.code)
    return result


@router.get("/me", response_model=AuthUserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return AuthUserResponse.from_user(current_user)
