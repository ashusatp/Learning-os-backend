import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class UserRevisionSettings(Base):
    __tablename__ = "user_revision_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    daily_limit = Column(Integer, nullable=False, default=15)

    vacation_until = Column(DateTime(timezone=True), nullable=True)

    streak_freezes_remaining = Column(Integer, nullable=False, default=0)

    daily_streak = Column(Integer, nullable=False, default=0)

    longest_streak = Column(Integer, nullable=False, default=0)

    catch_up_days = Column(Integer, nullable=False, default=5)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="revision_settings")
