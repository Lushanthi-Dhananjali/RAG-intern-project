from typing import Optional, Union
from pydantic import BaseModel, Field

# Imports for both the legacy C# DTO format and the native LEARN schema
try:
    from app.schemas.schema import LessonPlanSchema
except ModuleNotFoundError:
    LessonPlanSchema = dict

try:
    from app.schemas.lesson_plan_schema_dto import LessonPlanSchemaDto
except ModuleNotFoundError:
    LessonPlanSchemaDto = dict

from app.schemas.fact_check_report import FactCheckReportDto
from app.schemas.alignment_report import AlignmentReportDto


class LessonPlanGenerateRequest(BaseModel):
    query: str = Field(
        default="",
        description="The topic, concept, or educational objective prompt",
        examples=["Features of Direct Democracy in Ancient Athens"]
    )
    grade_level: str = Field(
        default="Grade 9",
        description="Target educational grade level",
        examples=["Grade 9"]
    )


class LessonPlanGenerateResponse(BaseModel):
    lesson_plan: Union[LessonPlanSchema, LessonPlanSchemaDto] = Field(
        default_factory=LessonPlanSchema,
        description="Generated LEARN-format or legacy structured lesson plan"
    )
    fact_check_report: Optional[FactCheckReportDto] = Field(
        default=None,
        description="Fact-checking and syllabus grounding verification report"
    )
    alignment_report: Optional[AlignmentReportDto] = Field(
        default=None,
        description="Pedagogical alignment evaluation report"
    )