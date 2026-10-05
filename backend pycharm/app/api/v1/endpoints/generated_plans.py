import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.generated_plans_manager import (
    list_generated_plans,
    get_generated_plan,
    delete_generated_plan,
    save_generated_plan,
    find_plan_by_competency,
)

logger = logging.getLogger("GeneratedPlansApi")

router = APIRouter(
    prefix="/api/v1/generated-plans",
    tags=["Generated Lesson Plans Storage"]
)


class SavePlanRequest(BaseModel):
    plan: Dict[str, Any] = Field(..., description="Full Peradeniya / NIE lesson plan JSON object")
    filename: Optional[str] = Field(default=None, description="Optional custom filename e.g. Grade_8_comp_8_1_1.json")


class DeletePlanResponse(BaseModel):
    success: bool
    message: str
    deleted_filename: str


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List all generated lesson plans with optional search and filters"
)
async def get_all_generated_plans(
    search: Optional[str] = Query(default=None, description="Keyword search in competence, topic, entrance, or filename"),
    grade: Optional[str] = Query(default=None, description="Filter by grade e.g. 'Grade 8'"),
    subject: Optional[str] = Query(default=None, description="Filter by subject e.g. 'Civic Education'"),
):
    """
    Returns list of summaries for all lesson plans stored in the generated_plans directory.
    """
    try:
        plans = list_generated_plans(search=search, grade=grade, subject=subject)
        return plans
    except Exception as exc:
        logger.exception("Error listing generated plans: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list generated lesson plans: {str(exc)}"
        )


@router.get(
    "/by-competency/{competency_level}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get generated lesson plan by competency level, grade, and subject"
)
async def get_plan_by_competency_endpoint(
    competency_level: str,
    grade: Optional[str] = Query(default=None),
    subject: Optional[str] = Query(default=None),
):
    """
    Looks up a saved generated plan for the given competency level, grade, and subject.
    """
    plan_info = find_plan_by_competency(
        competency_level=competency_level,
        grade=grade,
        subject=subject
    )
    if not plan_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No generated lesson plan found for Competency Level '{competency_level}'."
        )
    return plan_info


@router.get(
    "/{filename}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get full details and Peradeniya table JSON of a specific generated plan"
)
async def get_plan_by_filename(filename: str):
    """
    Fetches the complete lesson plan JSON structure for viewing or editing.
    """
    plan_info = get_generated_plan(filename)
    if not plan_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated lesson plan '{filename}' was not found in storage."
        )
    return plan_info


@router.delete(
    "/{filename}",
    response_model=DeletePlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a generated lesson plan permanently from storage"
)
async def delete_plan_by_filename(filename: str):
    """
    Deletes the specified lesson plan file from the generated_plans directory.
    """
    try:
        deleted = delete_generated_plan(filename)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson plan '{filename}' could not be found to delete."
            )
        return DeletePlanResponse(
            success=True,
            message=f"Lesson plan '{filename}' has been permanently deleted.",
            deleted_filename=filename
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to delete lesson plan '%s': %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lesson plan '{filename}': {str(exc)}"
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Save a generated lesson plan to storage"
)
async def save_plan(request: SavePlanRequest):
    """
    Saves a lesson plan to the generated_plans directory.
    """
    try:
        saved_filename = save_generated_plan(request.plan, request.filename)
        return {
            "success": True,
            "message": f"Lesson plan saved successfully as '{saved_filename}'.",
            "filename": saved_filename
        }
    except Exception as exc:
        logger.exception("Error saving plan: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save lesson plan: {str(exc)}"
        )
