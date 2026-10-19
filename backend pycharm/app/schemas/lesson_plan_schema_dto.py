from typing import List, Optional
import re
from pydantic import BaseModel, Field, model_validator


class LessonDevelopmentStepDto(BaseModel):
    step_number: int = Field(..., description="Step sequence number (1, 2, 3...)")
    teacher_activities: str = Field(..., description="Teacher facilitation and scaffolding actions based on TIG")
    student_activities: str = Field(..., description="Active student investigations, discussions, and presentations")
    learning_teaching_method: str = Field(..., description="e.g., Guided Inquiry, Cooperative Group Work, Simulation, Jigsaw")
    learning_teaching_aids: str = Field(..., description="Instructional materials used in this step (task cards, sheets, board)")
    assessment_and_feedback: str = Field(..., description="Formative checks and immediate feedback during activity")
    time_minutes: int = Field(default=10, description="Step duration in minutes (5-minute multiples, sum must equal 30)")
    other: Optional[str] = Field(default="", description="Blackboard layout, grouping remarks, or safety notes")


class LessonPlanSchemaDto(BaseModel):
    grade: str = Field(..., description="Target school grade level (e.g., Grade 8)")
    subject: str = Field(default="Civic Education", description="Academic subject area")
    time_allocation: str = Field(..., description="e.g., '40 Minutes (Period 1 of 2)'")
    competence: str = Field(..., description="Broad competency statement from official TIG")
    competence_level: str = Field(..., description="Competency level code and statement (e.g., 8.1.1)")
    lesson: str = Field(..., description="Lesson title or theme")
    unique_learning_outcome: List[str] = Field(
        default_factory=list,
        description="Official syllabus outcomes assigned to this 40-minute period (programmatically injected)"
    )
    the_entrance: str = Field(
        ...,
        description="Motivational hook / introduction (Strictly 5 Minutes)"
    )
    lesson_development_steps: List[LessonDevelopmentStepDto] = Field(
        ...,
        description="Sequential development steps (Sum must strictly equal 30 Minutes)"
    )
    summary: str = Field(..., description="Consolidation and synthesis of key student findings")
    assessment_and_feedback_whole_lesson: str = Field(
        ...,
        description="Creative formative assessment (Strictly 5 Minutes: rhyming verse, freeze frame, sketch duel, pass-the-parcel)"
    )
    post_activity: str = Field(..., description="Follow-up reflection, observation, or homework task")
    information_sources: List[str] = Field(default_factory=list, description="Curriculum sources (NIE TIG, Pupil Textbook)")
    attachments: List[str] = Field(default_factory=list, description="Concrete titles of worksheets, cue cards, or checklists")

    @model_validator(mode="after")
    def balance_strict_40_minute_pacing(self):
        """
        Enforces the Strict LEARN Kandy 40-Minute Period Architecture:
        - Entrance: Exactly 5 mins
        - Development Steps: Exactly 30 mins (Sum across all development steps)
        - Creative Assessment: Exactly 5 mins
        - Total Period Duration: 5 + 30 + 5 = 40 Minutes.
        """
        TARGET_DEV_MINUTES = 30

        # 1. Fallback: If development steps are missing, initialize default scaffolded steps
        if not self.lesson_development_steps:
            self.lesson_development_steps = [
                LessonDevelopmentStepDto(
                    step_number=1,
                    teacher_activities="Teacher organizes students into structured inquiry teams and introduces the task scenario.",
                    student_activities="Students review task cards, assume collaborative group roles, and begin investigations.",
                    learning_teaching_method="Guided Inquiry",
                    learning_teaching_aids="Task Cards & Activity Prompts",
                    assessment_and_feedback="Teacher checks clarity of instructions and initial group comprehension.",
                    time_minutes=15,
                    other="Group formation"
                ),
                LessonDevelopmentStepDto(
                    step_number=2,
                    teacher_activities="Teacher moderates rapid student presentations, highlights key points, and addresses misconceptions.",
                    student_activities="Student spokespersons present team findings, compare observations, and note feedback.",
                    learning_teaching_method="Presentation & Discussion",
                    learning_teaching_aids="Whiteboard & Presentation Charts",
                    assessment_and_feedback="Formative peer feedback and teacher clarification of concepts.",
                    time_minutes=15,
                    other="Peer presentation"
                )
            ]

        # 2. If only 1 step was generated, split it to ensure at least 2 distinct developmental phases
        if len(self.lesson_development_steps) == 1:
            orig = self.lesson_development_steps[0]
            orig.time_minutes = 15
            self.lesson_development_steps.append(
                LessonDevelopmentStepDto(
                    step_number=2,
                    teacher_activities=f"Teacher facilitates student presentations and synthesis of findings from Step 1.",
                    student_activities="Students present their conclusions, compare outcomes with peers, and record feedback.",
                    learning_teaching_method="Presentation & Synthesis",
                    learning_teaching_aids=orig.learning_teaching_aids,
                    assessment_and_feedback="Teacher assesses clarity of student findings and reinforces core syllabus concepts.",
                    time_minutes=15,
                    other="Presentation synthesis"
                )
            )

        # 3. Round all individual step durations to the nearest multiple of 5 (minimum 5 mins)
        for step in self.lesson_development_steps:
            raw_val = step.time_minutes
            rounded = round(raw_val / 5.0) * 5
            step.time_minutes = max(5, int(rounded))

        # 4. Calculate drift relative to the strict 30-minute development ceiling
        current_sum = sum(s.time_minutes for s in self.lesson_development_steps)
        drift = TARGET_DEV_MINUTES - current_sum

        # 5. Deterministically balance drift strictly in 5-minute increments
        if drift != 0:
            units = drift // 5
            direction = 5 if units > 0 else -5
            step_count = len(self.lesson_development_steps)

            for _ in range(abs(units)):
                if direction < 0:
                    # Negative drift: trim the longest step that is greater than 5 minutes
                    candidates = [i for i, s in enumerate(self.lesson_development_steps) if s.time_minutes > 5]
                    if candidates:
                        idx = max(candidates, key=lambda k: self.lesson_development_steps[k].time_minutes)
                        self.lesson_development_steps[idx].time_minutes += direction
                    else:
                        break
                else:
                    # Positive drift: expand the shortest step
                    idx = min(range(step_count), key=lambda k: self.lesson_development_steps[k].time_minutes)
                    self.lesson_development_steps[idx].time_minutes += direction

        # 6. Sequentially renumber step indices (1, 2, 3...)
        for idx, step in enumerate(self.lesson_development_steps, start=1):
            step.step_number = idx

        return self


# Backward-compatibility alias
LearnLessonPlanDto = LessonPlanSchemaDto
PeradeniyaLessonPlanDto = LessonPlanSchemaDto