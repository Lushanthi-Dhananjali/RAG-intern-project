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
1. The Entrance (exactly 5 mins): State what the teacher and students do; connect prior knowledge or everyday Sri Lankan experience to this period's topic and the teacher's activity. Do not depend on unverified external links.
2. Lesson Development Steps (CLEAN MULTIPLES OF 5, TOTAL = EXACTLY 30 MINUTES):
   - Fully integrate the teacher's custom idea: "{teacher_custom_activity}".
   - Teacher acts strictly as FACILITATOR: circulating, scaffolding, asking probing questions, never lecturing.
   - Ground scenarios and tasks in authentic Sri Lankan context (schools, local governance, communities, cultural traditions).
   - Every step's duration MUST be a clean multiple of 5 (e.g. 5, 10, 15, 20 mins). Sum MUST equal exactly 30 minutes.
   - Step count typically 3 (e.g. 10m + 10m + 10m = 30m, or 5m + 15m + 10m = 30m, or 5m + 20m + 5m = 30m), but 2 or 4 steps matching the custom activity are also accepted.
3. Creative In-Class Assignment & Closure (exactly 5 mins total): Put a creative, age-appropriate in-class concluding task in 'post_activity' and 'summary' connecting directly to the period outcome and custom activity (e.g. quick 2-line rhyme, drawing challenge, mini-quiz, pass-the-parcel concept ball, or statement display). Must be achievable in 5 minutes in-class.
4. Align the Entrance and Assignment & Closure with the supplied competency outcomes and the teacher's custom activity. Generate usable classroom content, never placeholders or URLs.
5. The 'the_entrance' field must describe both teacher and student actions. The 'post_activity' field must describe the in-class five-minute task, not take-home homework.

CLASSROOM LOGISTICS & ROLES ({student_count} Students):
- Partition: {logistics.group_summary_label}.
- Assigned Student Roles: {roles_str}.
- Active engagement mandate: No passive spectators. Every student must execute their assigned role.

6. REQUIRED JSON FORMAT:
You MUST respond with a valid JSON object matching this schema.
CRITICAL ANTI-BOILERPLATE MANDATE:
- DO NOT output ellipsis ("...").
- DO NOT copy placeholder text or output generic descriptions like "(e.g., ...)".
- DO NOT output identical text across different periods or lesson plans.
- Seamlessly integrate the teacher's custom pedagogical concept: "{teacher_custom_activity}".
- Provide rich, concrete, creative details describing actual Sri Lankan classroom dialogues, specific task cards, specific physical artifacts, and dynamic student collaboration.
- Each development step must be detailed (3-5 sentences describing concrete student actions and teacher facilitation).
- The 'the_entrance' MUST be a creative 5-minute motivational hook connecting an authentic Sri Lankan situation to this specific period's outcome and the teacher's custom activity.
- The 'post_activity' MUST be a creative, highly engaging 5-minute active in-class evaluation (such as a 2-line rhyme/verse recitation, a rapid team quiz/competition, a quick concept drawing/sketch challenge, a pass-the-parcel concept ball, or a statement display & vote).

{{
  "grade": "{grade_level}",
  "subject": "Civic Education",
  "time_allocation": "40 Minutes (Period {current_period} of {total_periods})",
  "competence": "Broad curriculum competency standard in plain English",
  "competence_level": "Curriculum Standard",
  "lesson": "{lesson_topic}",
  "the_entrance": "<string: creative 5-minute motivational introduction specifically tailored to this period and the custom activity>",
  "lesson_development_steps": [
    {{
      "step_number": 1,
      "time_minutes": 10,
      "learning_teaching_method": "<string: pedagogical method for step 1, e.g. Task Orientation & Guided Inquiry Launch>",
      "learning_teaching_aids": "<string: specific physical materials and task cards for step 1>",
      "teacher_activities": "<string: detailed facilitator actions introducing the custom scenario and organizing student roles>",
      "student_activities": "<string: detailed active student actions starting the investigation for this period>",
      "assessment_and_feedback": ""
    }},
    {{
      "step_number": 2,
      "time_minutes": 10,
      "learning_teaching_method": "<string: method name reflecting the custom activity>",
      "learning_teaching_aids": "<string: specific materials, props, worksheets, or artifacts used in this activity>",
      "teacher_activities": "<string: detailed facilitator actions, guiding questions, and scaffolding during this custom activity>",
      "student_activities": "<string: detailed actions of students actively performing the custom activity in their teams>",
      "assessment_and_feedback": ""
    }},
    {{
      "step_number": 3,
      "time_minutes": 10,
      "learning_teaching_method": "<string: presentation, peer review and synthesis method name>",
      "learning_teaching_aids": "<string: presentation boards, whiteboard, checklist>",
      "teacher_activities": "<string: detailed teacher moderation of student team presentations and synthesis>",
      "student_activities": "<string: detailed student actions presenting group work and discussing peer feedback>",
      "assessment_and_feedback": ""
    }}
  ],
  "summary": "<string: 2-minute synthesis of core student discoveries on this period's outcomes>",
  "assessment_and_feedback_whole_lesson": "<string: formative feedback criteria for this lesson>",
  "post_activity": "<string: creative 5-minute in-class assessment: quiz, drawing, rhyme, or voting>"
}}

Respond ONLY with valid JSON conforming strictly to the above keys.<|eot_id|>
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