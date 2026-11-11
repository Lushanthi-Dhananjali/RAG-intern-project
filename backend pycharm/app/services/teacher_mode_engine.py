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

    assignment_styles = [
        "Rapid Team Quiz / Buzzer Board Challenge (2 fast conceptual dilemma questions on this period's Sri Lankan topic)",
        "Statement Display & Justified Standpoint Vote (display an authentic Sri Lankan societal statement on board; students vote Agree/Disagree and justify)",
        "Creative Rhyming Poem / 2-4 Line Verse Recitation (students in pairs compose or recite a short rhythm summarizing the core civic value or duty)",
        "Concept Drawing / Quick Sketch Challenge (students rapidly sketch a symbol, emblem, or flowchart mapping the solution to the Sri Lankan scenario)",
        "Pass-the-Parcel Concept Dilemma Ball (students pass a prompt ball with question cards; receivers solve short real-world dilemmas)",
    ]
    period_suggested_style = assignment_styles[(current_period - 1) % len(assignment_styles)]

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a Senior Pedagogical Scaffolding Specialist for the Sri Lankan NIE Civic Education Curriculum (Grades 6-9).
The teacher has provided their OWN custom pedagogical concept (Mode B).
Your job is NOT to replace their idea, but to scaffold it cleanly into the official 40-minute LEARN Kandy Practice Teaching Framework.

PEDAGOGICAL PACING MANDATE (Total: 40 Minutes):
1. The Entrance (exactly 5 mins): Ground dynamically in the retrieved NIE learning outcomes, the teacher's custom activity, textbook details, and Teacher Instructional Guide (TIG). Design an active motivational hook connecting student prior knowledge to launch the activity towards achieving the target learning outcomes. Detail both teacher challenge prompt and student active responses.
2. Lesson Development Steps (CLEAN MULTIPLES OF 5, TOTAL = EXACTLY 30 MINUTES):
   - Fully integrate the teacher's custom idea: "{teacher_custom_activity}".
   - Teacher acts strictly as FACILITATOR: circulating, scaffolding, asking probing questions, never lecturing.
   - Ground scenarios and tasks in authentic Sri Lankan context (schools, local governance, communities, cultural traditions).
   - Every step's duration MUST be a clean multiple of 5 (e.g. 5, 10, 15, 20 mins). Sum MUST equal exactly 30 minutes.
   - Determine step count (2, 3, or 4 steps) and duration of each step organically to suit the teacher's custom activity:
     * Examples: 15m + 15m = 30m, 5m + 15m + 10m = 30m, 10m + 15m + 5m = 30m, 5m + 20m + 5m = 30m, or 5m + 10m + 10m + 5m = 30m.
   - Do NOT default to a fixed 10+10+10 or fixed step structure across all lessons. Time allocation must reflect the actual depth of each step's tasks.
   - DYNAMIC STEP STRUCTURING:
     * Structure the sequence, pedagogical method names, and tasks organically around "{teacher_custom_activity}", the target learning outcomes, and the curriculum context.
     * Every step must detail student active participation and teacher facilitation.
   - STRICT ANTI-COPY MANDATE:
     * DO NOT copy, quote, or echo instruction sentences or headings into your JSON fields!
     * DO NOT repeat the same sentences across different steps!
     * In 'learning_teaching_method', name a meaningful pedagogical phase. NEVER output generic "Step 1", "Step 2" numbers!
     * In 'learning_teaching_aids', list specific concrete materials for EVERY step. NEVER leave this field empty ("")!
     * In 'assessment_and_feedback', keep it empty ("") as formative assessment is conducted at the bottom of the plan ('assessment_and_feedback_whole_lesson').
3. Creative In-Class Assignment & Closure ('post_activity', exactly 5 mins total):
   - Put a highly creative in-class closing evaluation check directly addressing '{lesson_topic}', the period outcomes, and the custom activity in an authentic Sri Lankan context (NOT take-home homework).
   - MULTI-PERIOD DIVERSITY & INNOVATION MANDATE:
     * Across a {total_periods}-period sequence, each period MUST feature a completely different assignment format (NEVER repeat the same type of assignment across periods!).
     * You have complete pedagogical freedom: you may use the suggested format for Period {current_period} ({period_suggested_style}), OR invent a BRAND NEW creative format (e.g., Mini Speed Debate, 60-Second Civic Pitch, Headline Writing, Case Verdict, Taboo Word Challenge, or your own original active learning check).
   - The formats below are pedagogical ideas only—DO NOT copy generic sentences! Generate a brand new, unique task tailored specifically to '{lesson_topic}':
     * Creative Rhyming Poem / Verses: Students compose or recite a short 2-4 line original rhyming verse summarizing the core concept, duty, or value of '{lesson_topic}'.
     * Rapid Team Quiz / Competition: Fast-paced buzzer or board challenge testing 2 specific conceptual questions from this period's Sri Lankan topic.
     * Concept Drawing / Quick Sketch Challenge: Students rapidly sketch a symbol, emblem, or diagram representing the core solution to the Sri Lankan scenario studied.
     * Pass-the-Parcel Concept Ball: Students pass a prompt ball with question cards; student holding it solves a short case dilemma on '{lesson_topic}'.
     * Statement Display & Vote: Teacher displays an agree/disagree civic statement relevant to Sri Lankan society on this topic; students vote and justify their stance.
   - Must be achievable in 5 minutes in-class.
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
- The 'the_entrance' MUST be an engaging 5-minute motivational hook grounded in the learning outcomes, the teacher's custom activity, textbook details, and Teacher Guide (TIG).
- The 'post_activity' MUST be a creative, highly engaging 5-minute active in-class evaluation (such as a 2-line rhyme/verse recitation, a rapid team quiz/competition, a quick concept drawing/sketch challenge, a pass-the-parcel concept ball, or a statement display & vote).

{{
  "grade": "{grade_level}",
  "subject": "Civic Education",
  "time_allocation": "40 Minutes (Period {current_period} of {total_periods})",
  "competence": "Broad curriculum competency standard in plain English",
  "competence_level": "Curriculum Standard",
  "lesson": "{lesson_topic}",
  "the_entrance": "<string: creative 5-minute motivational hook connecting learning outcomes, textbook, and TIG to launch the custom activity>",
  "lesson_development_steps": [
    {{
      "step_number": 1,
      "time_minutes": 15,
      "learning_teaching_method": "string (Specific pedagogical phase name organically matching this activity's first stage)",
      "learning_teaching_aids": "string (Specific physical classroom materials and task sheets used in this step)",
      "teacher_activities": "string (Detailed 2-4 sentences: teacher facilitation, inquiry prompts, and scaffolding questions)",
      "student_activities": "string (Detailed 2-4 sentences: active student collaboration, investigative tasks, and discussions)",
      "assessment_and_feedback": ""
    }},
    {{
      "step_number": 2,
      "time_minutes": 15,
      "learning_teaching_method": "string (Specific pedagogical phase name organically matching this activity's execution or presentation)",
      "learning_teaching_aids": "string (Specific physical artifacts, evidence cards, presentation charts, or whiteboard)",
      "teacher_activities": "string (Detailed 2-4 sentences: teacher observing, guiding, asking probing questions, or moderating)",
      "student_activities": "string (Detailed 2-4 sentences: active student debate, problem-solving, synthesis, or evaluation)",
      "assessment_and_feedback": ""
    }}
  ],
  "summary": "string (2-minute synthesis of core student discoveries on this period's outcomes)",
  "assessment_and_feedback_whole_lesson": "string (Formative feedback criteria for this lesson)",
  "post_activity": "string (Creative 5-minute active in-class evaluation check: rapid quiz, sketch challenge, rhyme, or voting)"
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