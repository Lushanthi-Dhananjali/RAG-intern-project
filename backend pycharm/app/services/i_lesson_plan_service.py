import os
import sys
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Support both legacy LessonPlanSchema and updated LEARN LessonPlanSchemaDto
try:
    from app.schemas.lesson_plan_schema_dto import LessonPlanSchemaDto
except ModuleNotFoundError:
    try:
        from schemas.lesson_plan_schema_dto import LessonPlanSchemaDto
    except ModuleNotFoundError:
        try:
            from lesson_plan_schema_dto import LessonPlanSchemaDto
        except ModuleNotFoundError:
            from schema import LessonPlanSchema as LessonPlanSchemaDto


# =====================================================================
# DTO MODELS (ApiGateway.DTOs Equivalent)
# =====================================================================
class CurriculumExtractRequest(BaseModel):
    raw_text: str = Field(..., description="Raw unstructured syllabus or curriculum text")


class LessonPlanGenerateRequest(BaseModel):
    query: str = Field(..., description="Topic or lesson focus")
    competency_level: str = Field(default="8.1.1", description="Target competency level code (e.g. 8.1.1, 8.2.3)")
    grade_level: str = Field(default="Grade 8", description="Grade level")
    subject: str = Field(default="Civic Education", description="Academic subject area")
    periods: Optional[int] = Field(
        default=1,
        ge=1,
        le=4,
        description="Number of periods to scale steps and duration (1 to 4 periods, 40 mins each)"
    )
    time_slot: Optional[str] = Field(
        default="40 Minutes (1 Period)",
        description="Formatted time slot label (e.g., '80 Minutes (2 Periods)', '120 Minutes (3 Periods)')"
    )
    duration_minutes: Optional[int] = Field(
        default=40,
        description="Total duration in minutes (calculated as periods * 40 if omitted)"
    )


class LessonPlanGenerateResponse(BaseModel):
    lesson_plan: LessonPlanSchemaDto
    fact_check_report: Any
    alignment_report: Any


class VerifyAlignmentRequest(BaseModel):
    lesson_plan: LessonPlanSchemaDto


class AlignmentReportDto(BaseModel):
    overall_alignment_score: float
    passed_alignment_guardrail: bool
    details: Optional[Dict[str, Any]] = None


# =====================================================================
# INTERFACE DEFINITION (ILessonPlanMlService Equivalent)
# =====================================================================
class ILessonPlanMlService(ABC):
    """
    Abstract interface corresponding to ApiGateway.Services.ILessonPlanMlService.
    Orchestrates extraction, period-scaled RAG generation, and pedagogical verification.
    """

    @abstractmethod
    async def extract_curriculum_async(
        self,
        request: CurriculumExtractRequest
    ) -> LessonPlanSchemaDto:
        """Translates to Task<LessonPlanSchemaDto> ExtractCurriculumAsync(...)"""
        pass

    @abstractmethod
    async def generate_lesson_plan_async(
        self,
        request: LessonPlanGenerateRequest
    ) -> LessonPlanGenerateResponse:
        """Translates to Task<LessonPlanGenerateResponse> GenerateLessonPlanAsync(...)"""
        pass

    @abstractmethod
    async def verify_alignment_async(
        self,
        request: VerifyAlignmentRequest
    ) -> AlignmentReportDto:
        """Translates to Task<AlignmentReportDto> VerifyAlignmentAsync(...)"""
        pass

    @abstractmethod
    async def generate_unit_plans_async(
        self,
        unit_query: str,
        grade_level: str = "Grade 8",
        subject: str = "Civic Education",
        periods: int = 1,
        time_slot: Optional[str] = None,
        duration_minutes: Optional[int] = None
    ) -> List[LessonPlanSchemaDto]:
        """Translates to Task<List<LessonPlanSchemaDto>> GenerateUnitPlansAsync(...)"""
        pass