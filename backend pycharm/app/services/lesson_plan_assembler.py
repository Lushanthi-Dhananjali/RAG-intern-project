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

    # If steps are uniform [10, 10, 10], diversify based on step depth and tasks
    if len(steps) == 3 and all(s.time_minutes == 10 for s in steps):
        steps = differentiate_step_timings_by_content(steps)
        if sum(s.time_minutes for s in steps) == 30:
            return steps

    # If already exactly 30 mins and all steps are multiples of 5 (min 5), preserve dynamic allocation
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
        f"""MANDATORY ACTIVITY & DYNAMIC DEVELOPMENT STEPS DIRECTIVE:
AUTHORITATIVE SELECTED ACTIVITY FOR THIS LESSON:
"{chosen_strategy_description}"

CRITICAL INSTRUCTIONS FOR GENERATING CREATIVE DEVELOPMENT STEPS:
- You MUST generate completely unique, imaginative, highly creative development steps designed strictly around:
  * SPECIFIC SELECTED ACTIVITY: "{chosen_strategy_description}"
  * ALLOCATED LEARNING OUTCOMES FOR THIS PERIOD:
{outcomes_formatted}
  * LESSON TOPIC: "{lesson_topic}"

- PROGRESSIVE MULTI-STAGE STEP BLUEPRINT:
  * Each step represents a distinct progressive phase of "{chosen_strategy_description}". DO NOT repeat the same tasks or phrases across steps!
  * Step 1 (Launch & Investigation Setup): Teacher introduces the specific real-world Sri Lankan dilemma or scenario for "{lesson_topic}", presents concrete inquiry task cards/materials, and assigns active group roles. Students examine the prompt, divide responsibilities, and formulate inquiry questions.
  * Step 2 (Active Collaborative Deep-Dive / Simulation): Students actively execute "{chosen_strategy_description}" (e.g., roleplaying civic stakeholders, auditing scenarios, debating propositions, or designing civic artifacts). Teacher circulates among teams, asking probing questions to scaffold learning without lecturing.
  * Step 3 (Spokesperson Sharing, Peer Critique & Plenary Consolidation): Group spokespersons present their civic findings or artifacts; peer teams evaluate using clear criteria and offer feedback; teacher synthesizes discoveries against the learning outcomes.
  * (If 4 steps are used, split the middle deep-dive into two distinct progressive sub-stages).

- ABSOLUTE PROHIBITION OF REPETITION & BOILERPLATE:
  * NEVER repeat the exact same sentences for 'teacher_activities' or 'student_activities' across multiple steps (e.g. NEVER repeat "Facilitates role execution" or "Students negotiate a solution" across steps 2, 3, 4). Each step MUST describe unique, specific actions!
  * NEVER use generic boilerplate titles like 'Task Orientation & Guided Inquiry Launch' or copy unrelated method names.
  * In 'learning_teaching_method', name the specific sub-stage of this activity (e.g., for a debate: "Dilemma Framing & Evidence Prep", "Cross-Team Rebuttal Session", "Consensus Resolution"; for a hazard walk: "Campus Hazard Inspection", "Risk Matrix Formulation", "Safety Charter Drafting").
  * In 'learning_teaching_aids', list specific, physical items (e.g. hazard cards, dilemma briefs, role badges, observation grids, chart paper, markers). NEVER output "None" or "none"!
  * In 'teacher_activities' and 'student_activities', write 2 to 4 detailed sentences with concrete Sri Lankan classroom dialogue, teacher scaffolding questions, and active student tasks.

- Dynamic Timing: Auto-generate 'time_minutes' as clean multiples of 5 (e.g. 5, 10, 15, or 20) totaling exactly 30 minutes across steps (such as 10m+10m+10m, 5m+15m+10m, 10m+15m+5m, 15m+15m, or 5m+20m+5m)."""
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
     * Examples: 10m + 10m + 10m, 5m + 15m + 10m, 10m + 15m + 5m, 15m + 15m, 5m + 20m + 5m, or 5m + 10m + 10m + 5m = 30m.
   - DYNAMIC TIMING AUTO-GENERATION:
     * Automatically generate and allocate 'time_minutes' to each development step to fit what students and the teacher actually do in that step.
     * Each step's duration must be a clean multiple of 5 (e.g. 5, 10, 15, or 20 minutes).
     * The total across all development steps must sum to exactly 30 minutes. (10+10+10 is completely acceptable when steps are balanced, as are 5+15+10, 10+15+5, 15+15, or 5+20+5).
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

10. REQUIRED JSON FORMAT:
You MUST respond with a valid JSON object matching this schema.
CRITICAL ANTI-BOILERPLATE MANDATE:
- DO NOT output ellipsis ("...").
- DO NOT copy placeholder text or output generic descriptions like "(e.g., ...)".
- DO NOT output identical text across different periods or lesson plans.
- Provide rich, concrete, creative details describing actual Sri Lankan classroom dialogues, specific task cards, specific physical artifacts, and dynamic student collaboration.
- Each development step must be detailed (3-5 sentences describing concrete student actions and teacher facilitation).
- The 'the_entrance' MUST be a creative 5-minute motivational hook connecting an authentic Sri Lankan situation or everyday experience to this specific period's outcome and chosen activity.
- The 'post_activity' MUST be a creative, highly engaging 5-minute active in-class evaluation (such as a 2-line rhyme/verse recitation, a rapid team quiz/competition, a quick concept drawing/sketch challenge, a pass-the-parcel concept ball, or a statement display & vote).

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
      "teacher_activities": "<string: 2-4 sentences describing exact teacher facilitator actions introducing this specific scenario and scaffolding role distribution>",
      "student_activities": "<string: 2-4 sentences describing active student teamwork reviewing scenario prompts and assigning group roles>",
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
{retrieved_tig_context[:1800]}
{textbook_context[:1200]}

Assemble the final, validated LEARN lesson plan JSON now.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    return prompt