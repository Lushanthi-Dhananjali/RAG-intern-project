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
    Enforces that all developmental steps mathematically sum to exactly 30 minutes in clean multiples of 5 (5, 10, 15, 20).
    """
    if not steps:
        return steps

    # If already exactly 30 mins and all steps are multiples of 5 (min 5), preserve LLM's dynamic allocation
    if sum(s.time_minutes for s in steps) == 30 and all(s.time_minutes % 5 == 0 and s.time_minutes >= 5 for s in steps):
        return steps

    logger.warning("Step timing drift or non-multiples of 5 detected. Re-balancing in 5-minute increments to exactly 30 mins...")

    # Round each step to nearest multiple of 5 (min 5 mins)
    for s in steps:
        s.time_minutes = max(5, int(round(s.time_minutes / 5.0) * 5))

    total = sum(s.time_minutes for s in steps)
    drift = 30 - total
    step_count = len(steps)

    if drift != 0:
        units = drift // 5
        direction = 5 if units > 0 else -5
        for _ in range(abs(units)):
            if direction < 0:
                candidates = [i for i, s in enumerate(steps) if s.time_minutes > 5]
                if candidates:
                    idx = max(candidates, key=lambda k: steps[k].time_minutes)
                    steps[idx].time_minutes += direction
                else:
                    break
            else:
                idx = min(range(step_count), key=lambda k: steps[k].time_minutes)
                steps[idx].time_minutes += direction

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
    textbook_context: str = "",
    progression_context: str = "",
) -> str:
    """
    Constructs a rigid, single-period prompt for Llama 3 enforcing the 5m-30m-5m LEARN blueprint.
    """
    logistics: GroupingLogisticsResult = GroupingLogisticsEngine.calculate_grouping(student_count)
    roles_str = ", ".join([f"{r.role_name} ({r.responsibility})" for r in logistics.roles_assigned])
    outcomes_formatted = "\n".join([f"- {o}" for o in period_outcomes]) if period_outcomes else "- Foundational civic concept exploration."
    resources_formatted = ", ".join(accessible_resources) if accessible_resources else "Standard blackboard, student notebooks"
    is_civic_education = subject.strip().casefold() == "civic education"
    step_assessment_rule = (
        "   - Do not include assessment_and_feedback in development steps; the only assessment belongs in Assessment & Closure."
        if is_civic_education
        else "   - Every step MUST include distinct: learning_teaching_method, learning_teaching_aids, teacher_activities, student_activities, and assessment_and_feedback."
    )

    strategy_directive = (
        f"CORE PEDAGOGICAL ACTIVITY DIRECTIVE:\n\"{chosen_strategy_description}\"\n"
        "- This teacher-selected activity is authoritative for this period. Do not replace it with another activity; structure the lesson steps, student roles, materials, and assessment around it.\n"
        if chosen_strategy_description
        else "CORE PEDAGOGICAL ACTIVITY DIRECTIVE: Interactive student-centered collaborative investigation."
    )

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert Sri Lankan Teacher Educator and Curriculum Specialist for the LEARN Practice Teaching Framework in Sri Lanka.
Your task is to assemble an innovative, highly engaging, student-centered single-period lesson plan for Period {current_period} of a {total_periods}-period sequence.

STRICT PEDAGOGICAL & 40-MINUTE STRUCTURAL LAWS:
1. Total Duration: EXACTLY 40 minutes (5m Entrance + 30m Development + 5m Closure/Assessment).
2. STUDENT-CENTERED PEDAGOGY (TEACHER AS FACILITATOR):
   - The teacher must NEVER deliver passive monologues or lengthy lectures.
   - The teacher's role is strictly that of a FACILITATOR: circulating among student groups, providing investigative task prompts, observing interactions, asking probing questions to scaffold learning, and moderating peer feedback.
   - Students are at the center: actively collaborating in small groups, conducting roleplays or investigations, exploring Sri Lankan real-world scenarios, presenting solutions, and evaluating peers without passive bystanders.
3. AUTHENTIC SRI LANKAN CONTEXT:
   - Ground all scenarios, investigations, roleplays, and discussions in real Sri Lankan situations (e.g., Sri Lankan school community, local government authorities like Pradeshiya Sabha / Urban Council / Municipal Council, Grama Niladhari, Sri Lankan multicultural society, environmental protection, and civic rights/duties).
4. DYNAMIC ALIGNMENT WITH CHOSEN ACTIVITY & ALLOCATED OUTCOMES:
   - The lesson development steps MUST directly embody the teacher-selected activity and address the specific NIE learning outcome(s) allocated for this period!
   - Do NOT output generic boilerplate. Explicitly name the concrete tasks, materials, role cards, inquiry questions, or case scenarios derived from the chosen activity and period outcomes.
5. The Entrance (time: exactly 5 minutes):
   - Active motivational hook linking student everyday experience in Sri Lanka to this period's topic and allocated outcomes, transitioning directly into the chosen activity.
6. Lesson Development Steps (CLEAN MULTIPLES OF 5, TOTAL = EXACTLY 30 MINUTES):
   - Every single step's 'time_minutes' MUST be a clean multiple of 5 (e.g. 5, 10, 15, 20). NEVER use non-multiples of 5 like 7, 8, 12, 13, 14, 17, 22!
   - Step count is typically 3 steps, but can be 2, 3, or 4 steps depending on what best suits the selected activity and learning outcome:
     * 3 Steps (Standard): e.g. 10m + 10m + 10m = 30m; OR 5m (Launch) + 15m (Active Simulation/Walk) + 10m (Synthesis) = 30m; OR 10m (Setup) + 15m (Inquiry) + 5m (Review) = 30m; OR 5m (Setup) + 20m (Extended Drama/Field Work) + 5m (Debrief) = 30m.
     * 2 Steps (Intensive): e.g. 10m (Orientation) + 20m (Roleplay/Debate) = 30m; OR 15m + 15m = 30m.
     * 4 Steps (Multi-Station): e.g. 5m + 10m + 10m + 5m = 30m.
   - The SUM of all development steps MUST strictly equal 30 minutes.
   - DYNAMIC ADAPTATION: Allocate time and step contents to fit the specific activity (e.g. a drama or school-walk needs a longer middle step like 15-20m; station jigsaw may use 10m/10m/10m).
{step_assessment_rule}
7. Creative In-Class Assignment & Formative Closure (time: exactly 5 minutes total):
   - Put a highly creative in-class closing check in 'post_activity' and 'summary' matching the selected activity and period outcomes.
   - Examples of creative checks: a 2-line rhyming verse/poem recitation, a rapid quiz or team mini-competition, a quick drawing/sketch challenge, a pass-the-parcel concept ball, or a statement display & vote.
   - Must be an in-class active check achievable in 5 minutes, NOT take-home homework.
8. Logistics ({student_count} Students):
   - Partition: {logistics.group_summary_label}.
   - Roles to embed: {roles_str}.
   - Use only the available aids listed below, adapt to the stated classroom setting, and ensure every student can participate within the 30-minute development phase.
9. ABSOLUTE PROHIBITION OF URLs AND EXTERNAL LINKS:
   - NEVER output URLs, website links, or http/https links anywhere in ANY field of the lesson plan.
   - 'competence' MUST be the broad curriculum competency standard in plain English text. Never output a URL or web link.
   - 'competence_level' MUST be strictly the curriculum code string "{competency_level}". Never output a URL or web link.

10. REQUIRED JSON SCHEMA KEYS - YOUR OUTPUT JSON MUST CONTAIN EXACTLY THESE FIELD NAMES (PROVIDING 3 DEVELOPMENT STEPS):
{{
  "grade": "{grade_level}",
  "subject": "{subject}",
  "time_allocation": "40 Minutes (Period {current_period} of {total_periods})",
  "competence": "Broad curriculum competency standard",
  "competence_level": "{competency_level}",
  "lesson": "{lesson_topic}",
  "the_entrance": "Detailed 5-minute introduction: teacher and student actions linking prior knowledge to this period topic and activity...",
  "lesson_development_steps": [
    {{
      "step_number": 1,
      "time_minutes": 10,
      "learning_teaching_method": "Task Orientation & Guided Inquiry Launch",
      "learning_teaching_aids": "Task assignment cards, role description sheets, inquiry scenario prompts",
      "teacher_activities": "Teacher introduces the Sri Lankan real-world scenario, explains group objectives, distributes task materials, and assigns student roles as a facilitator...",
      "student_activities": "Students arrange into cooperative groups, assign designated roles, review inquiry cards, and begin collaborative planning...",
      "assessment_and_feedback": ""
    }},
    {{
      "step_number": 2,
      "time_minutes": 10,
      "learning_teaching_method": "Active Student-Centered Investigation / Simulation / Drama / School-Walk",
      "learning_teaching_aids": "Worksheets, roleplay cue cards, chart papers, colored markers",
      "teacher_activities": "Teacher circulates as facilitator among groups, observes peer interactions, scaffolds challenging concepts with probing questions, and ensures active participation without lecturing...",
      "student_activities": "Students actively execute the chosen activity (e.g., conducting mock council session, exploratory school-walk survey, analyzing Sri Lankan community issues, or solving civic challenges in groups) using assigned roles...",
      "assessment_and_feedback": ""
    }},
    {{
      "step_number": 3,
      "time_minutes": 10,
      "learning_teaching_method": "Spokesperson Presentation & Plenary Synthesis",
      "learning_teaching_aids": "Student output posters, whiteboard, peer assessment checklist",
      "teacher_activities": "Teacher moderates student presentations, facilitates constructive peer review, and synthesizes key student discoveries directly against the period's learning outcomes...",
      "student_activities": "Spokespersons present group solutions or roleplay outcomes; class peers ask questions, provide constructive feedback, and summarize key takeaways in their notebooks...",
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
- Subject: {subject}
- Grade: {grade_level}
- Competency Level: {competency_level} (plain string code, never a URL)
- Lesson Title: {lesson_topic} (Period {current_period} of {total_periods})
- Use this period-specific curriculum topic; do not replace it with the broad competency title.
- Duration: 40 Minutes
- Classroom Setting: {classroom_environment}
- Available Aids: {resources_formatted}

TARGET VERBATIM LEARNING OUTCOMES FOR PERIOD {current_period}:
{outcomes_formatted}

INTERNAL SEQUENCE GUIDANCE FOR THIS PERIOD:
{progression_context or "Use the period position to introduce, develop, practise, and assess the allocated outcomes appropriately."}

{strategy_directive}

TIG & TEXTBOOK CONTEXT:
{retrieved_tig_context[:1800]}
{textbook_context[:1200]}

Assemble the final, validated LEARN lesson plan JSON now.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    return prompt