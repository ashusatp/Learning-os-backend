from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class CreateGoalRequest(BaseModel):
    title: str
    description: str | None = None
    target_exam: str | None = None
    target_year: int | None = None


class UpdateGoalRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    target_exam: str | None = None
    target_year: int | None = None


class GoalResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    target_exam: str | None
    target_year: int | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
