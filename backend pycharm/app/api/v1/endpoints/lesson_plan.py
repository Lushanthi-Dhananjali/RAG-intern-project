import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse

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
    summary="Generates a structured lesson plan using the RAG pipeline."
)
async def generate_lesson_plan(
        request: LessonPlanGenerateRequest,
        ml_service: ILessonPlanMlService = Depends(get_lesson_service),
):
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query prompt cannot be empty."
        )

    try:
        return await ml_service.generate_lesson_plan_async(request)

    except Exception as ex:
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