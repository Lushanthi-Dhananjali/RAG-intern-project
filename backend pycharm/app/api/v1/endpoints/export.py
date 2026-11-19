import logging
import os
import re
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Body, Response

from app.services.export_service import generate_docx_stream, generate_pdf_stream
from app.services.generated_plans_manager import get_generated_plan

logger = logging.getLogger("ExportAPI")

router = APIRouter(tags=["Lesson Plan Export"])


def _make_safe_filename(plan_data: Dict[str, Any], ext: str) -> str:
    """Generates a clean, informative filename for downloads."""
    grade = plan_data.get("grade", "Grade_8")
    comp = plan_data.get("competence_level", "")
    p_num = plan_data.get("period_number")

    grade_clean = re.sub(r"[^\w]", "_", str(grade))
    comp_clean = re.sub(r"[^\w.]", "_", str(comp))

    parts = ["LessonPlan", grade_clean]
    if comp_clean:
        parts.append(f"comp_{comp_clean}")
    if p_num:
        parts.append(f"p{p_num}")

    base = "_".join(parts)
    return f"{base}.{ext.lstrip('.')}"


@router.post(
    "/docx",
    summary="Export lesson plan JSON to styled Word document (.docx)",
    response_description="Binary Microsoft Word document (.docx)"
)
async def export_plan_docx(payload: Dict[str, Any] = Body(...)):
    """
    Accepts full lesson plan JSON (single period or multi-period)
    and returns a professionally formatted Word document (.docx).
    """
    try:
        buffer = generate_docx_stream(payload)
        filename = _make_safe_filename(payload, "docx")
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as exc:
        logger.exception("Failed to export Word document: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Word document: {str(exc)}"
        )


@router.post(
    "/pdf",
    summary="Export lesson plan JSON to pixel-perfect PDF (.pdf)",
    response_description="Binary Adobe PDF document"
)
async def export_plan_pdf(payload: Dict[str, Any] = Body(...)):
    """
    Accepts full lesson plan JSON (single period or multi-period)
    and returns a pixel-perfect Adobe PDF file (.pdf).
    """
    try:
        buffer = generate_pdf_stream(payload)
        filename = _make_safe_filename(payload, "pdf")
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as exc:
        logger.exception("Failed to export PDF document: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF document: {str(exc)}"
        )


@router.get(
    "/saved/{filename}/docx",
    summary="Export a saved lesson plan by filename to Word document (.docx)"
)
async def export_saved_plan_docx(filename: str):
    """
    Retrieves the saved lesson plan JSON from generated_plans directory
    and returns a formatted Word document (.docx).
    """
    try:
        data = get_generated_plan(filename)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson plan '{filename}' not found."
            )
        buffer = generate_docx_stream(data)
        out_name = f"{os.path.splitext(filename)[0]}.docx"
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{out_name}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error exporting saved plan to docx: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export saved plan: {str(exc)}"
        )


@router.get(
    "/saved/{filename}/pdf",
    summary="Export a saved lesson plan by filename to PDF (.pdf)"
)
async def export_saved_plan_pdf(filename: str):
    """
    Retrieves the saved lesson plan JSON from generated_plans directory
    and returns a pixel-perfect Adobe PDF (.pdf).
    """
    try:
        data = get_generated_plan(filename)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson plan '{filename}' not found."
            )
        buffer = generate_pdf_stream(data)
        out_name = f"{os.path.splitext(filename)[0]}.pdf"
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{out_name}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error exporting saved plan to pdf: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export saved plan: {str(exc)}"
        )
