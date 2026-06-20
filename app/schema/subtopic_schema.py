from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.models.enum import MasteryLevel


class CreateSubTopicRequest(BaseModel):
    name: str
    description: str | None = None
    order: int = 0


class UpdateSubTopicRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    order: int | None = None


class ReorderSubTopicsRequest(BaseModel):
    ordered_ids: list[UUID]


class UpdatePerformanceRequest(BaseModel):
    questions_solved: int
    questions_correct: int
    mistake_count: int


class SaveNotesRequest(BaseModel):
    notes_html: str | None = None
    sketch_data_url: str | None = None
    whiteboard_data_url: str | None = None


class SubtopicFileResponse(BaseModel):
    id: UUID
    subtopic_id: UUID
    name: str
    original_name: str
    content_type: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True


class SubTopicResponse(BaseModel):
    id: UUID
    topic_id: UUID
    name: str
    description: str | None
    order: int
    revision_count: int
    last_revised_at: datetime | None
    confidence_level: float
    mastery_level: MasteryLevel
    questions_solved: int
    questions_correct: int
    mistake_count: int
    notes_html: str | None
    sketch_data_url: str | None
    whiteboard_data_url: str | None
    files: list[SubtopicFileResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
