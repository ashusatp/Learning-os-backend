from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str


class UpdateUserRequest(BaseModel):
    name: str | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
