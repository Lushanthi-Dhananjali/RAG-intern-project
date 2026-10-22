"""
Service Interfaces and Request/Response DTOs for Lesson Plan Engine.
Defines abstract contracts (ILessonPlanMlService) and strongly typed Pydantic models
governing curriculum extraction, multi-period generation, and alignment verification.
"""

import os
import sys
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict

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
    raw_text: str = Field(..., description="Raw unstructured syllabus or curriculum guide text")


class LessonPlanGenerateRequest(BaseModel):
    query: str = Field(..., description="Topic query, lesson focus, or competency label")
    competency_level: str = Field(
        default="8.1.1",
        description="Target NIE competency level code (e.g. 8.1.1, 8.2.3, 1.6)"
    )
    grade_level: str = Field(default="Grade 8", description="Grade level (e.g. Grade 6 - Grade 9)")
    subject: str = Field(default="Civic Education", description="Academic subject area")

    # Strict clamping: 1 to 4 periods for Civic Education
    periods: int = Field(
        default=1,
        description="Number of periods to scale steps and duration (strictly clamped to 1-4 for Civic Education)"
    )
    total_periods_for_competency: Optional[int] = Field(
        default=None,
        description="Total periods allocated for this competency level across the unit (1 to 4)"
    )
    current_period: int = Field(
        default=1,
        description="Specific sequential period number being planned (e.g., Period 2 of 3)"
    )
    single_period_only: bool = Field(
        default=False,
        description="Generate only current_period while allocating outcomes across all periods"
    )

    # Class Dynamics & Environment Adaptation
    student_count: int = Field(
        default=35,
        ge=5,
        le=80,
        description="Total number of students in class for pedagogical group sizing and logistics"
    )
    classroom_environment: Optional[str] = Field(
        default="Standard Classroom",
        description="Physical learning setting (e.g., 'Standard Classroom', 'School Grounds', 'Hall')"
    )
    accessible_resources: List[str] = Field(
        default_factory=list,
        description="List of resources explicitly available in the classroom"
    )
    student_special_needs: Optional[str] = Field(
        default=None,
        description="Specific accessibility or differentiated instruction requirements"
    )

    # Teacher Modes & Strategy Directives
    teacher_mode: Literal["suggested", "own_approach"] = Field(
        default="suggested",
        description="Mode A ('suggested' for 3 options) vs Mode B ('own_approach' for teacher custom strategy)"
    )
    selected_activity_option: Optional[str] = Field(
        default=None,
        description="Text description of the chosen AI activity option"
    )
    selected_activity_title: Optional[str] = Field(
        default=None,
        description="Title of the activity selected for this individual period"
    )
    activity_options: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="The three activity options shown for this period"
    )
    custom_teacher_activity: Optional[str] = Field(
        default=None,
        description="Custom activity entered manually by the teacher overriding AI options"
    )
    previous_period_activities: List[str] = Field(
        default_factory=list,
        description="List of activities previously used in this competency sequence to prevent repetition"
    )

    # Timing Configuration
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Total duration in minutes (calculated as periods * 40 if omitted)"
    )
    time_slot: Optional[str] = Field(
        default="40 Minutes (1 Period)",
        description="Formatted time slot label (e.g., '80 Minutes (2 Periods)', '120 Minutes (3 Periods)')"
    )

    @field_validator("periods", mode="before")
    @classmethod
    def clamp_periods_input(cls, v: Any) -> int:
        """
        Enforces strict period clamping between 1 and 4.
        Ensures a single Competency Level cannot exceed 4 periods.
        """
        try:
            val = int(v) if v is not None else 1
        except (ValueError, TypeError):
            val = 1
        return max(1, min(val, 4))

    @field_validator("current_period", mode="before")
    @classmethod
    def clamp_current_period_input(cls, v: Any) -> int:
        """Clamps current_period index between 1 and 4."""
        try:
            val = int(v) if v is not None else 1
        except (ValueError, TypeError):
            val = 1
        return max(1, min(val, 4))


class LessonPlanGenerateResponse(BaseModel):
    lesson_plan: LessonPlanSchemaDto = Field(
        ...,
        description="Primary or single-period LessonPlanSchemaDto object"
    )
    lesson_plans: Optional[List[LessonPlanSchemaDto]] = Field(
        default_factory=list,
        description="Sequential list of 40-minute plans for multi-period requests (e.g. Period 1, Period 2)"
    )
    fact_check_report: Optional[Any] = Field(
        default=None,
        description="Curriculum factual grounding and hallucination check report"
    )
    alignment_report: Optional[Any] = Field(
        default=None,
        description="Pedagogical alignment and syllabus outcome verification report"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class VerifyAlignmentRequest(BaseModel):
    lesson_plan: LessonPlanSchemaDto


class AlignmentReportDto(BaseModel):
    overall_alignment_score: float = Field(..., description="Alignment score from 0.0 to 1.0")
    passed_alignment_guardrail: bool = Field(..., description="True if plan satisfies minimum threshold")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed dimension scores")


# =====================================================================
# INTERFACE DEFINITION (ILessonPlanMlService Equivalent)
# =====================================================================

class ILessonPlanMlService(ABC):
    """
    Abstract interface corresponding to ApiGateway.Services.ILessonPlanMlService.
    Orchestrates extraction, pedagogical options discovery, sequential multi-period
    RAG generation, and verification guardrails.
    """

    @abstractmethod
    async def extract_curriculum_async(
        self,
        request: CurriculumExtractRequest
    ) -> LessonPlanSchemaDto:
        """Extracts structured lesson plan metadata from raw syllabus text."""
        pass

    @abstractmethod
    async def suggest_pedagogical_options_async(
        self,
        competency_level: str,
        student_count: int = 35,
        periods: int = 1,
        requested_period: int = 1,
        grade_level: str = "Grade 8",
        subject: str = "Civic Education",
        classroom_environment: str = "Standard Classroom",
        accessible_resources: Optional[List[str]] = None,
        previous_period_activities: Optional[List[str]] = None,
        topic_query: str = ""
    ) -> Dict[str, Any]:
        """Discovers 3 meaningfully distinct student-centered activity options."""
        pass

    @abstractmethod
    async def generate_lesson_plan_async(
        self,
        request: LessonPlanGenerateRequest
    ) -> LessonPlanGenerateResponse:
        """Generates sequential 40-minute lesson plans with 5m-30m-5m strict pacing."""
        pass

    @abstractmethod
    async def verify_alignment_async(
        self,
        request: VerifyAlignmentRequest
    ) -> AlignmentReportDto:
        """Verifies pedagogical goal alignment for a generated lesson plan."""
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
        """Batch discovers and generates plans for all competencies in an educational unit."""
        pass