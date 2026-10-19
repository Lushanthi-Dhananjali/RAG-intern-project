"""
Subject & Grade Scope Guard for LEARN Practice Teaching Engine.
Isolates the new Creative, Student-Centred, Multi-Period pipeline strictly
to Civic Education (Grades 6-9) while safeguarding Science and other subjects.
"""

from typing import Tuple, Optional
import logging

logger = logging.getLogger("SubjectGuard")

# Strict allowable scope for the new creative pipeline
ALLOWED_SUBJECT = "civic education"
ALLOWED_GRADES = {"grade 6", "grade 7", "grade 8", "grade 9", "6", "7", "8", "9"}
MAX_CIVIC_PERIODS = 4


def normalize_grade(grade_str: str) -> str:
    """Normalizes variations like '8', 'Grade 8', 'grade 8' into standard 'Grade 8'."""
    clean = grade_str.strip().lower().replace("grade", "").strip()
    return f"Grade {clean}" if clean in {"6", "7", "8", "9"} else grade_str.strip()


def is_civic_creative_pipeline_enabled(subject: str, grade: str) -> bool:
    """
    Returns True ONLY if the subject is Civic Education and Grade is in [6, 7, 8, 9].
    Returns False for Science, English, Maths, or unsupported grades.
    """
    sub_clean = (subject or "").strip().lower()
    grd_clean = (grade or "").strip().lower()

    is_civic = sub_clean == ALLOWED_SUBJECT
    is_supported_grade = grd_clean in ALLOWED_GRADES

    enabled = is_civic and is_supported_grade

    if not enabled:
        logger.info(
            "Request [%s | %s] routed to LEGACY/DEFAULT pipeline (Creative pipeline disabled).",
            subject,
            grade
        )
    else:
        logger.info(
            "Request [%s | %s] validated for NEW CREATIVE CIVIC pipeline.",
            subject,
            grade
        )

    return enabled


def enforce_civic_period_boundary(periods: Optional[int]) -> Tuple[int, Optional[str]]:
    """
    Strict Rule: Each individual Competency Level can have a maximum of 4 periods (1 to 4).
    If requested periods > 4, clamps to 4 and provides a warning message.
    """
    raw_periods = periods or 1
    if raw_periods < 1:
        return 1, "Periods adjusted to minimum allowable (1 period)."
    if raw_periods > MAX_CIVIC_PERIODS:
        return (
            MAX_CIVIC_PERIODS,
            f"Civic Education competency levels have a strict maximum limit of 4 periods. Clamped from {raw_periods} to 4."
        )
    return raw_periods, None