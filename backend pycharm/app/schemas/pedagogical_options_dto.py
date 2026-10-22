"""
Pedagogical Activity Options DTOs with Strict Clamping & Teacher Modes.
Enforces strict 1 <= periods <= 4 limits for Civic Education while maintaining
full backward compatibility with legacy frontend and API clients.
"""
from typing import List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator


class PedagogicalActivityOption(BaseModel):
    id: str = Field(..., description="Unique ID for option (e.g. 'option_1', 'option_2', 'option_3')")
    title: str = Field(..., description="Action-oriented student-centered title (e.g. 'Interactive Mock Council Debate')")
    pedagogy_type: str = Field(
        ...,
        description="Methodology (e.g. 'Roleplay / Drama', 'School-walk / Field Inquiry', 'Simulation & Mock Election', 'Station / Jigsaw')"
    )
    description: str = Field(..., description="Brief step-by-step overview of student inquiry and what students do")

    # Detailed Pedagogical Properties (Optional with defaults for backward compatibility)
    learning_outcomes_addressed: List[str] = Field(
        default_factory=list,
        description="Specific official learning outcomes addressed in this activity option"
    )
    student_action_summary: Optional[str] = Field(
        default="",
        description="Explicit breakdown of student investigation, teamwork, or creation steps"
    )
    teacher_facilitation_summary: Optional[str] = Field(
        default="",
        description="Teacher's facilitation, scaffolding prompts, cue card distribution, and timekeeping"
    )
    student_grouping: str = Field(
        ...,
        description="Logistical grouping adapted strictly to the student count (e.g. '6 groups of 6 students with assigned roles')"
    )
    required_materials: List[str] = Field(
        default_factory=list,
        description="Concrete, low-cost Sri Lankan classroom aids (e.g. ['Chart Paper', 'Scenario Prompt Cards', 'Observation Sheet'])"
    )
    approximate_duration_minutes: int = Field(
        default=30,
        description="Duration allocated for lesson development phase (strictly 30 minutes for a 40-minute period)"
    )
    expected_student_output: Optional[str] = Field(
        default="",
        description="Concrete evidence of learning produced (e.g. citizen bill of rights poster, roleplay presentation, completed matrix)"
    )
    creative_assessment_preview: str = Field(
        ...,
        description="Preview of a 5-minute active review (e.g. '2-line rhyming jingle', '1-minute freeze-frame tableau', 'rapid quiz')"
    )
    low_resource_alternative: Optional[str] = Field(
        default="",
        description="Practical fallback modification if electricity, printouts, or outdoor access are unavailable"
    )


class PedagogicalOptionsRequest(BaseModel):
    competency_level: str = Field(..., examples=["8.1.1"], description="Target NIE competency level code")
    grade_level: str = Field(default="Grade 8", examples=["Grade 8"], description="School grade level (Grades 6-9)")
    subject: str = Field(default="Civic Education", examples=["Civic Education"], description="Subject name")
    topic_query: Optional[str] = Field(
        default="",
        description="Optional lesson topic to guide activity discovery alongside retrieved curriculum outcomes"
    )
    student_count: int = Field(default=35, ge=5, le=80, description="Total number of students in the class")

    # Strict clamping: 1 <= periods <= 4
    periods: int = Field(
        default=1,
        description="Number of allocated 40-minute periods (strictly clamped between 1 and 4 for Civic Education)"
    )
    requested_period: Optional[int] = Field(
        default=1,
        description="The specific period number (1 to 4) for which options are currently being generated"
    )

    # Teacher Modes & Context
    teacher_mode: Literal["suggested", "own_approach"] = Field(
        default="suggested",
        description="Mode A ('suggested' for 3 diverse AI options) vs Mode B ('own_approach' for teacher custom activity)"
    )
    classroom_environment: Optional[str] = Field(
        default="Standard Classroom",
        description="Physical setting (e.g. 'Standard Classroom', 'School Grounds', 'School Hall')"
    )
    accessible_resources: Optional[List[str]] = Field(
        default_factory=list,
        description="List of resources explicitly available in the classroom"
    )
    previous_period_activities: Optional[List[str]] = Field(
        default_factory=list,
        description="List of activities already chosen in earlier periods to prevent accidental repetition"
    )

    @field_validator("periods", mode="before")
    @classmethod
    def clamp_civic_periods(cls, v: Any) -> int:
        """
        Enforces the project rule:
        Each individual Competency Level can have a maximum of 4 periods.
        Clamps values so 1 <= periods <= 4.
        """
        try:
            val = int(v) if v is not None else 1
        except (ValueError, TypeError):
            val = 1
        return max(1, min(val, 4))

    @field_validator("requested_period", mode="before")
    @classmethod
    def clamp_requested_period(cls, v: Any) -> int:
        """Ensures the requested period index stays strictly within the 1-4 boundary."""
        try:
            val = int(v) if v is not None else 1
        except (ValueError, TypeError):
            val = 1
        return max(1, min(val, 4))


class PedagogicalOptionsResponse(BaseModel):
    competency_level: str = Field(..., description="Target competency level code")
    lesson_topic: str = Field(..., description="Generated or extracted curriculum lesson focus")
    student_count: int = Field(..., description="Class size used to adapt group logistics")
    periods: int = Field(..., description="Total clamped period count (1 to 4)")
    requested_period: int = Field(default=1, description="Period number these options apply to")
    teacher_mode: str = Field(default="suggested", description="Interaction mode used during options generation")
    options: List[PedagogicalActivityOption] = Field(
        ...,
        description="List of 3 meaningfully diverse student-centered activity options"
    )