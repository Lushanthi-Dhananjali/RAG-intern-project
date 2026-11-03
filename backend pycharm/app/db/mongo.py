import logging
import os
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

logger = logging.getLogger("MongoAuthDatabase")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "rag_lesson_planner")

_client: MongoClient | None = None
_client_lock = Lock()
_indexes_ready = False


def get_auth_users_collection() -> Collection:
    """Return the MongoDB users collection and ensure auth uniqueness indexes."""
    global _client, _indexes_ready

    with _client_lock:
        if _client is None:
            _client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                tz_aware=True,
            )

        collection = _client[MONGODB_DATABASE]["users"]
        if not _indexes_ready:
            try:
                collection.create_index("username", unique=True)
                collection.create_index("email", unique=True)
                _indexes_ready = True
                logger.info("MongoDB authentication indexes are ready.")
            except Exception as e:
                logger.warning("Could not create MongoDB indexes yet: %s", e)

    return collection
