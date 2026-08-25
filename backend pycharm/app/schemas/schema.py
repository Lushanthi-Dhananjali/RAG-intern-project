# schema.py
from typing import List, Optional
from pydantic import BaseModel, Field


class LearningOutcome(BaseModel):
    id: int = Field(description="Outcome index starting at 1")
    description: str = Field(description="Measurable learning objective")
    blooms_taxonomy_level: Optional[str] = Field(default=None)


class MaterialItem(BaseModel):
    item_name: str = Field(description="Name of resource")
    quantity: str = Field(description="Amount needed")
    is_digital: bool = Field(default=False)


class ProcedureStep(BaseModel):
    step_number: int = Field(description="Sequence index")
    phase_title: str = Field(description="Warm-up, Direct Instruction, Group Activity, Closure")
    duration_minutes: int = Field(description="Time allocation in minutes")
    teacher_action: str = Field(description="Teacher action description")
    student_action: str = Field(description="Student action description")


class AssessmentAndVerification(BaseModel):
    formative_assessment: str = Field(description="In-class check during lesson")
    summative_assessment: Optional[str] = Field(default=None)
    alignment_check: str = Field(description="Verification of objective achievement")


class LessonPlanSchema(BaseModel):
    """
    MASTER SCHEMA: Fields must remain in this exact sequence to enforce
    Educational Goals -> Learning Outcomes -> Materials -> Procedures -> Verification.
    """
    title: str = Field(description="Title of the lesson plan")
    subject: str = Field(default="Civic Education", description="Academic subject")
    grade_level: str = Field(description="Target grade level")
    topic: str = Field(description="Specific unit/topic name")

    # 1. Educational Standard / Goal
    educational_goal_or_standard: str = Field(
        description="STEP 1: Educational Goal or Standard governing the lesson"
    )
    estimated_duration_minutes: int = Field(default=45)

    # 2. Measurable Objectives / Outcomes
    learning_outcomes: List[LearningOutcome] = Field(
        description="STEP 2: Measurable learning objectives derived directly from the goal"
    )

    # 3. Materials
    materials: List[MaterialItem] = Field(
        description="STEP 3: Required physical and digital instructional resources"
    )

    # 4. Sequential Procedures
    procedures: List[ProcedureStep] = Field(
        description="STEP 4: Sequential instructional steps executing the learning objectives"
    )

    # 5. Verification & Assessment
    verification: AssessmentAndVerification = Field(
        description="STEP 5: Assessment check verifying that procedures achieved the learning outcomes"
    )