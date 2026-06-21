import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class RevisionSchedule(Base):
    __tablename__ = "revision_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    subtopic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subtopics.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    next_revision_at = Column(DateTime(timezone=True), nullable=False)

    current_interval_days = Column(Integer, nullable=False, default=1)

    ease_factor = Column(Float, nullable=False, default=2.5)

    consecutive_successes = Column(Integer, nullable=False, default=0)

    consecutive_misses = Column(Integer, nullable=False, default=0)

    total_revisions = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subtopic = relationship("SubTopic", back_populates="revision_schedule")

    logs = relationship(
        "RevisionLog",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
