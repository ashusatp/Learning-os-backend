from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.enum import CampaignScopeType, CampaignStatus, CampaignType


# ── Scope ──

class CampaignScopeCreate(BaseModel):
    scope_type: CampaignScopeType
    subject_id: UUID
    topic_id: UUID | None = None


class CampaignScopeResponse(BaseModel):
    id: UUID
    scope_type: CampaignScopeType
    subject_id: UUID
    topic_id: UUID | None
    subject_name: str | None = None
    topic_name: str | None = None

    class Config:
        from_attributes = True


# ── Campaign Create ──

class CampaignCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    campaign_type: CampaignType
    total_days: int = Field(..., ge=1, le=365)
    daily_frequency: int | None = Field(None, ge=1, le=100)
    parallel_subjects: int = Field(1, ge=1, le=20)
    start_date: date
    scopes: list[CampaignScopeCreate] = Field(..., min_length=1)
    # Optional: reordered subject sequence from preview
    subject_order: list[UUID] | None = None


# ── Preview Request / Response ──

class CampaignPreviewRequest(BaseModel):
    campaign_type: CampaignType
    total_days: int = Field(..., ge=1, le=365)
    daily_frequency: int | None = Field(None, ge=1, le=100)
    parallel_subjects: int = Field(1, ge=1, le=20)
    start_date: date
    scopes: list[CampaignScopeCreate] = Field(..., min_length=1)
    subject_order: list[UUID] | None = None


class PreviewDayItem(BaseModel):
    subtopic_id: str | None = None
    subtopic_name: str | None = None
    topic_name: str | None = None
    subject_name: str | None = None
    mistake_id: str | None = None
    question_id: str | None = None


class PreviewDay(BaseModel):
    date: date
    day_number: int
    items: list[PreviewDayItem]


class SubjectSummary(BaseModel):
    subject_id: str
    subject_name: str
    subtopic_count: int


class CampaignPreviewResponse(BaseModel):
    total_items: int
    total_days: int
    daily_frequency: int
    parallel_subjects: int
    subjects: list[SubjectSummary]
    schedule: list[PreviewDay]


# ── Campaign Item ──

class CampaignItemResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    subtopic_id: UUID | None
    mistake_id: UUID | None
    question_id: UUID | None
    scheduled_date: date
    order_in_day: int
    is_completed: bool
    completed_at: datetime | None
    notes: str | None
    subtopic_name: str | None = None
    topic_name: str | None = None
    subject_name: str | None = None
    mistake_description: str | None = None
    question_text: str | None = None

    class Config:
        from_attributes = True


class CampaignItemCompleteRequest(BaseModel):
    notes: str | None = None


# ── Campaign Response ──

class CampaignResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    campaign_type: CampaignType
    status: CampaignStatus
    total_days: int
    daily_frequency: int
    parallel_subjects: int = 1
    start_date: date
    end_date: date
    total_items: int = 0
    completed_items: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignDetailResponse(CampaignResponse):
    scopes: list[CampaignScopeResponse] = []


# ── Campaign Queue (today's items) ──

class CampaignQueueResponse(BaseModel):
    campaign_id: UUID
    campaign_name: str
    campaign_type: CampaignType
    scheduled_date: date
    items: list[CampaignItemResponse]
    total_for_day: int
    completed_for_day: int


# ── Reorder ──

class CampaignReorderRequest(BaseModel):
    """Swap a subtopic from one day to another day position."""
    item_id: UUID
    target_date: date
    target_order: int
