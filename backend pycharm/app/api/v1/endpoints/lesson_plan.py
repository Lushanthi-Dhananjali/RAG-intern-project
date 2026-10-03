import json
import logging
from typing import Optional, AsyncGenerator
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

# Database dependencies & models
from app.db.session import get_db
from app.models.user import User
from app.models.generation_history import GenerationHistory

# Service contracts & DTOs
from app.services.i_lesson_plan_service import (
    ILessonPlanMlService,
    LessonPlanGenerateRequest,
    LessonPlanGenerateResponse,
)
from main import get_lesson_service

logger = logging.getLogger("LessonPlanController")

router = APIRouter(
    prefix="/api/v1/lessonplan",
    tags=["LessonPlan"]
)


# =====================================================================
# POST /api/v1/lessonplan/generate
# =====================================================================
@router.post(
    "/generate",
    response_model=LessonPlanGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generates a structured lesson plan and logs execution metrics in database."
)
async def generate_lesson_plan(
        request: LessonPlanGenerateRequest,
        user_id: Optional[UUID] = Query(default=None, alias="userId"),
        db: Session = Depends(get_db),
        ml_service: ILessonPlanMlService = Depends(get_lesson_service),
):
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query prompt cannot be empty."
        )

    try:
        # 1. Execute RAG generation & evaluation pipeline directly in Python
        ml_response = await ml_service.generate_lesson_plan_async(request)

        # 2. Persist Generation Metrics if userId is supplied
        if user_id:
            user_exists = db.scalar(
                select(User.id).where(User.id == user_id)
            ) is not None

            if user_exists:
                # Extract guardrail scores safely
                fact_check = getattr(ml_response, "fact_check_report", None)
                alignment = getattr(ml_response, "alignment_report", None)

                grounding_score = (
                    getattr(fact_check, "grounding_score", 0.0)
                    if fact_check else 0.0
                )
                alignment_score = (
                    getattr(alignment, "overall_alignment_score", 0.0)
                    if alignment else 0.0
                )

                history_log = GenerationHistory(
                    user_id=user_id,
                    query_prompt=request.query,
                    grounding_score=grounding_score,
                    alignment_score=alignment_score,
                    executed_at=datetime.now(timezone.utc)
                )

                db.add(history_log)
                db.commit()

        return ml_response

    except Exception as ex:
        db.rollback()
        logger.error(f"Unexpected error during lesson plan generation: {str(ex)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(ex)}"
        )


# =====================================================================
# POST /api/v1/lessonplan/generate-stream
# =====================================================================
@router.post(
    "/generate-stream",
    summary="Streams tokenized lesson plan output in real-time using Server-Sent Events (SSE)."
)
async def stream_lesson_plan(
        request_data: LessonPlanGenerateRequest,
        raw_request: Request,
        ml_service: ILessonPlanMlService = Depends(get_lesson_service),
):
    if not request_data.query or not request_data.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query prompt cannot be empty."
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Check if client disconnected before starting
            if await raw_request.is_disconnected():
                logger.info("Streaming request was cancelled by the client before execution.")
                return

            # Note: For non-streaming fallback models, we yield the complete serialized JSON chunk
            result = await ml_service.generate_lesson_plan_async(request_data)
            payload = result.model_dump_json() if hasattr(result, "model_dump_json") else json.dumps(result)

            yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as ex:
            logger.error(f"Error occurred during streaming lesson plan execution: {str(ex)}", exc_info=True)
            yield f"data: [ERROR] {str(ex)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )