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
    mastery_level: MasteryLevel | None = None
    confidence_level: float | None = None
    exam_frequency: int | None = None
    marks_per_question: int | None = None


class ReorderSubTopicsRequest(BaseModel):
    ordered_ids: list[UUID]


class UpdatePerformanceRequest(BaseModel):
    questions_correct: int
    mistake_count: int


class SaveNotesRequest(BaseModel):
    notes_html: str | None = None
    sketch_data_url: str | None = None
    whiteboard_data_url: str | None = None


class SubtopicFileResponse(BaseModel):
    id: UUID
    subtopic_id: UUID
    folder_id: UUID | None = None
    name: str
    original_name: str
    content_type: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True


class SubtopicFolderResponse(BaseModel):
    id: UUID
    subtopic_id: UUID
    parent_id: UUID | None = None
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class CreateFolderRequest(BaseModel):
    name: str
    parent_id: UUID | None = None


class RenameFolderRequest(BaseModel):
    name: str


class MoveFolderRequest(BaseModel):
    parent_id: UUID | None = None


class MoveFileRequest(BaseModel):
    folder_id: UUID | None = None


class RenameFileRequest(BaseModel):
    original_name: str


class FolderContentsResponse(BaseModel):
    folders: list[SubtopicFolderResponse]
    files: list[SubtopicFileResponse]


class SubtopicStatsResponse(BaseModel):
    mastery_level: MasteryLevel
    confidence_level: float
    revision_count: int
    last_revised_at: datetime | None
    question_count: int
    total_mistakes: int
    unresolved_mistakes: int
    resolved_mistakes: int
    exam_frequency: int
    marks_per_question: int
    created_at: datetime
    updated_at: datetime


class UpdateStatsRequest(BaseModel):
    mastery_level: MasteryLevel | None = None
    confidence_level: float | None = None
    exam_frequency: int | None = None
    marks_per_question: int | None = None


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
    exam_frequency: int
    marks_per_question: int
    notes_html: str | None
    sketch_data_url: str | None
    whiteboard_data_url: str | None
    files: list[SubtopicFileResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
