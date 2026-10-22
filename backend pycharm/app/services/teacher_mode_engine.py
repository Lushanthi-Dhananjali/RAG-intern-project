"""
Teacher's Own Approach Engine (Mode B) for Civic Education.
Adapts unstructured teacher inputs (custom ideas, video simulations, local scenarios)
into structured, curriculum-grounded LEARN lesson plans with strict 5m-30m-5m pacing.
"""

import logging
from typing import List, Dict, Any, Optional

from app.services.grouping_logistics_engine import (
    GroupingLogisticsEngine,
    GroupingLogisticsResult,
)

logger = logging.getLogger("TeacherModeEngine")


def build_mode_b_scaffolding_prompt(
    teacher_custom_activity: str,
    period_outcomes: List[str],
    current_period: int,
    total_periods: int,
    student_count: int,
    lesson_topic: str,
    grade_level: str,
    classroom_environment: str = "Standard Classroom",
    accessible_resources: Optional[List[str]] = None,
    progression_context: str = "",
) -> str:
    """
    Constructs an explicit prompt for local Llama 3 that honors the teacher's custom activity,
    binding it strictly to the period's official verbatim outcomes and class logistics.
    """
    logistics: GroupingLogisticsResult = GroupingLogisticsEngine.calculate_grouping(student_count)
    roles_str = ", ".join([f"{r.role_name} ({r.responsibility})" for r in logistics.roles_assigned])
    outcomes_formatted = "\n".join([f"- {o}" for o in period_outcomes]) if period_outcomes else "- Foundational civic concept exploration."
    resources_formatted = ", ".join(accessible_resources) if accessible_resources else "Standard classroom chalkboard, notebooks"

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a Senior Pedagogical Scaffolding Specialist for the Sri Lankan NIE Civic Education Curriculum (Grades 6-9).
The teacher has provided their OWN custom pedagogical concept (Mode B).
Your job is NOT to replace their idea, but to scaffold it cleanly into the official 40-minute LEARN Kandy Practice Teaching Framework.

PEDAGOGICAL PACING MANDATE (Total: 40 Minutes):
1. The Entrance (exactly 5 mins): State what the teacher and students do; connect prior knowledge or everyday experience to this period's topic and the teacher's activity. Do not depend on unverified external links.
2. Lesson Development Steps (30 mins across 2 or 3 structured steps):
   - Fully integrate the teacher's custom idea: "{teacher_custom_activity}".
   - Step 1: Orientation & Group Task Setup (5-7 mins).
   - Step 2: Active Student Collaboration / Production (15-18 mins) using the allocated group structure.
   - Step 3: Synthesis, Plenary Sharing & Cross-Review (7-10 mins).
3. Assignment & Closure (exactly 5 mins total): Put a specific, age-appropriate in-class assignment/concluding task in 'post_activity'. It must connect to this period's topic, allocated outcome, and custom activity, and be achievable in five minutes. The summary and assessment feedback are brief parts of this same five-minute phase, not extra time.
4. Align the Entrance and Assignment & Closure with the supplied competency outcomes and the teacher's custom activity. Generate usable classroom content, never placeholders or URLs.
5. The 'the_entrance' field must describe both teacher and student actions. The 'post_activity' field must describe the in-class five-minute task, not take-home homework.

CLASSROOM LOGISTICS & ROLES ({student_count} Students):
- Partition: {logistics.group_summary_label}.
- Assigned Student Roles: {roles_str}.
- Active engagement mandate: No passive spectators. Every student must execute their assigned role.

Respond ONLY with valid JSON conforming strictly to the LearnLessonPlanDto schema.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
LESSON METADATA:
- Subject: Civic Education
- Grade Level: {grade_level}
- Topic: {lesson_topic}
- Period: Period {current_period} of {total_periods} (40 Minutes)
- Setting: {classroom_environment}
- Available Aids: {resources_formatted}

OFFICIAL VERBATIM OUTCOMES TO ACHIEVE:
{outcomes_formatted}

INTERNAL SEQUENCE GUIDANCE FOR THIS PERIOD:
{progression_context or "Use the period position to introduce, develop, practise, and assess the allocated outcomes appropriately."}

TEACHER'S CUSTOM ACTIVITY SPECIFICATION (MODE B):
"{teacher_custom_activity}"

Generate the complete, validated LEARN lesson plan JSON now.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    return prompt