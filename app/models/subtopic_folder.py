import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class SubtopicFolder(Base):
    __tablename__ = "subtopic_folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    subtopic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subtopics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subtopic_folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    name = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    subtopic = relationship("SubTopic", back_populates="folders")
    parent = relationship("SubtopicFolder", remote_side=[id], backref="children")
    files = relationship("SubtopicFile", back_populates="folder")
