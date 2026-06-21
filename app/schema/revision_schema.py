from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.models.enum import QualityRating, RevisionEventType


# ── Revision Schedule ──

class RevisionScheduleResponse(BaseModel):
    id: UUID
    subtopic_id: UUID
    next_revision_at: datetime
    current_interval_days: int
    ease_factor: float
    consecutive_successes: int
    consecutive_misses: int
    total_revisions: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Revision Log ──

class RevisionLogResponse(BaseModel):
    id: UUID
    subtopic_id: UUID
    schedule_id: UUID
    event_type: RevisionEventType
    quality_rating: QualityRating | None
    scheduled_for: datetime
    completed_at: datetime | None
    was_on_time: bool
    interval_used_days: int
    next_interval_days: int | None
    ease_before: float
    ease_after: float | None
    revision_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Revision Actions ──

class CompleteRevisionRequest(BaseModel):
    quality_rating: QualityRating
    revision_notes: str | None = None


class RescheduleRevisionRequest(BaseModel):
    new_date: datetime


# ── User Revision Settings ──

class UserRevisionSettingsResponse(BaseModel):
    id: UUID
    user_id: UUID
    daily_limit: int
    vacation_until: datetime | None
    streak_freezes_remaining: int
    daily_streak: int
    longest_streak: int
    catch_up_days: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateRevisionSettingsRequest(BaseModel):
    daily_limit: int | None = None
    vacation_until: datetime | None = None
    catch_up_days: int | None = None


# ── Queue Item (computed, not a model) ──

class RevisionQueueItem(BaseModel):
    schedule_id: UUID
    subtopic_id: UUID
    subtopic_name: str
    topic_name: str
    subject_name: str
    mastery_level: str
    mistake_count: int
    exam_frequency: int
    marks_per_question: int
    next_revision_at: datetime
    current_interval_days: int
    ease_factor: float
    consecutive_successes: int
    days_overdue: int
    priority_score: float
    status: str  # "overdue" | "due_today" | "upcoming"


class RevisionQueueResponse(BaseModel):
    overdue: list[RevisionQueueItem]
    due_today: list[RevisionQueueItem]
    upcoming: list[RevisionQueueItem]
    stats: "RevisionStatsResponse"


class RevisionStatsResponse(BaseModel):
    due_today: int
    overdue_count: int
    completed_today: int
    daily_streak: int
    longest_streak: int
    completion_rate_7d: float
    completion_rate_30d: float


class RevisionCompleteResponse(BaseModel):
    schedule: RevisionScheduleResponse
    log: RevisionLogResponse
    next_interval_days: int
    new_ease_factor: float
    next_revision_at: datetime
