import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    ai_enabled = Column(Boolean, nullable=False, server_default="false")

    ai_requests_today = Column(Integer, nullable=False, server_default="0")

    ai_requests_last_reset = Column(DateTime(timezone=True), nullable=True)

    plan = Column(String, nullable=False, server_default="free")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="account")
