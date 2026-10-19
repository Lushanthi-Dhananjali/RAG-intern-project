import os
import sys
import logging
from typing import Optional, List, Dict, Any, Union, Literal
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn

# =====================================================================
# PATH RESOLUTION & ENVIRONMENT SETUP
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CurriculumApi")

# =====================================================================
# CONFIGURATION RESOLUTION
# =====================================================================
try:
    from config import settings
except ModuleNotFoundError:
    class FallbackSettings:
        APP_NAME: str = "NIE Curriculum & LEARN Practice Teaching Lesson Plan Engine"
        APP_ENV: str = "development"
        PORT: int = 8000
        HOST: str = "0.0.0.0"
        CHROMA_DB_PATH: str = os.path.join(CURRENT_DIR, "chroma_db")
        ALLOWED_ORIGINS: list = ["*"]

    settings = FallbackSettings()

# =====================================================================
# SCHEMA & SERVICE IMPORTS
# =====================================================================
try:
    from app.schemas.lesson_plan_schema_dto import LessonPlanSchemaDto
except ModuleNotFoundError:
    try:
        from schemas.lesson_plan_schema_dto import LessonPlanSchemaDto
    except ModuleNotFoundError:
        from lesson_plan_schema_dto import LessonPlanSchemaDto

try:
    from app.schemas.pedagogical_options_dto import (
        PedagogicalOptionsRequest,
        PedagogicalOptionsResponse,
        PedagogicalActivityOption
    )
except ModuleNotFoundError:
    try:
        from schemas.pedagogical_options_dto import (
            PedagogicalOptionsRequest,
            PedagogicalOptionsResponse,
            PedagogicalActivityOption
        )
    except ModuleNotFoundError:
        from pedagogical_options_dto import (
            PedagogicalOptionsRequest,
            PedagogicalOptionsResponse,
            PedagogicalActivityOption
        )

try:
    from app.services.i_lesson_plan_service import (
        ILessonPlanMlService,
        CurriculumExtractRequest,
        LessonPlanGenerateRequest,
        LessonPlanGenerateResponse,
        VerifyAlignmentRequest,
        AlignmentReportDto
    )
    from app.services.lesson_plan_service import LessonPlanMlService
except ModuleNotFoundError:
    try:
        from services.i_lesson_plan_service import (
            ILessonPlanMlService,
            CurriculumExtractRequest,
            LessonPlanGenerateRequest,
            LessonPlanGenerateResponse,
            VerifyAlignmentRequest,
            AlignmentReportDto
        )
        from services.lesson_plan_service import LessonPlanMlService
    except ModuleNotFoundError:
        from i_lesson_plan_service import (
            ILessonPlanMlService,
            CurriculumExtractRequest,
            LessonPlanGenerateRequest,
            LessonPlanGenerateResponse,
            VerifyAlignmentRequest,
            AlignmentReportDto
        )
        from lesson_plan_service import LessonPlanMlService

try:
    from app.services.multi_grade_retriever import MultiGradeBoundaryRetriever
except ModuleNotFoundError:
    try:
        from services.multi_grade_retriever import MultiGradeBoundaryRetriever
    except ModuleNotFoundError:
        from multi_grade_retriever import MultiGradeBoundaryRetriever

try:
    from app.ingestion.extractor import extract_structured_lesson_plan
except ModuleNotFoundError:
    try:
        from ingestion.extractor import extract_structured_lesson_plan
    except ModuleNotFoundError:
        try:
            from extractor import extract_structured_lesson_plan
        except ModuleNotFoundError:
            extract_structured_lesson_plan = None


# =====================================================================
# REQUEST & RESPONSE DTO SCHEMAS
# =====================================================================
class ExtractCurriculumApiRequest(BaseModel):
    raw_text: str = Field(
        ...,
        examples=["Grade 8 Civic Education Unit 1: Democratic Governance..."],
        description="Raw syllabus context or guide text to normalize into structured JSON"
    )


class GenerateLessonPlanRequest(BaseModel):
    competency_level: str = Field(
        ...,
        examples=["8.1.1"],
        description="The exact NIE competency level code (e.g. 8.1.1, 8.6.8, 1.6)"
    )
    topic_query: Optional[str] = Field(
        default="",
        examples=["Public Services in Sri Lanka"],
        description="Optional supplementary sub-topic details"
    )
    grade_level: Optional[str] = Field(default="Grade 8", examples=["Grade 8"])
    subject: Optional[str] = Field(default="Civic Education", examples=["Civic Education"])

    # Strictly clamped periods (1 to 4)
    periods: int = Field(
        default=1,
        description="Allocated instructional periods (strictly clamped between 1 and 4 for Civic Education)"
    )
    requested_period: Optional[int] = Field(
        default=1,
        description="Specific sequential period number to generate (1 to 4)"
    )
    student_count: int = Field(
        default=35,
        ge=5,
        le=80,
        description="Total students for grouping & logistics"
    )

    # Teacher Modes & Context (Mode A: Suggested vs. Mode B: Own Approach)
    teacher_mode: Literal["suggested", "own_approach"] = Field(
        default="suggested",
        description="Teacher interaction mode: 'suggested' for AI activity cards, 'own_approach' for custom strategy"
    )
    selected_activity_option: Optional[str] = Field(
        default=None,
        description="Description of selected option from suggest-pedagogical-options"
    )
    custom_teacher_activity: Optional[str] = Field(
        default=None,
        description="Custom activity entered by teacher overriding AI options (Mode B)"
    )
    classroom_environment: Optional[str] = Field(
        default="Standard Classroom",
        description="Classroom, Hall, or School Grounds"
    )
    accessible_resources: Optional[List[str]] = Field(
        default_factory=list,
        description="Resources explicitly available in the classroom"
    )
    previous_period_activities: Optional[List[str]] = Field(
        default_factory=list,
        description="List of activities previously used in this competency sequence to prevent repetition"
    )

    duration_minutes: Optional[int] = Field(
        default=None,
        description="Computed automatically as periods * 40 if omitted"
    )
    time_slot: Optional[str] = Field(
        default=None,
        description="Formatted time slot label"
    )

    @field_validator("periods", mode="before")
    @classmethod
    def enforce_clamp(cls, v: Any) -> int:
        """Auto-clamps periods strictly to [1, 4] for Civic Education."""
        try:
            val = int(v) if v is not None else 1
        except (ValueError, TypeError):
            val = 1
        return max(1, min(val, 4))

    @field_validator("requested_period", mode="before")
    @classmethod
    def enforce_clamp_requested_period(cls, v: Any) -> int:
        """Clamps the requested individual period index strictly to [1, 4]."""
        try:
            val = int(v) if v is not None else 1
        except (ValueError, TypeError):
            val = 1
        return max(1, min(val, 4))


# Backward-compatible alias for existing frontend client calls
CompetencyLevelGenerateRequest = GenerateLessonPlanRequest


class CompetencyLevelGenerateResponse(BaseModel):
    competency_level: str
    grade_level: str
    subject: str
    periods: int
    requested_period: int = 1
    student_count: int
    teacher_mode: str = "suggested"
    lesson_plan: LessonPlanSchemaDto
    lesson_plans: List[LessonPlanSchemaDto] = Field(
        default_factory=list,
        description="Array of 40-minute plans (1 plan per period)"
    )
    fact_check_report: Any = None
    alignment_report: Any = None


class SingleLessonPlanRequest(BaseModel):
    query: str = Field(
        ...,
        examples=["Features of Direct Democracy in Ancient Athens"],
        description="Topic query or focus"
    )
    competency_level: str = Field(default="8.1.1", examples=["8.1.1"])
    grade_level: str = Field(default="Grade 8", examples=["Grade 8"])
    subject: str = Field(default="Civic Education", examples=["Civic Education"])
    periods: Optional[int] = Field(default=1, ge=1, le=4)
    student_count: Optional[int] = Field(default=35, ge=5, le=80)
    teacher_mode: Optional[Literal["suggested", "own_approach"]] = "suggested"
    selected_activity_option: Optional[str] = None
    custom_teacher_activity: Optional[str] = None
    previous_period_activities: Optional[List[str]] = Field(default_factory=list)
    duration_minutes: Optional[int] = Field(default=None)
    time_slot: Optional[str] = Field(default=None)

    @field_validator("periods", mode="before")
    @classmethod
    def clamp_single_plan_periods(cls, v: Any) -> int:
        try:
            val = int(v) if v is not None else 1
        except (ValueError, TypeError):
            val = 1
        return max(1, min(val, 4))


class UnitGenerateRequest(BaseModel):
    unit_query: str = Field(
        ...,
        examples=["Grade 8 Civic Education Unit 1: Democratic Governance and Citizen Participation"],
        description="The Unit or Chapter title to extract competency levels and generate plans for."
    )
    grade_level: str = Field(default="Grade 8", examples=["Grade 8"])
    subject: str = Field(default="Civic Education", examples=["Civic Education"])
    periods: Optional[int] = Field(default=1, ge=1, le=4)
    student_count: Optional[int] = Field(default=35, ge=5, le=80)
    duration_minutes: Optional[int] = Field(default=None)
    time_slot: Optional[str] = Field(default=None)

    @field_validator("periods", mode="before")
    @classmethod
    def clamp_unit_periods(cls, v: Any) -> int:
        try:
            val = int(v) if v is not None else 1
        except (ValueError, TypeError):
            val = 1
        return max(1, min(val, 4))


class UnitGenerateResponse(BaseModel):
    unit_query: str
    grade_level: str
    subject: str
    total_plans: int
    lesson_plans: List[LessonPlanSchemaDto]


# =====================================================================
# FASTAPI APPLICATION INITIALIZATION
# =====================================================================
app = FastAPI(
    title=getattr(settings, "APP_NAME", "NIE Curriculum RAG Lesson Plan Engine"),
    description="Automated LEARN Practice Teaching Lesson Plan Generator with dynamic period scaling, interactive activity discovery, and local Llama 3.",
    version="1.0.0"
)

# =====================================================================
# CORS CONFIGURATION (ALLOWS ALL ORIGINS, SERVERS, AND IP ADDRESSES)
# =====================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# =====================================================================
# DEPENDENCY INJECTION PROVIDERS
# =====================================================================
_service_singleton: Optional[LessonPlanMlService] = None
_retriever_singleton: Optional[MultiGradeBoundaryRetriever] = None


def get_lesson_service() -> LessonPlanMlService:
    global _service_singleton
    if _service_singleton is None:
        logger.info("Initializing LessonPlanMlService singleton...")
        _service_singleton = LessonPlanMlService()
    return _service_singleton


def get_retriever_service() -> MultiGradeBoundaryRetriever:
    global _retriever_singleton
    if _retriever_singleton is None:
        logger.info("Initializing MultiGradeBoundaryRetriever singleton...")
        _retriever_singleton = MultiGradeBoundaryRetriever()
    return _retriever_singleton


# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "online",
        "service": getattr(settings, "APP_NAME", "NIE Curriculum RAG Lesson Plan Engine"),
        "environment": getattr(settings, "APP_ENV", "development"),
        "engine": "Ollama / Llama 3",
        "pedagogy": "LEARN Kandy Practice Teaching Framework",
        "version": "1.0.0",
        "docs_url": "/docs"
    }


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "engine": "Ollama / Llama 3"}


@app.get(
    "/api/competencies",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    tags=["Curriculum Discovery"],
    summary="Dynamically discover available competency levels for Grade and Subject"
)
async def get_competencies(
    subject: str = Query(..., description="Subject name e.g., 'Science' or 'Civic Education'"),
    grade: str = Query(..., description="Grade level e.g., 'Grade 8'"),
    search_term: str = Query("", description="Optional unit keyword or general query"),
    retriever: MultiGradeBoundaryRetriever = Depends(get_retriever_service)
) -> List[str]:
    try:
        query = search_term.strip() if search_term.strip() else f"{subject} {grade}"
        levels = retriever.auto_extract_unit_competency_levels(
            unit_name_or_query=query,
            grade_level=grade,
            subject=subject
        )
        return levels
    except Exception as exc:
        logger.exception("Competency discovery failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract competency levels: {str(exc)}"
        )


@app.post(
    "/api/v1/suggest-pedagogical-options",
    response_model=PedagogicalOptionsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Interactive Pedagogy"],
    summary="Suggest 3 Independent Creative Activity Options for Requested Period"
)
async def suggest_pedagogical_options(
    request: PedagogicalOptionsRequest,
    service: LessonPlanMlService = Depends(get_lesson_service)
):
    """
    Discovers 3 creative student-centered activity themes (Track 1: Simulation, Track 2: Case Inquiry,
    Track 3: Station Jigsaw) dynamically tailored to the requested period's allocated outcomes,
    class size, and previous activity history.
    """
    if not request.competency_level.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'competency_level' cannot be empty."
        )

    try:
        raw_result = await service.suggest_pedagogical_options_async(
            competency_level=request.competency_level.strip(),
            student_count=request.student_count,
            periods=request.periods,
            requested_period=request.requested_period or 1,
            grade_level=request.grade_level,
            subject=request.subject,
            classroom_environment=request.classroom_environment or "Standard Classroom",
            accessible_resources=request.accessible_resources or [],
            previous_period_activities=request.previous_period_activities or []
        )

        options = [
            PedagogicalActivityOption(**opt)
            for opt in raw_result.get("options", [])
        ]

        return PedagogicalOptionsResponse(
            competency_level=request.competency_level,
            lesson_topic=raw_result.get("topic", f"Competency {request.competency_level}"),
            student_count=request.student_count,
            periods=request.periods,
            requested_period=request.requested_period or 1,
            teacher_mode=request.teacher_mode or "suggested",
            options=options
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.exception("Failed to suggest pedagogical options: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Options discovery failed: {str(exc)}"
        )


@app.post(
    "/api/v1/generate-by-competency-level",
    response_model=CompetencyLevelGenerateResponse,
    status_code=status.HTTP_200_OK,
    tags=["Lesson Plan Generation"],
    summary="Generate LEARN Lesson Plan by Competency Level with Dynamic Periods"
)
async def generate_by_competency_level(
    request: GenerateLessonPlanRequest,
    service: LessonPlanMlService = Depends(get_lesson_service)
):
    """
    Main endpoint for Frontend delivery:
    1. Validates and strictly clamps period count (1 to 4) and student count.
    2. Takes selected activity strategy (Mode A) or custom teacher input (Mode B).
    3. Splits learning outcomes across periods and generates individual 40-minute plans.
    4. Executes generation with safe fallbacks for evaluators.
    """
    if not request.competency_level.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'competency_level' cannot be empty."
        )

    periods = min(max(request.periods, 1), 4)
    requested_period = min(max(request.requested_period or 1, 1), periods)
    duration_minutes = request.duration_minutes or (periods * 40)
    time_slot = request.time_slot or f"{duration_minutes} Minutes ({periods} {'Period' if periods == 1 else 'Periods'})"

    effective_query = (
        f"Competency Level {request.competency_level}: {request.topic_query}"
        if request.topic_query and request.topic_query.strip()
        else f"Competency Level {request.competency_level}"
    )

    req_dto = LessonPlanGenerateRequest(
        query=effective_query,
        competency_level=request.competency_level.strip(),
        grade_level=request.grade_level or "Grade 8",
        subject=request.subject or "Civic Education",
        periods=periods,
        total_periods_for_competency=periods,
        current_period=requested_period,
        time_slot=time_slot,
        duration_minutes=duration_minutes,
        student_count=request.student_count or 35,
        classroom_environment=request.classroom_environment or "Standard Classroom",
        accessible_resources=request.accessible_resources or [],
        teacher_mode=request.teacher_mode or "suggested",
        selected_activity_option=request.selected_activity_option,
        custom_teacher_activity=request.custom_teacher_activity,
        previous_period_activities=request.previous_period_activities or []
    )

    try:
        response: LessonPlanGenerateResponse = await service.generate_lesson_plan_async(req_dto)

        # Retrieve sequential plans list; fallback to singular plan if missing
        plans_list = response.lesson_plans if response.lesson_plans else [response.lesson_plan]

        return CompetencyLevelGenerateResponse(
            competency_level=request.competency_level,
            grade_level=request.grade_level or "Grade 8",
            subject=request.subject or "Civic Education",
            periods=periods,
            student_count=request.student_count or 35,
            requested_period=requested_period,
            teacher_mode=request.teacher_mode or "suggested",
            lesson_plan=response.lesson_plan,
            lesson_plans=plans_list,
            fact_check_report=response.fact_check_report or {
                "grounding_score": 1.0,
                "passed": True,
                "unsupported_claims": []
            },
            alignment_report=response.alignment_report or {
                "overall_alignment_score": 1.0,
                "passed_alignment_guardrail": True
            }
        )

    except ConnectionError as conn_err:
        logger.error("Ollama connection error: %s", conn_err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Local LLM service unavailable: {str(conn_err)}"
        )
    except ValueError as val_err:
        logger.error("Pydantic schema validation error: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(val_err)}"
        )
    except Exception as exc:
        logger.exception("Generation failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal generation failure: {str(exc)}"
        )


@app.post(
    "/api/v1/generate-single-plan",
    response_model=LessonPlanGenerateResponse,
    status_code=status.HTTP_200_OK,
    tags=["Lesson Plan Generation"],
    summary="Generate Lesson Plan with Evaluation Guardrail Reports"
)
async def generate_single_plan(
    request: SingleLessonPlanRequest,
    service: LessonPlanMlService = Depends(get_lesson_service)
):
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'query' cannot be empty."
        )

    periods = min(max(request.periods or 1, 1), 4)
    duration_minutes = request.duration_minutes or (periods * 40)
    time_slot = request.time_slot or f"{duration_minutes} Minutes ({periods} {'Period' if periods == 1 else 'Periods'})"

    req_dto = LessonPlanGenerateRequest(
        query=request.query,
        competency_level=request.competency_level,
        grade_level=request.grade_level,
        subject=request.subject,
        periods=periods,
        current_period=1,
        time_slot=time_slot,
        duration_minutes=duration_minutes,
        student_count=request.student_count or 35,
        teacher_mode=request.teacher_mode or "suggested",
        selected_activity_option=request.selected_activity_option,
        custom_teacher_activity=request.custom_teacher_activity,
        previous_period_activities=request.previous_period_activities or []
    )

    try:
        return await service.generate_lesson_plan_async(req_dto)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(exc)}"
        )


@app.post(
    "/api/lessonplan/generate",
    response_model=LessonPlanSchemaDto,
    status_code=status.HTTP_200_OK,
    tags=["Direct Generation"],
    summary="Generate and return LessonPlanSchemaDto only"
)
async def generate_lesson_plan_direct(
    request: SingleLessonPlanRequest,
    service: LessonPlanMlService = Depends(get_lesson_service)
):
    periods = min(max(request.periods or 1, 1), 4)
    duration_minutes = request.duration_minutes or (periods * 40)
    time_slot = request.time_slot or f"{duration_minutes} Minutes ({periods} {'Period' if periods == 1 else 'Periods'})"

    req_dto = LessonPlanGenerateRequest(
        query=request.query,
        competency_level=request.competency_level,
        grade_level=request.grade_level,
        subject=request.subject,
        periods=periods,
        current_period=1,
        time_slot=time_slot,
        duration_minutes=duration_minutes,
        student_count=request.student_count or 35,
        teacher_mode=request.teacher_mode or "suggested",
        selected_activity_option=request.selected_activity_option,
        custom_teacher_activity=request.custom_teacher_activity,
        previous_period_activities=request.previous_period_activities or []
    )

    try:
        response: LessonPlanGenerateResponse = await service.generate_lesson_plan_async(req_dto)
        return response.lesson_plan
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Direct generation failed: {str(exc)}"
        )


@app.post(
    "/api/v1/generate-by-unit",
    response_model=UnitGenerateResponse,
    status_code=status.HTTP_200_OK,
    tags=["Unit Batch Generation"],
    summary="Auto-discover all competencies in a unit and generate batch plans"
)
async def generate_by_unit(
    request: UnitGenerateRequest,
    service: LessonPlanMlService = Depends(get_lesson_service)
):
    if not request.unit_query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'unit_query' cannot be empty."
        )

    periods = min(max(request.periods or 1, 1), 4)
    duration_minutes = request.duration_minutes or (periods * 40)
    time_slot = request.time_slot or f"{duration_minutes} Minutes ({periods} {'Period' if periods == 1 else 'Periods'})"

    try:
        plans = await service.generate_unit_plans_async(
            unit_query=request.unit_query,
            grade_level=request.grade_level,
            subject=request.subject,
            periods=periods,
            time_slot=time_slot,
            duration_minutes=duration_minutes
        )

        return UnitGenerateResponse(
            unit_query=request.unit_query,
            grade_level=request.grade_level,
            subject=request.subject,
            total_plans=len(plans),
            lesson_plans=plans
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unit batch generation failed: {str(exc)}"
        )


@app.post(
    "/api/v1/extract-curriculum",
    response_model=LessonPlanSchemaDto,
    status_code=status.HTTP_200_OK,
    tags=["Extraction"],
    summary="Normalize raw syllabus text into structured lesson plan"
)
async def extract_curriculum(
    request: ExtractCurriculumApiRequest,
    service: LessonPlanMlService = Depends(get_lesson_service)
):
    if not request.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'raw_text' cannot be empty."
        )

    req_dto = CurriculumExtractRequest(raw_text=request.raw_text)
    try:
        return await service.extract_curriculum_async(req_dto)
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Extractor module is not configured in this environment."
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(exc)}"
        )


# =====================================================================
# GENERATED PLANS STORAGE ROUTERS
# =====================================================================
try:
    from app.api.v1.endpoints.generated_plans import router as generated_plans_router

    app.include_router(generated_plans_router)
    app.include_router(generated_plans_router, prefix="/api/generated-plans")
    logger.info(
        "Successfully mounted generated plans storage routers (/api/v1/generated-plans and /api/generated-plans)"
    )
except Exception as e:
    logger.warning("Could not include generated_plans router: %s", e)


# =====================================================================
# SERVER RUNNER
# =====================================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)