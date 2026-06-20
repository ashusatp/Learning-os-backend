from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr


class OAuthCallbackRequest(BaseModel):
    code: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "AuthUserResponse"


class AuthUserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    ai_enabled: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_user(cls, user) -> "AuthUserResponse":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            ai_enabled=user.account.ai_enabled if user.account else False,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
