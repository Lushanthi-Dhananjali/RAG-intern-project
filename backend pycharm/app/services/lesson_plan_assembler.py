"""
Step 7: 40-Minute Lesson Plan Assembly Engine (Strict 5m - 30m - 5m Pacing).
Assembles a single-period LEARN Practice Teaching Lesson Plan tailored strictly
to the requested period's outcomes and selected/custom pedagogical strategy.
"""

import logging
from typing import List, Dict, Any, Optional
from app.schemas.lesson_plan_schema_dto import (
    LearnLessonPlanDto,
    LessonDevelopmentStepDto,
)
from app.services.grouping_logistics_engine import (
    GroupingLogisticsEngine,
    GroupingLogisticsResult,
)

logger = logging.getLogger("LessonPlanAssembler")


def balance_development_step_times(steps: List[LessonDevelopmentStepDto]) -> List[LessonDevelopmentStepDto]:
    """
    Enforces that all developmental steps mathematically sum to exactly 30 minutes.
    If the LLM drifts (e.g. 20m or 35m total), this normalizes and adjusts the middle step.
    """
    if not steps:
        return steps

    total = sum(step.time_minutes for step in steps)
    target = 30

    if total == target:
        return steps

    logger.warning("Step timing drift detected (Sum: %d mins). Re-balancing to exactly 30 mins...", total)

    if len(steps) == 2:
        # Standard 2-step breakdown: Step 1 (12 mins), Step 2 (18 mins)
        steps[0].time_minutes = 12
        steps[1].time_minutes = 18
    elif len(steps) == 3:
        # Standard 3-step breakdown: Step 1 (8 mins), Step 2 (14 mins), Step 3 (8 mins)
        steps[0].time_minutes = 8
        steps[1].time_minutes = 14
        steps[2].time_minutes = 8
    else:
        # Proportional adjustment
        diff = target - total
        steps[1].time_minutes = max(5, steps[1].time_minutes + diff)

    return steps


def build_single_period_assembly_prompt(
    competency_level: str,
    period_outcomes: List[str],
    current_period: int,
    total_periods: int,
    student_count: int,
    lesson_topic: str,
    grade_level: str,
    subject: str = "Civic Education",
    chosen_strategy_description: Optional[str] = None,
    classroom_environment: str = "Standard Classroom",
    accessible_resources: Optional[List[str]] = None,
    retrieved_tig_context: str = "",
    textbook_context: str = ""
) -> str:
    """
    Constructs a rigid, single-period prompt for Llama 3 enforcing the 5m-30m-5m LEARN blueprint.
    """
    logistics: GroupingLogisticsResult = GroupingLogisticsEngine.calculate_grouping(student_count)
    roles_str = ", ".join([f"{r.role_name} ({r.responsibility})" for r in logistics.roles_assigned])
    outcomes_formatted = "\n".join([f"- {o}" for o in period_outcomes]) if period_outcomes else "- Foundational civic concept exploration."
    resources_formatted = ", ".join(accessible_resources) if accessible_resources else "Standard blackboard, student notebooks"

    strategy_directive = (
        f"CORE PEDAGOGICAL ACTIVITY DIRECTIVE:\n\"{chosen_strategy_description}\"\n"
        if chosen_strategy_description
        else "CORE PEDAGOGICAL ACTIVITY DIRECTIVE: Interactive student-centered collaborative investigation."
    )

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert Teacher Educator and Curriculum Evaluator for the LEARN Practice Teaching Framework in Sri Lanka.
Your task is to assemble a complete, single-period lesson plan for Period {current_period} of a {total_periods}-period sequence.

STRICT 40-MINUTE LEARN KANDY STRUCTURAL LAWS:
1. Total Duration: EXACTLY 40 minutes.
2. The Entrance (time: exactly 5 minutes):
   - Hook the students with a stimulus question, short story, or real-life civic dilemma.
   - Link prior learning to Period {current_period}'s focus.
3. Lesson Development Steps (time: sum MUST equal exactly 30 minutes across 2 or 3 steps):
   - Step 1 (Setup/Inquiry Launch: 7-8 mins): Teacher delivers prompts/cue cards; students inspect tasks.
   - Step 2 (Group Investigation & Production: 14-15 mins): Active teamwork executing roles without bystanders.
   - Step 3 (Presentation & Cross-Review: 7-8 mins): Spokespersons present; peer feedback.
   - Every step MUST include distinct: learning_teaching_method, learning_teaching_aids, teacher_activities, student_activities, and assessment_and_feedback.
4. Summary & Whole Lesson Assessment (time: exactly 5 minutes):
   - 2-minute summary consolidating key concepts.
   - 3-minute active assessment directly verifying the allocated outcomes.
5. Logistics ({student_count} Students):
   - Partition: {logistics.group_summary_label}.
   - Roles to embed: {roles_str}.

Respond ONLY with valid JSON conforming to the LearnLessonPlanDto schema.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
LESSON METADATA:
- Subject: {subject}
- Grade: {grade_level}
- Competency Level: {competency_level}
- Lesson Title: {lesson_topic} (Period {current_period} of {total_periods})
- Duration: 40 Minutes
- Classroom Setting: {classroom_environment}
- Available Aids: {resources_formatted}

TARGET VERBATIM LEARNING OUTCOMES FOR PERIOD {current_period}:
{outcomes_formatted}

{strategy_directive}

TIG & TEXTBOOK CONTEXT:
{retrieved_tig_context[:1800]}
{textbook_context[:1200]}

Assemble the final, validated LEARN lesson plan JSON now.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    return prompt