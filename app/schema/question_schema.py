from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.models.enum import QuestionType, DifficultyLevel


# ── Option schemas ──


class CreateOptionRequest(BaseModel):
    text_html: str
    is_correct: bool = False
    order: int = 0


class UpdateOptionRequest(BaseModel):
    id: UUID | None = None  # None = new option to create
    text_html: str
    is_correct: bool = False
    order: int = 0


class OptionResponse(BaseModel):
    id: UUID
    question_id: UUID
    text_html: str
    is_correct: bool
    order: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Question schemas ──


class CreateQuestionRequest(BaseModel):
    question_type: QuestionType = QuestionType.SINGLE_MCQ
    text_html: str
    explanation_html: str | None = None
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    marks: float = 1.0
    negative_marks: float = 0.0
    numerical_answer: float | None = None
    numerical_tolerance: float | None = None
    answer_html: str | None = None
    is_pyq: bool = False
    tags: list[str] = []
    order: int = 0
    options: list[CreateOptionRequest] = []


class UpdateQuestionRequest(BaseModel):
    question_type: QuestionType | None = None
    text_html: str | None = None
    explanation_html: str | None = None
    difficulty: DifficultyLevel | None = None
    marks: float | None = None
    negative_marks: float | None = None
    numerical_answer: float | None = None
    numerical_tolerance: float | None = None
    answer_html: str | None = None
    is_pyq: bool | None = None
    tags: list[str] | None = None
    order: int | None = None
    options: list[UpdateOptionRequest] | None = None


class QuestionResponse(BaseModel):
    id: UUID
    subtopic_id: UUID
    question_type: QuestionType
    text_html: str
    explanation_html: str | None
    difficulty: DifficultyLevel
    marks: float
    negative_marks: float
    numerical_answer: float | None
    numerical_tolerance: float | None
    answer_html: str | None
    is_pyq: bool
    tags: list[str]
    order: int
    options: list[OptionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReorderQuestionsRequest(BaseModel):
    ordered_ids: list[UUID]
