import uuid

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enum import MasteryLevel


class SubTopic(Base):
    __tablename__ = "subtopics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String, nullable=False)

    description = Column(Text, nullable=True)

    order = Column(Integer, nullable=False, default=0)

    # Learning metadata
    revision_count = Column(Integer, nullable=False, default=0)

    last_revised_at = Column(DateTime(timezone=True), nullable=True)

    confidence_level = Column(Float, nullable=False, default=0.0)

    mastery_level = Column(
        Enum(MasteryLevel),
        nullable=False,
        default=MasteryLevel.NOT_STARTED,
    )

    questions_solved = Column(Integer, nullable=False, default=0)

    questions_correct = Column(Integer, nullable=False, default=0)

    mistake_count = Column(Integer, nullable=False, default=0)

    # Notes content
    notes_html = Column(Text, nullable=True)
    sketch_data_url = Column(Text, nullable=True)
    whiteboard_data_url = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    topic = relationship(
        "Topic",
        back_populates="subtopics",
    )

    files = relationship(
        "SubtopicFile",
        back_populates="subtopic",
        cascade="all, delete-orphan",
    )

    questions = relationship(
        "Question",
        back_populates="subtopic",
        cascade="all, delete-orphan",
    )

    mistakes = relationship(
        "Mistake",
        back_populates="subtopic",
        cascade="all, delete-orphan",
    )
