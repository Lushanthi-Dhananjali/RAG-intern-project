import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.schemas.lesson_plan_schema_dto import LessonPlanSchemaDto
from app.services.lesson_plan_service import LessonPlanMlService
from app.services.i_lesson_plan_service import LessonPlanGenerateRequest, LessonPlanGenerateResponse

logger = logging.getLogger("LessonPlanAPI")

router = APIRouter(prefix="/api/v1", tags=["Lesson Plan Generation"])

# Request payload from frontend (Next.js)
class GenerateByCompetencyRequest(BaseModel):
    query: str = Field(..., example="Features of Direct Democracy in Ancient Athens")
    competency_level: str = Field(..., example="8.1.1")
    grade_level: str = Field(default="Grade 8", example="Grade 8")
    subject: str = Field(default="Civic Education", example="Civic Education")
    time_slot: str = Field(default="40 Minutes (1 Period)", example="40 Minutes (1 Period)")
    duration_minutes: int = Field(default=40, example=40)


# Dependency injection for the orchestration service singleton
def get_lesson_plan_service() -> LessonPlanMlService:
    return LessonPlanMlService()


@router.post(
    "/generate-by-competency-level",
    response_model=LessonPlanGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Peradeniya 5E Lesson Plan by Competency Level"
)
async def generate_by_competency_level(
    payload: GenerateByCompetencyRequest,
    service: LessonPlanMlService = Depends(get_lesson_plan_service)
):
    """
    1. Queries ChromaDB for exact NIE syllabus and textbook chunks.
    2. Enforces Peradeniya 5E structure via prompt templates.
    3. Runs token-constrained grammar decoding via local Llama 3 (Ollama).
    4. Validates schema and guardrails, returning structured JSON to frontend.
    """
    logger.info("Received generation request for Competency %s: '%s'", payload.competency_level, payload.query)

    try:
        # Map controller payload into service DTO
        request_dto = LessonPlanGenerateRequest(
            query=payload.query,
            competency_level=payload.competency_level,
            grade_level=payload.grade_level,
            subject=payload.subject,
            time_slot=payload.time_slot,
            duration_minutes=payload.duration_minutes
        )

        response: LessonPlanGenerateResponse = await service.generate_lesson_plan_async(request_dto)
        return response

    except ConnectionError as conn_err:
        logger.error("LLM Server unreachable: %s", conn_err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Local Ollama service unavailable: {str(conn_err)}"
        )
    except ValueError as val_err:
        logger.error("Schema or validation failure: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Pedagogical validation error: {str(val_err)}"
        )
    except Exception as exc:
        logger.exception("Unexpected error during plan generation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal pipeline failure: {str(exc)}"
        )