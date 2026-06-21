import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enum import QualityRating, RevisionEventType


class RevisionLog(Base):
    __tablename__ = "revision_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    subtopic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subtopics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("revision_schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(
        Enum(RevisionEventType),
        nullable=False,
    )

    quality_rating = Column(
        Enum(QualityRating),
        nullable=True,
    )

    scheduled_for = Column(DateTime(timezone=True), nullable=False)

    completed_at = Column(DateTime(timezone=True), nullable=True)

    was_on_time = Column(Boolean, nullable=False, default=True)

    interval_used_days = Column(Integer, nullable=False)

    next_interval_days = Column(Integer, nullable=True)

    ease_before = Column(Float, nullable=False)

    ease_after = Column(Float, nullable=True)

    revision_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    subtopic = relationship("SubTopic", back_populates="revision_logs")

    schedule = relationship("RevisionSchedule", back_populates="logs")
