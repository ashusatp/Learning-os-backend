from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class AttachmentInfo(BaseModel):
    original_name: str
    disk_name: str
    content_type: str
    size: int


class IssueResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str
    page_url: str | None
    category: str
    status: str
    attachments: list[AttachmentInfo]
    created_at: datetime

    class Config:
        from_attributes = True
