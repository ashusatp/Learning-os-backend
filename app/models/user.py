import uuid

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = Column(String, unique=True, nullable=False, index=True)

    password_hash = Column(String, nullable=True)

    name = Column(String, nullable=False)

    auth_provider = Column(String, nullable=True)

    auth_provider_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    account = relationship(
        "Account",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    goals = relationship(
        "Goal",
        back_populates="user",
        cascade="all, delete-orphan",
    )
