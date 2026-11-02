import logging
from app.db.session import engine
from app.models.user import User

logger = logging.getLogger("DatabaseInit")


def init_db():
    """
    Creates the SQL user table required by legacy lesson-history relationships.
    Signup and login profiles are stored separately in MongoDB.
    """
    try:
        logger.info("Verifying SQL users table for lesson-history relationships...")
        User.__table__.create(bind=engine, checkfirst=True)
        logger.info("SQL 'users' compatibility table is ready.")
    except Exception as exc:
        logger.error(
            "SQL compatibility database initialization error: %s\n"
            "Action required:\n"
            "1. Make sure MariaDB/MySQL is running.\n"
            "2. Make sure the database exists: CREATE DATABASE IF NOT EXISTS rag_lesson_planner;\n"
            "3. If your MySQL 'root' user has a password, set it in backend .env:\n"
            "   DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/rag_lesson_planner\n"
            "   (Or if no password: mysql+pymysql://root:@localhost:3306/rag_lesson_planner)",
            exc
        )