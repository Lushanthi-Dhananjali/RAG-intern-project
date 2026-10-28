import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.db.session import Base


class User(Base):
    """
    User entity dedicated solely to MySQL login and signup authentication.
    No other project tables or lesson plans are linked here.
    """
    __tablename__ = "users"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    username = Column(
        String(100),
        unique=True,
        nullable=False,
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
        nullable=True,
        default=""
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
