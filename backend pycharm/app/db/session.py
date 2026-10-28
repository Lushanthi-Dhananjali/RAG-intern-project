import os
import logging
from typing import Generator
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("DatabaseSession")

# 1. Check if individual MySQL parameters are set (avoids special character issues in password)
mysql_user = os.getenv("MYSQL_USER")
mysql_password = os.getenv("MYSQL_PASSWORD")
mysql_host = os.getenv("MYSQL_HOST", "localhost")
mysql_port = os.getenv("MYSQL_PORT", "3306")
mysql_db = os.getenv("MYSQL_DATABASE")

if mysql_user and mysql_db:
    # URL encode password so special characters (@, #, $, etc.) don't break SQLAlchemy URL
    encoded_pw = quote_plus(mysql_password) if mysql_password else ""
    pw_part = f":{encoded_pw}" if encoded_pw else ""
    DATABASE_URL = f"mysql+pymysql://{mysql_user}{pw_part}@{mysql_host}:{mysql_port}/{mysql_db}"
else:
    # 2. Or read full DATABASE_URL directly from .env
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app_database.db")

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif "mysql" in DATABASE_URL:
    # Recycle connections every 1 hour to avoid MySQL 'server has gone away' timeouts
    engine_kwargs["pool_recycle"] = 3600
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request,
    closing it automatically when finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()