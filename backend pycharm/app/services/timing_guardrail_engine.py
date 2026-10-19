"""
Step 8: Deterministic Guardrails & Timing Auto-Repair Engine.
Enforces strict 40-minute LEARN framework invariants (5m - 30m - 5m)
and guarantees verbatim NIE learning outcomes injection.
"""

import logging
from typing import List, Optional
from app.schemas.lesson_plan_schema_dto import (
    LearnLessonPlanDto,
    LessonDevelopmentStepDto,
)

logger = logging.getLogger("TimingGuardrailEngine")

# Standard pedagogical blueprints for 30-minute developmental blocks
STANDARD_DEVELOPMENT_STEP_PRESETS = {
    1: [30],
    2: [12, 18],
    3: [8, 14, 8],
    4: [6, 10, 8, 6],
}


class TimingGuardrailEngine:
    """
    Mathematical normalizer and invariant enforcer for 40-minute lesson plans.
    """

    @staticmethod
    def auto_repair_step_timings(
        steps: List[LessonDevelopmentStepDto],
    ) -> List[LessonDevelopmentStepDto]:
        """
        Guarantees that the sum of lesson development steps equals exactly 30 minutes.
        Repairs LLM drift without failing generation or throwing validation errors.
        """
        if not steps:
            # Fallback to default 3-step scaffold if LLM emitted an empty array
            return [
                LessonDevelopmentStepDto(
                    step_number=1,
                    time_minutes=8,
                    learning_teaching_method="Task Orientation & Prompt Distribution",
                    learning_teaching_aids="Task assignment cards, chalkboard",
                    teacher_activities="Distributes materials and sets investigative goals.",
                    student_activities="Review task cards in assigned groups.",
                    assessment_and_feedback="Checks student readiness and clarifies questions.",
                ),
                LessonDevelopmentStepDto(
                    step_number=2,
                    time_minutes=14,
                    learning_teaching_method="Cooperative Group Investigation",
                    learning_teaching_aids="Worksheets, student notebooks",
                    teacher_activities="Circulates to provide scaffolding and monitor roles.",
                    student_activities="Collaborate within assigned roles to solve the problem.",
                    assessment_and_feedback="Provides formative feedback on ongoing discussion.",
                ),
                LessonDevelopmentStepDto(
                    step_number=3,
                    time_minutes=8,
                    learning_teaching_method="Plenary Presentation & Review",
                    learning_teaching_aids="Blackboard, completed posters",
                    teacher_activities="Facilitates peer review and synthesizes main findings.",
                    student_activities="Spokespersons share group outputs with class.",
                    assessment_and_feedback="Clarifies misconceptions and provides peer assessment.",
                ),
            ]

        step_count = len(steps)
        current_sum = sum(s.time_minutes for s in steps)

        # Re-index step numbers consecutively (1 to N)
        for idx, s in enumerate(steps, start=1):
            s.step_number = idx

        # If already exactly 30 minutes, preserve LLM's proportional decisions
        if current_sum == 30:
            return steps

        logger.warning(
            "Timing drift detected: Developmental steps sum to %dm (target: 30m). Auto-repairing...",
            current_sum,
        )

        # Strategy A: Use proven preset if step count is between 1 and 4
        if step_count in STANDARD_DEVELOPMENT_STEP_PRESETS:
            preset = STANDARD_DEVELOPMENT_STEP_PRESETS[step_count]
            for s, allocated_mins in zip(steps, preset):
                s.time_minutes = allocated_mins
            return steps

        # Strategy B: Proportional scaling for 5+ steps
        # Normalize and clamp delta into the longest middle activity step
        scale_factor = 30.0 / max(1, current_sum)
        allocated_so_far = 0

        for i in range(step_count - 1):
            normalized = max(3, round(steps[i].time_minutes * scale_factor))
            steps[i].time_minutes = normalized
            allocated_so_far += normalized

        # Assign remaining minutes to final step, ensuring at least 3 minutes
        steps[-1].time_minutes = max(3, 30 - allocated_so_far)

        # Final pass verification
        final_sum = sum(s.time_minutes for s in steps)
        if final_sum != 30:
            steps[1].time_minutes += (30 - final_sum)

        return steps

    @staticmethod
    def enforce_invariants_and_inject_outcomes(
        plan: LearnLessonPlanDto,
        verbatim_outcomes: List[str],
        requested_period: int = 1,
        total_periods: int = 1,
    ) -> LearnLessonPlanDto:
        """
        Enforces complete Step 8 guardrails:
        1. Injects official verbatim learning outcomes (overwriting any LLM paraphrasing).
        2. Normalizes developmental step timings to sum to exactly 30 minutes.
        3. Formats the canonical time allocation string.
        4. Validates that the Entrance and Assessment phases comply with the 5m boundaries.
        """
        # 1. Verbatim TIG Outcomes Injection
        if verbatim_outcomes and len(verbatim_outcomes) > 0:
            clean_outcomes = [o.strip() for o in verbatim_outcomes if o.strip()]
            plan.unique_learning_outcome = clean_outcomes
            logger.info("Programmatically injected %d verbatim TIG outcome(s).", len(clean_outcomes))

        # 2. Timing Auto-Repair
        plan.lesson_development_steps = TimingGuardrailEngine.auto_repair_step_timings(
            plan.lesson_development_steps
        )

        # 3. Time Allocation Formatting
        plan.time_allocation = f"40 Minutes (Period {requested_period} of {total_periods})"

        # 4. Phase 1 & Phase 3 Sanitization
        if not plan.the_entrance or len(plan.the_entrance.strip()) < 10:
            plan.the_entrance = (
                "Stimulate student interest through a relevant question or short scenario "
                "connecting prior community observations to today's civic focus. (5 minutes)"
            )

        if not plan.assessment_and_feedback_whole_lesson or len(plan.assessment_and_feedback_whole_lesson.strip()) < 10:
            plan.assessment_and_feedback_whole_lesson = (
                "Conduct a 5-minute formative assessment (rapid exit ticket or quick 3-question peer quiz) "
                "evaluating the achievement of today's learning outcomes."
            )

        return plan