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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
