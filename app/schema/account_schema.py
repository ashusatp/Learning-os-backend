from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class AccountResponse(BaseModel):
    id: UUID
    user_id: UUID
    ai_enabled: bool
    ai_requests_today: int
    plan: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateAccountRequest(BaseModel):
    ai_enabled: bool | None = None
    plan: str | None = None
