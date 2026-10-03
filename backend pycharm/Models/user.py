import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash = Column(
        String(255),
        nullable=False,
        default=""
    )
    full_name = Column(
        String(255),
        nullable=False,
        default=""
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Navigation Properties (One-to-Many relationships)
    saved_lesson_plans = relationship(
        "SavedLessonPlan",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    history_logs = relationship(
        "GenerationHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )