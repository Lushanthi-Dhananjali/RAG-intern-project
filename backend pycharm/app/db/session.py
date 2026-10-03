import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Pull connection string from environment variable or fallback to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app_database.db")

# SQLite needs connect_args check_same_thread set to False for FastAPI threads
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request,
    closing it automatically when finished (equivalent to ASP.NET AddDbContext).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()