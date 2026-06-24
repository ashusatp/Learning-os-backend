import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class CampaignItem(Base):
    __tablename__ = "campaign_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("revision_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subtopic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subtopics.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    mistake_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mistakes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    scheduled_date = Column(Date, nullable=False, index=True)

    order_in_day = Column(Integer, nullable=False, default=0)

    is_completed = Column(Boolean, nullable=False, default=False)

    completed_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    campaign = relationship("RevisionCampaign", back_populates="items")

    subtopic = relationship("SubTopic")

    mistake = relationship("Mistake")

    question = relationship("Question")
