from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from schema import LessonPlanSchema
from evaluator_schema import FactCheckReport
from alignment_schema import AlignmentReport


# --- Request Schemas ---

class CurriculumExtractRequest(BaseModel):
    raw_text: str = Field(description="Unstructured curriculum text or raw lesson plan content")


class LessonPlanGenerateRequest(BaseModel):
    query: str = Field(description="User prompt or topic (e.g., 'Constitutional rights and duties')")
    grade_level: Optional[str] = Field(default="Grade 9", description="Target grade level")


class VerifyAlignmentRequest(BaseModel):
    educational_goal: str = Field(description="Target educational standard or goal text")
    lesson_objectives: List[str] = Field(description="List of generated lesson objectives to verify")


# --- Response Wrappers ---

class LessonPlanResponse(BaseModel):
    lesson_plan: LessonPlanSchema
    fact_check_report: Optional[FactCheckReport] = None
    alignment_report: Optional[AlignmentReport] = None