from app.db.session import Base, engine

# Import all entity models so metadata is registered to Base
from app.models.user import User
from app.models.saved_lesson_plan import SavedLessonPlan
from app.models.generation_history import GenerationHistory


def init_db():
    """
    Creates tables directly if running without migrations
    (equivalent to dbContext.Database.EnsureCreated()).
    """
    Base.metadata.create_all(bind=engine)