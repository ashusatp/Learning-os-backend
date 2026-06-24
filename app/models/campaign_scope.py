import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enum import CampaignScopeType


class CampaignScope(Base):
    __tablename__ = "campaign_scopes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("revision_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scope_type = Column(
        Enum(CampaignScopeType),
        nullable=False,
    )

    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    campaign = relationship("RevisionCampaign", back_populates="scopes")

    subject = relationship("Subject")

    topic = relationship("Topic")
