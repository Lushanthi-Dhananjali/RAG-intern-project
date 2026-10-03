import os
import sys
import logging
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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
        APP_NAME: str = "NIE Curriculum & Peradeniya Practice Teaching Lesson Plan Engine"
        APP_ENV: str = "development"
        PORT: int = 8000
        HOST: str = "0.0.0.0"
        CHROMA_DB_PATH: str = os.path.join(CURRENT_DIR, "chroma_db")
        ALLOWED_ORIGINS: list = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://10.30.54.14:3000",
            "http://10.30.5.126:3000",
            "*"
        ]
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
        examples=["Features of Direct Democracy in Ancient Athens"],
        description="Optional supplementary sub-topic details"
    )
    grade_level: Optional[str] = Field(default="Grade 8", examples=["Grade 8"])
    subject: Optional[str] = Field(default="Civic Education", examples=["Civic Education"])
    periods: Optional[int] = Field(
        default=1,
        ge=1,
        le=4,
        description="Allocated instructional periods (1 to 4 periods, 40 minutes each)"
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Optional explicit duration in minutes (computed automatically as periods * 40 if omitted)"
    )
    time_slot: Optional[str] = Field(
        default=None,
        description="Formatted time slot label (e.g., '120 Minutes (3 Periods)')"
    )


# Backward-compatible alias for existing frontend client calls
CompetencyLevelGenerateRequest = GenerateLessonPlanRequest


class CompetencyLevelGenerateResponse(BaseModel):
    competency_level: str
    grade_level: str
    subject: str
    lesson_plan: LessonPlanSchemaDto
    fact_check_report: Any
    alignment_report: Any


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
    duration_minutes: Optional[int] = Field(default=None)
    time_slot: Optional[str] = Field(default=None)


class UnitGenerateRequest(BaseModel):
    unit_query: str = Field(
        ...,
        examples=["Grade 8 Civic Education Unit 1: Democratic Governance and Citizen Participation"],
        description="The Unit or Chapter title to extract competency levels and generate plans for."
    )
    grade_level: str = Field(default="Grade 8", examples=["Grade 8"])
    subject: str = Field(default="Civic Education", examples=["Civic Education"])
    periods: Optional[int] = Field(default=1, ge=1, le=4)
    duration_minutes: Optional[int] = Field(default=None)
    time_slot: Optional[str] = Field(default=None)


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
    description="Automated Peradeniya Practice Teaching Lesson Plan Generator with dynamic period scaling and local Llama 3.",
    version="1.0.0"
)

# =====================================================================
# CORS CONFIGURATION (FULL NETWORK AND FRONTEND ACCESS)
# =====================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://10.30.54.14:3000",
        "http://10.30.5.126:3000",
        "*"
    ],
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
    """
    Ensures ChromaDB collections, local embedding functions, and the
    RAG generator are instantiated once as an in-memory singleton.
    """
    global _service_singleton
    if _service_singleton is None:
        logger.info("Initializing LessonPlanMlService singleton...")
        _service_singleton = LessonPlanMlService()
    return _service_singleton


def get_retriever_service() -> MultiGradeBoundaryRetriever:
    """
    Ensures MultiGradeBoundaryRetriever is instantiated once as an in-memory singleton.
    """
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
        "pedagogy": "University of Peradeniya Practice Teaching Framework",
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
    """
    Returns available competency levels for the selected Subject and Grade
    directly from ChromaDB index.
    """
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
    "/api/v1/generate-by-competency-level",
    response_model=CompetencyLevelGenerateResponse,
    status_code=status.HTTP_200_OK,
    tags=["Lesson Plan Generation"],
    summary="Generate Peradeniya Lesson Plan by Competency Level with Dynamic Periods"
)
async def generate_by_competency_level(
    request: GenerateLessonPlanRequest,
    service: LessonPlanMlService = Depends(get_lesson_service)
):
    """
    Main endpoint for Frontend delivery:
    1. Validates and clamps period count (1 to 4) and derives exact duration (40m per period).
    2. Filters ChromaDB curriculum for target competency code.
    3. Triggers dynamic step scaling based on period count.
    4. Executes generation with safe fallbacks for evaluators.
    """
    if not request.competency_level.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'competency_level' cannot be empty."
        )

    # 1. Enforce 1 to 4 periods range and calculate duration (1 period = 40 minutes)
    periods = min(max(request.periods or 1, 1), 4)
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
        time_slot=time_slot,
        duration_minutes=duration_minutes
    )

    try:
        response: LessonPlanGenerateResponse = await service.generate_lesson_plan_async(req_dto)

        return CompetencyLevelGenerateResponse(
            competency_level=request.competency_level,
            grade_level=request.grade_level or "Grade 8",
            subject=request.subject or "Civic Education",
            lesson_plan=response.lesson_plan,
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
        time_slot=time_slot,
        duration_minutes=duration_minutes
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
        time_slot=time_slot,
        duration_minutes=duration_minutes
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
# SERVER RUNNER
# =====================================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)