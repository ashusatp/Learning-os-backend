from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.models.enum import MistakeType


class CreateMistakeRequest(BaseModel):
    subtopic_id: UUID | None = None  # optional — can be inferred from path
    question_id: UUID | None = None
    mistake_type: MistakeType = MistakeType.OTHER
    description_html: str
    correction_html: str | None = None
    tags: list[str] = []


class UpdateMistakeRequest(BaseModel):
    mistake_type: MistakeType | None = None
    description_html: str | None = None
    correction_html: str | None = None
    tags: list[str] | None = None


class MistakeResponse(BaseModel):
    id: UUID
    subtopic_id: UUID
    question_id: UUID | None
    mistake_type: MistakeType
    description_html: str
    correction_html: str | None
    tags: list[str]
    is_resolved: bool
    resolved_at: datetime | None
    revision_count: int
    last_revised_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoalMistakeResponse(MistakeResponse):
    subject_id: UUID
    subject_name: str
    topic_id: UUID
    topic_name: str
    subtopic_name: str
