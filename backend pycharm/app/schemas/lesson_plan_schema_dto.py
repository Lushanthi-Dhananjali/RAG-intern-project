from typing import List, Optional
import re
from pydantic import BaseModel, Field, model_validator


class LessonDevelopmentStepDto(BaseModel):
    step_number: int = Field(..., description="Step sequence number (1, 2, 3...)")
    teacher_activities: str = Field(..., description="Pedagogical actions executed by teacher based on TIG")
    student_activities: str = Field(..., description="Active learning tasks and investigations by students")
    learning_teaching_method: str = Field(..., description="Method used (e.g., Guided Inquiry, Cooperative Group Work)")
    learning_teaching_aids: str = Field(..., description="Concrete instructional materials for this step")
    assessment_and_feedback: str = Field(..., description="Formative checks, oral questions, or teacher feedback")
    time_minutes: int = Field(default=10, description="Step duration in minutes (aligned with 40 mins/period)")
    other: Optional[str] = Field(default="", description="Blackboard notes, grouping remarks")


class LessonPlanSchemaDto(BaseModel):
    grade: str = Field(..., description="Target school grade level (e.g., Grade 8)")
    subject: str = Field(default="Civic Education", description="Academic subject area")
    time_allocation: str = Field(..., description="e.g., '120 Minutes (3 Periods)', '160 Minutes (4 Periods)'")
    competence: str = Field(..., description="Main competency standard from syllabus")
    competence_level: str = Field(..., description="Competency level code and statement")
    lesson: str = Field(..., description="Lesson topic or unit theme")
    unique_learning_outcome: List[str] = Field(
        default_factory=list,
        description="All learning outcomes from TIG (programmatically populated)"
    )
    the_entrance: str = Field(..., description="Motivational introduction (5-10 mins)")
    lesson_development_steps: List[LessonDevelopmentStepDto] = Field(
        ...,
        description="Sequential development steps (Enforces periods + 1 steps)"
    )
    summary: str = Field(..., description="Synthesis of key concepts at conclusion")
    assessment_and_feedback_whole_lesson: str = Field(..., description="Summative evaluation check")
    post_activity: str = Field(..., description="Homework or field inquiry")
    information_sources: List[str] = Field(default_factory=list, description="Textbook and TIG references")
    attachments: List[str] = Field(default_factory=list, description="Worksheets or aids")

    @model_validator(mode="after")
    def validate_and_balance_dynamic_steps(self):
        # 1. Learning outcomes check relaxed to allow programmatic enrichment from TIG post-generation
        # (Outcomes are injected in service layer via extract_verbatim_tig_outcomes)

        # 2. Extract target minutes & determine minimum required steps (periods + 1)
        match = re.search(r"(\d+)\s*Minutes", self.time_allocation, re.IGNORECASE)
        target_minutes = int(match.group(1)) if match else 40

        # Formula: 1 Period (40m) -> 2 steps | 2 Periods (80m) -> 3 steps | 3 Periods (120m) -> 4 steps | 4 Periods (160m) -> 5 steps
        periods_count = max(1, round(target_minutes / 40))
        required_min_steps = periods_count + 1

        # 3. Auto-expand/split steps if LLM generated fewer than (periods + 1)
        # Prevents 422 HTTP crashes by dynamically fulfilling pedagogical requirements
        while len(self.lesson_development_steps) < required_min_steps:
            # Find the longest step to split
            longest_step_idx = max(
                range(len(self.lesson_development_steps)),
                key=lambda i: self.lesson_development_steps[i].time_minutes
            )
            longest_step = self.lesson_development_steps[longest_step_idx]

            orig_time = longest_step.time_minutes
            half_1 = max(5, (orig_time // 10) * 5)
            half_2 = max(5, orig_time - half_1)

            longest_step.time_minutes = half_1

            new_step = LessonDevelopmentStepDto(
                step_number=len(self.lesson_development_steps) + 1,
                teacher_activities=f"Facilitates student presentations and synthesis of findings from Step {longest_step.step_number}.",
                student_activities="Students present their findings, compare outcomes, and note teacher feedback.",
                learning_teaching_method="Presentation & Discussion",
                learning_teaching_aids=longest_step.learning_teaching_aids,
                assessment_and_feedback="Teacher checks clarity of student presentations and corrects misconceptions.",
                time_minutes=half_2,
                other="Presentation synthesis"
            )
            self.lesson_development_steps.insert(longest_step_idx + 1, new_step)

        # 4. Sequentially renumber steps (1, 2, 3, 4, 5...)
        for idx, step in enumerate(self.lesson_development_steps, start=1):
            step.step_number = idx

        # 5. Round all step durations to nearest multiple of 5 (minimum 5 minutes)
        for step in self.lesson_development_steps:
            raw_minutes = step.time_minutes
            rounded = round(raw_minutes / 5.0) * 5
            step.time_minutes = max(5, int(rounded))

        # 6. Balance remaining drift strictly in increments of 5 minutes
        total_time = sum(s.time_minutes for s in self.lesson_development_steps)
        drift = target_minutes - total_time

        if drift != 0 and self.lesson_development_steps:
            five_min_units = drift // 5
            step_count = len(self.lesson_development_steps)
            direction = 5 if five_min_units > 0 else -5

            for i in range(abs(five_min_units)):
                step_idx = i % step_count
                if direction < 0 and self.lesson_development_steps[step_idx].time_minutes <= 5:
                    continue
                self.lesson_development_steps[step_idx].time_minutes += direction

        return self


LearnLessonPlanDto = LessonPlanSchemaDto