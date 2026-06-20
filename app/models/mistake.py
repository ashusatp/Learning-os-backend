import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enum import MistakeType


class Mistake(Base):
    __tablename__ = "mistakes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    subtopic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subtopics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    mistake_type = Column(
        Enum(MistakeType),
        nullable=False,
        default=MistakeType.OTHER,
    )

    description_html = Column(Text, nullable=False)

    correction_html = Column(Text, nullable=True)

    tags = Column(ARRAY(String), nullable=False, server_default="{}")

    is_resolved = Column(Boolean, nullable=False, default=False)

    resolved_at = Column(DateTime(timezone=True), nullable=True)

    revision_count = Column(Integer, nullable=False, default=0)

    last_revised_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subtopic = relationship("SubTopic", back_populates="mistakes")

    question = relationship("Question", back_populates="mistakes")
