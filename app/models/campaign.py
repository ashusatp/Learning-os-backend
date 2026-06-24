import uuid

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enum import CampaignStatus, CampaignType


class RevisionCampaign(Base):
    __tablename__ = "revision_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String, nullable=False)

    campaign_type = Column(
        Enum(CampaignType),
        nullable=False,
        default=CampaignType.SUBTOPIC_REVISION,
    )

    status = Column(
        Enum(CampaignStatus),
        nullable=False,
        default=CampaignStatus.ACTIVE,
    )

    total_days = Column(Integer, nullable=False)

    daily_frequency = Column(Integer, nullable=False)

    parallel_subjects = Column(Integer, nullable=False, default=1, server_default="1")

    start_date = Column(Date, nullable=False)

    end_date = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="campaigns")

    scopes = relationship(
        "CampaignScope",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )

    items = relationship(
        "CampaignItem",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
