from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class CreateSubjectRequest(BaseModel):
    name: str
    description: str | None = None
    order: int = 0


class UpdateSubjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    order: int | None = None


class SubjectResponse(BaseModel):
    id: UUID
    goal_id: UUID
    name: str
    description: str | None
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
