from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class CreateTopicRequest(BaseModel):
    name: str
    description: str | None = None
    order: int = 0


class UpdateTopicRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    order: int | None = None


class ReorderTopicsRequest(BaseModel):
    ordered_ids: list[UUID]


class TopicResponse(BaseModel):
    id: UUID
    subject_id: UUID
    name: str
    description: str | None
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
