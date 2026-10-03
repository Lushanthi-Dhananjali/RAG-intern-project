import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class GenerationHistory(Base):
    __tablename__ = "generation_history"

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
    query_prompt = Column(
        String(1000),
        nullable=False,
        default=""
    )
    grounding_score = Column(
        Float,
        nullable=False,
        default=0.0
    )
    alignment_score = Column(
        Float,
        nullable=False,
        default=0.0
    )
    executed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Navigation Property (EF Core WithMany relationship)
    user = relationship("User", back_populates="history_logs")