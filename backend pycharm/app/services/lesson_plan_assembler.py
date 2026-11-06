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
    Preserves LLM dynamic auto-generated allocation whenever steps sum to 30 in clean multiples of 5
    (including 10+10+10, 5+15+10, 10+15+5, 15+15, 5+20+5, etc.).
    """
    if not steps:
        return steps

    # If already exactly 30 mins and all steps are multiples of 5 (min 5), preserve LLM auto-generated allocation
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
        "   - Do NOT include assessment and feedback inside development steps (leave 'assessment_and_feedback': ''); "
        "the full lesson assessment belongs strictly in the final 5-minute section ('assessment_and_feedback_whole_lesson') at the bottom."
    )

    strategy_directive = (
        f"""MANDATORY ACTIVITY, CURRICULUM GROUNDING & DYNAMIC DEVELOPMENT STEPS DIRECTIVE:
AUTHORITATIVE SELECTED ACTIVITY FOR THIS LESSON:
"{chosen_strategy_description}"

CRITICAL INSTRUCTIONS FOR GENERATING DYNAMIC DEVELOPMENT STEPS:
- You MUST generate unique, highly creative, student-centered development steps designed strictly around:
  * SPECIFIC SELECTED ACTIVITY: "{chosen_strategy_description}"
  * ALLOCATED LEARNING OUTCOMES FOR THIS PERIOD:
{outcomes_formatted}
  * LESSON TOPIC: "{lesson_topic}"
  * ACTUAL TIG & TEXTBOOK EVIDENCE: Extract and directly weave the specific definitions, civic concepts, real-life examples, discussion dilemmas, and factual points from the TIG & TEXTBOOK CONTEXT into the steps!

- DYNAMIC STEP COUNT & TIMING (STRICTLY 30 MINUTES TOTAL):
  * You may generate 2, 3, or 4 development steps depending on what best suits "{chosen_strategy_description}":
    - 2-Step intensive activity: e.g., 15m + 15m = 30m, or 10m + 20m = 30m.
    - 3-Step progressive inquiry: e.g., 10m + 10m + 10m = 30m, 5m + 15m + 10m = 30m, 10m + 15m + 5m = 30m, or 5m + 20m + 5m = 30m.
    - 4-Step multi-station / carousel: e.g., 5m + 10m + 10m + 5m = 30m.
  * Every single step's 'time_minutes' MUST be a clean multiple of 5 (e.g. 5, 10, 15, or 20).
  * The sum of 'time_minutes' across all development steps MUST equal EXACTLY 30 minutes.

- STUDENT-CENTERED PROGRESSIVE PEDAGOGY:
  * Step 1 (Inquiry Setup & Launch): Teacher introduces the specific real-world Sri Lankan dilemma for "{lesson_topic}", presents concrete inquiry task cards/materials derived from the textbook/TIG, and organizes student teams with assigned roles. Students examine the prompt, divide responsibilities, and formulate inquiry questions.
  * Middle Step(s) (Active Collaborative Deep-Dive / Simulation): Students actively execute "{chosen_strategy_description}" (debating, roleplaying, investigating textbook scenarios, mapping hazards, or constructing artifacts) in small groups without passive spectators. Teacher circulates as facilitator, asking probing questions to scaffold learning without lecturing.
  * Final Step (Spokesperson Sharing, Peer Critique & Synthesis): Group spokespersons present discoveries or co-created artifacts; peer teams evaluate using criteria and offer feedback; teacher synthesizes discoveries against the learning outcomes.

- ABSOLUTE PROHIBITION OF REPETITION & BOILERPLATE:
  * NEVER repeat the exact same sentences for 'teacher_activities' or 'student_activities' across multiple steps. Each step MUST describe unique, progressive actions!
  * In 'learning_teaching_method', name the specific sub-stage of this activity (e.g. "Dilemma Analysis & Role Distribution", "Team Rebuttal Round", "Consensus Resolution").
  * In 'learning_teaching_aids', list concrete physical items (e.g. hazard cards, dilemma briefs, role badges, observation grids, chart paper, markers). NEVER output "None" or "none"!
  * In 'teacher_activities' and 'student_activities', write 2 to 4 detailed sentences incorporating actual curriculum content and teacher facilitation questions.
  * In 'assessment_and_feedback', keep it empty ("") as the complete lesson assessment is located at the bottom of the plan ('assessment_and_feedback_whole_lesson')."""
        if chosen_strategy_description
        else "MANDATORY ACTIVITY & DYNAMIC DEVELOPMENT STEPS DIRECTIVE: Generate rich, unique, student-centered collaborative investigation steps."
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
3. AUTHENTIC SRI LANKAN CONTEXT & CURRICULUM GROUNDING:
   - Ground all scenarios, investigations, roleplays, and discussions in real Sri Lankan situations and the factual concepts from the provided textbook and Teacher Guide context.
4. DYNAMIC ALIGNMENT WITH CHOSEN ACTIVITY & ALLOCATED OUTCOMES:
   - The lesson development steps MUST directly embody the teacher-selected activity and address the specific NIE learning outcome(s) allocated for this period!
   - Do NOT output generic boilerplate. Explicitly name the concrete tasks, materials, role cards, inquiry questions, or case scenarios derived from the chosen activity and period outcomes.
5. The Entrance (time: exactly 5 minutes):
   - Active motivational hook linking student everyday experience in Sri Lanka to this period's topic and allocated outcomes, transitioning directly into the chosen activity.
6. Lesson Development Steps (CLEAN MULTIPLES OF 5, TOTAL = EXACTLY 30 MINUTES):
   - Every single step's 'time_minutes' MUST be a clean multiple of 5 (e.g. 5, 10, 15, 20). NEVER use non-multiples of 5 like 7, 8, 12, 13, 14, 17, 22!
   - Step count is flexible (2, 3, or 4 steps) depending on what best suits the selected activity and learning outcome:
     * Examples: 10m + 10m + 10m = 30m, 5m + 15m + 10m = 30m, 10m + 15m + 5m = 30m, 15m + 15m = 30m, 5m + 20m + 5m = 30m, or 5m + 10m + 10m + 5m = 30m.
   - The total across all development steps must sum to exactly 30 minutes.
{step_assessment_rule}
7. Creative In-Class Assignment & Formative Closure (time: exactly 5 minutes total):
   - Put a highly creative in-class closing check in 'post_activity' and 'summary' matching the selected activity and period outcomes.
   - Must be an in-class active check achievable in 5 minutes, NOT take-home homework.
8. Logistics ({student_count} Students):
   - Partition: {logistics.group_summary_label}.
   - Roles to embed: {roles_str}.
   - Use only the available aids listed below, adapt to the stated classroom setting, and ensure every student can participate within the 30-minute development phase.
9. ABSOLUTE PROHIBITION OF URLs AND EXTERNAL LINKS:
   - NEVER output URLs, website links, or http/https links anywhere in ANY field of the lesson plan.
   - 'competence' MUST be the broad curriculum competency standard in plain English text. Never output a URL or web link.
   - 'competence_level' MUST be strictly the curriculum code string "{competency_level}". Never output a URL or web link.

10. REQUIRED JSON FORMAT:
You MUST respond with a valid JSON object matching this schema.
CRITICAL ANTI-BOILERPLATE MANDATE:
- DO NOT output ellipsis ("...").
- DO NOT copy placeholder text or output generic descriptions like "(e.g., ...)".
- DO NOT output identical text across different periods or lesson plans.
- Provide rich, concrete, creative details describing actual Sri Lankan classroom dialogues, specific task cards, specific physical artifacts, and dynamic student collaboration.
- Each development step must be detailed (3-5 sentences describing concrete student actions and teacher facilitation).
- The 'the_entrance' MUST be a creative 5-minute motivational hook connecting an authentic Sri Lankan situation or everyday experience to this specific period's outcome and chosen activity.
- The 'post_activity' MUST be a creative, highly engaging 5-minute active in-class evaluation.

{{
  "grade": "{grade_level}",
  "subject": "{subject}",
  "time_allocation": "40 Minutes (Period {current_period} of {total_periods})",
  "competence": "Broad curriculum competency standard in plain English",
  "competence_level": "{competency_level}",
  "lesson": "{lesson_topic}",
  "the_entrance": "<string: creative 5-minute motivational introduction specifically tailored to this period and activity>",
  "lesson_development_steps": [
    {{
      "step_number": 1,
      "time_minutes": 10,
      "learning_teaching_method": "<string: specific launch and inquiry setup phase for this activity>",
      "learning_teaching_aids": "<string: concrete physical materials, prompt cards, and worksheets for this step (never 'None')>",
      "teacher_activities": "<string: 2-4 sentences describing exact teacher facilitator actions introducing this specific scenario, referencing curriculum concepts, and scaffolding role distribution>",
      "student_activities": "<string: 2-4 sentences describing active student teamwork reviewing scenario prompts, examining textbook evidence, and assigning group roles>",
      "assessment_and_feedback": ""
    }},
    {{
      "step_number": 2,
      "time_minutes": 10,
      "learning_teaching_method": "<string: specific collaborative execution/simulation phase of this activity>",
      "learning_teaching_aids": "<string: concrete artifacts, case materials, charts, or props used in this step (never 'None')>",
      "teacher_activities": "<string: 2-4 sentences describing teacher circulating, observing, and asking probing questions to deepen inquiry>",
      "student_activities": "<string: 2-4 sentences describing active student investigation, roleplay, debate, or mapping without passive spectators>",
      "assessment_and_feedback": ""
    }},
    {{
      "step_number": 3,
      "time_minutes": 10,
      "learning_teaching_method": "<string: specific presentation, peer review, and plenary synthesis phase>",
      "learning_teaching_aids": "<string: student-created presentation charts, whiteboard, feedback cards (never 'None')>",
      "teacher_activities": "<string: 2-4 sentences describing teacher moderating presentations, guiding peer evaluation, and reinforcing syllabus concepts>",
      "student_activities": "<string: 2-4 sentences describing team spokespersons presenting findings and peer students critiquing and recording takeaways>",
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
{retrieved_tig_context[:2500]}
{textbook_context[:2500]}

Assemble the final, validated LEARN lesson plan JSON now.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    return prompt