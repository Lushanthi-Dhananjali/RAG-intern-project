from typing import List, Optional
from pydantic import BaseModel, Field


class LessonStep(BaseModel):
    step_number: int = Field(
        ...,
        description="Step sequence number (1, 2, 3, etc.)"
    )
    learning_teaching_method: str = Field(
        ...,
        description="Pedagogical methodology used (e.g., Direct Instruction, Discussion, Inquiry, Group Activity)"
    )
    learning_teaching_aids: str = Field(
        ...,
        description="Aids and materials used in this step (e.g., Chalkboard, Flashcards, Textbook page 42)"
    )
    teacher_activities: str = Field(
        ...,
        description="Specific instructions and actions performed by the teacher"
    )
    student_activities: str = Field(
        ...,
        description="Specific tasks and actions performed by students"
    )
    assessment_and_feedback: str = Field(
        ...,
        description="Formative assessment method and immediate feedback mechanism for this step"
    )
    time_minutes: str = Field(
        ...,
        description="Allocated time duration for this specific step (e.g., '10 mins')"
    )
    other: Optional[str] = Field(
        default="",
        description="Additional teacher notes, classroom organization, or differentiation details"
    )


class LessonPlanSchema(BaseModel):
    page_no: str = Field(default="01", description="Page number of the lesson plan")
    lesson_plan_number: str = Field(default="01", description="Sequential lesson plan index")
    date: str = Field(..., description="Date of lesson delivery (YYYY-MM-DD)")
    grade: str = Field(..., description="Grade level (e.g., 'Grade 8')")
    subject: str = Field(..., description="Subject name (e.g., 'Civic Education')")
    time_allocation: str = Field(..., description="Total time allocation (e.g., '40 Minutes (1 Period)')")

    competence: str = Field(
        ...,
        description="Broad NIE curriculum competency statement"
    )
    competence_level: str = Field(
        ...,
        description="Specific 3-digit NIE competency level code and description (e.g., '8.1.1: Identifies direct democracy features')"
    )
    lesson_topic: str = Field(
        ...,
        description="Specific lesson title or sub-topic name"
    )

    unique_learning_outcome: List[str] = Field(
        ...,
        description="Specific measurable behavioral learning outcomes to achieve by end of lesson"
    )

    the_entrance: str = Field(
        ...,
        description="Introduction/Engagement phase (3-5 mins) to stimulate curiosity and activate prior knowledge"
    )

    lesson_development_steps: List[LessonStep] = Field(
        ...,
        description="7-column tabular development steps following University of Peradeniya format"
    )

    summary: str = Field(
        ...,
        description="Consolidation and recap of key concepts learned (3-5 mins)"
    )

    assessment_and_feedback_whole_lesson: str = Field(
        ...,
        description="Summative or closing formative assessment measuring overall lesson outcome achievement"
    )

    post_activity: str = Field(
        ...,
        description="Homework, extended learning activity, or community assignment"
    )

    information_sources: List[str] = Field(
        default_factory=lambda: ["Teacher Instructional Guide (TIG)", "Student Textbook"],
        description="Curriculum guides, reference textbooks, and external sources cited"
    )

    attachments: List[str] = Field(
        default_factory=list,
        description="List of attached resources, worksheets, charts, or rubrics"
    )

    reflection: str = Field(
        default="To be completed post-lesson delivery by the teacher.",
        description="Post-lesson evaluative notes on student achievement and pedagogical adjustments"
    )