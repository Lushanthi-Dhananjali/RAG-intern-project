import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class SavedLessonPlan(Base):
    __tablename__ = "saved_lesson_plans"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(
        String(255),
        nullable=False,
        default=""
    )
    grade_level = Column(
        String(50),
        nullable=False,
        default=""
    )
    topic = Column(
        String(255),
        nullable=False,
        default=""
    )
    # Stores full structured LessonPlanSchema JSON payload
    plan_json_data = Column(
        Text,
        nullable=False,
        default="{}"
    )
    saved_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Navigation Property (EF Core WithMany relationship)
    user = relationship("User", back_populates="saved_lesson_plans")