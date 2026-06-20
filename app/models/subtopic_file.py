import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class SubtopicFile(Base):
    __tablename__ = "subtopic_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    subtopic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subtopics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String, nullable=False)

    original_name = Column(String, nullable=False)

    content_type = Column(String, nullable=False)

    size = Column(Integer, nullable=False)

    storage_path = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    subtopic = relationship("SubTopic", back_populates="files")
