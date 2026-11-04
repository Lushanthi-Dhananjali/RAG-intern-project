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

6. REQUIRED JSON SCHEMA KEYS - YOUR OUTPUT JSON MUST CONTAIN EXACTLY THESE FIELD NAMES (PROVIDING 3 DEVELOPMENT STEPS):
{{
  "grade": "{grade_level}",
  "subject": "Civic Education",
  "time_allocation": "40 Minutes (Period {current_period} of {total_periods})",
  "competence": "Broad curriculum competency standard",
  "competence_level": "Curriculum Standard",
  "lesson": "{lesson_topic}",
  "the_entrance": "Detailed 5-minute introduction: teacher and student actions linking prior knowledge to this period topic and activity...",
  "lesson_development_steps": [
    {{
      "step_number": 1,
      "time_minutes": 10,
      "learning_teaching_method": "Task Orientation & Guided Inquiry Launch",
      "learning_teaching_aids": "Task cards, worksheets, role sheets",
      "teacher_activities": "Teacher introduces the custom scenario, outlines objectives, and assigns student roles as facilitator...",
      "student_activities": "Students arrange in cooperative groups, assume assigned roles, and analyze task prompts...",
      "assessment_and_feedback": ""
    }},
    {{
      "step_number": 2,
      "time_minutes": 10,
      "learning_teaching_method": "Active Student-Centered Execution / Simulation",
      "learning_teaching_aids": "Activity materials, props, chart papers, markers",
      "teacher_activities": "Teacher circulates among student groups, facilitates progress, scaffolds challenges, and monitors engagement...",
      "student_activities": "Students actively perform the custom activity in their teams, discussing, creating, and recording outputs...",
      "assessment_and_feedback": ""
    }},
    {{
      "step_number": 3,
      "time_minutes": 10,
      "learning_teaching_method": "Presentation, Peer Review & Plenary Synthesis",
      "learning_teaching_aids": "Presentation boards, whiteboard, checklist",
      "teacher_activities": "Teacher coordinates spokesperson presentations, moderates peer feedback, and consolidates findings...",
      "student_activities": "Spokespersons present group work; classmates question, provide constructive peer review, and note key ideas...",
      "assessment_and_feedback": ""
    }}
  ],
  "summary": "Consolidation and synthesis of key concepts...",
  "assessment_and_feedback_whole_lesson": "Final closure formative assessment criteria...",
  "post_activity": "Five-minute in-class assignment or concluding task..."
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