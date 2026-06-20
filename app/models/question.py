import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enum import QuestionType, DifficultyLevel


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    subtopic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subtopics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_type = Column(
        Enum(QuestionType),
        nullable=False,
        default=QuestionType.SINGLE_MCQ,
    )

    # Rich HTML from editor (supports inline images via base64)
    text_html = Column(Text, nullable=False)

    explanation_html = Column(Text, nullable=True)

    difficulty = Column(
        Enum(DifficultyLevel),
        nullable=False,
        default=DifficultyLevel.MEDIUM,
    )

    marks = Column(Float, nullable=False, default=1.0)

    negative_marks = Column(Float, nullable=False, default=0.0)

    # Numerical question fields
    numerical_answer = Column(Float, nullable=True)

    numerical_tolerance = Column(Float, nullable=True, default=0.0)

    # Subjective answer (rich HTML)
    answer_html = Column(Text, nullable=True)

    # PYQ badge
    is_pyq = Column(Boolean, nullable=False, default=False)

    # Custom tags as array
    tags = Column(ARRAY(String), nullable=False, server_default="{}")

    order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subtopic = relationship("SubTopic", back_populates="questions")

    options = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.order",
    )

    mistakes = relationship(
        "Mistake",
        back_populates="question",
    )
