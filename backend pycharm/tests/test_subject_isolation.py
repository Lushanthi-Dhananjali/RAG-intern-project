import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.subject_guard import is_civic_creative_pipeline_enabled
from app.services.i_lesson_plan_service import LessonPlanGenerateRequest
from app.services.lesson_plan_service import LessonPlanMlService
from app.schemas.lesson_plan_schema_dto import LessonPlanSchemaDto


@pytest.fixture
def mock_service():
    with patch("app.services.lesson_plan_service.RAGLessonPlanGenerator"), \
         patch("app.services.lesson_plan_service.chromadb.PersistentClient"):
        service = LessonPlanMlService()
        return service


def test_scope_guard_evaluation():
    """Verify that only Civic Education for Grades 6-9 enables the creative pipeline."""
    # Must be False for Science across all grades
    assert is_civic_creative_pipeline_enabled("Science", "Grade 6") is False
    assert is_civic_creative_pipeline_enabled("Science", "Grade 7") is False
    assert is_civic_creative_pipeline_enabled("Science", "Grade 8") is False
    assert is_civic_creative_pipeline_enabled("Science", "Grade 9") is False

    # Must be False for other subjects
    assert is_civic_creative_pipeline_enabled("Mathematics", "Grade 8") is False
    assert is_civic_creative_pipeline_enabled("English", "Grade 8") is False

    # Must be True ONLY for Civic Education Grades 6-9
    assert is_civic_creative_pipeline_enabled("Civic Education", "Grade 8") is True
    assert is_civic_creative_pipeline_enabled("civic education", "Grade 7") is True


@pytest.mark.asyncio
async def test_science_routes_strictly_to_legacy_pipeline(mock_service):
    """Verify that a Science request invokes the legacy handler and bypasses Civic outcome splitting."""
    req = LessonPlanGenerateRequest(
        query="Photosynthesis and Plant Cellular Respiration",
        competency_level="8.2.1",
        grade_level="Grade 8",
        subject="Science",
        periods=2
    )

    # Mock internal runners
    mock_service._execute_civic_creative_pipeline = AsyncMock()
    mock_service._execute_legacy_pipeline = AsyncMock(return_value="legacy_executed")

    await mock_service.generate_lesson_plan_async(req)

    # Assert Route B was called and Route A was never touched
    mock_service._execute_legacy_pipeline.assert_awaited_once()
    mock_service._execute_civic_creative_pipeline.assert_not_awaited()


@pytest.mark.asyncio
async def test_suggest_pedagogical_options_rejects_science(mock_service):
    """Ensure that the creative activity discovery endpoint strictly blocks Science."""
    with pytest.raises(ValueError) as exc_info:
        await mock_service.suggest_pedagogical_options_async(
            competency_level="8.1.1",
            grade_level="Grade 8",
            subject="Science"
        )
    assert "restricted to Civic Education" in str(exc_info.value)