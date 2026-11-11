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

    assignment_styles = [
        "Rapid Team Quiz / Buzzer Board Challenge (2 fast conceptual dilemma questions on this period's Sri Lankan topic)",
        "Statement Display & Justified Standpoint Vote (display an authentic Sri Lankan societal statement on board; students vote Agree/Disagree and justify)",
        "Creative Rhyming Poem / 2-4 Line Verse Recitation (students in pairs compose or recite a short rhythm summarizing the core civic value or duty)",
        "Concept Drawing / Quick Sketch Challenge (students rapidly sketch a symbol, emblem, or flowchart mapping the solution to the Sri Lankan scenario)",
        "Pass-the-Parcel Concept Dilemma Ball (students pass a prompt ball with question cards; receivers solve short real-world dilemmas)",
    ]
    period_suggested_style = assignment_styles[(current_period - 1) % len(assignment_styles)]

    step_assessment_rule = (
        "   - Do NOT include assessment and feedback inside development steps (leave 'assessment_and_feedback': ''); "
        "the full lesson assessment belongs strictly in the final 5-minute section ('assessment_and_feedback_whole_lesson') at the bottom."
    )

    clean_act_desc = (chosen_strategy_description or "").strip()
    if clean_act_desc:
        lines = [line.strip() for line in clean_act_desc.splitlines() if line.strip()]
        filtered = [l for l in lines if not l.lower().startswith("standard class layout") and not l.lower().startswith("grouping:")]
        clean_act_desc = "\n".join(filtered) if filtered else clean_act_desc

    strategy_directive = (
        f"""MANDATORY ACTIVITY & DYNAMIC DEVELOPMENT STEPS INSTRUCTIONS:
SELECTED ACTIVITY FOR THIS LESSON:
{clean_act_desc}

CURRICULUM GROUNDING & REQUIREMENTS:
- Target Outcomes: Address these specific outcomes through active student work:
{outcomes_formatted}
- Lesson Topic: {lesson_topic}
- DYNAMIC ACTIVITY-BASED DEVELOPMENT STEP DESIGN:
  * Do NOT use a rigid or fixed step template. Create steps dynamically and organically based on the nature of the selected activity '{clean_act_desc}', the target outcomes, and the provided TIG and Textbook facts.
  * Different activities demand completely different structures and phases:
    - A debate, mock trial, or negotiation may have 2 deep phases (e.g. 10m preparation + 20m structured debate/rebuttal, or 15m + 15m).
    - An inquiry investigation, experiment, or case study may have 3 phases (e.g. 5m setup + 15m evidence gathering + 10m synthesis/defense).
    - A multi-station workshop, gallery walk, or jigsaw may have 3 or 4 phases (e.g. 5m + 10m + 10m + 5m).
  * Determine the step count (2, 3, or 4 steps) and duration of each step to best suit the activity.
  * Every step's 'time_minutes' MUST be a clean multiple of 5 (e.g. 5, 10, 15, 20) and the sum across all steps MUST strictly equal exactly 30 minutes. Do NOT default to a fixed time allocation across all lessons.
- STRICT ANTI-COPY MANDATE:
  * DO NOT copy, quote, or echo instruction sentences, headings, or activity summary paragraphs into your JSON fields!
  * DO NOT repeat the same sentences across different steps!
  * Write original, detailed classroom dialogue, teacher facilitation questions, and student collaborative tasks.
  * In 'learning_teaching_method', name a meaningful pedagogical phase derived from the activity (e.g. "Case Evidence Analysis", "Mock Assembly Deliberation", "Community Map Reconstruction"). NEVER output generic "Step 1", "Step 2" numbers!
  * In 'learning_teaching_aids', list specific concrete materials (sheets, task cards, chart paper, markers, whiteboard) for EVERY step. NEVER leave this field empty (\"\") or output "None"!
  * In 'assessment_and_feedback', leave it empty (\"\") as full assessment is in 'assessment_and_feedback_whole_lesson'."""
        if chosen_strategy_description
        else "MANDATORY DIRECTIVE: Generate rich, unique, student-centered collaborative investigation steps totaling exactly 30 minutes based on the curriculum and learning outcomes."
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
   - Ground dynamically in the retrieved NIE learning outcome(s), the selected activity, relevant textbook details, and Teacher Instructional Guide (TIG) guidelines.
   - Design an active motivational hook connecting student prior knowledge and enthusiasm to launch the chosen activity towards achieving the target learning outcomes.
   - Explicitly detail both teacher facilitation actions (launch prompt / challenge scenario) and student collaborative responses.
6. Lesson Development Steps (CLEAN MULTIPLES OF 5, TOTAL = EXACTLY 30 MINUTES):
   - Every single step's 'time_minutes' MUST be a clean multiple of 5 (e.g. 5, 10, 15, 20). NEVER use non-multiples of 5 like 7, 8, 12, 13, 14, 17, 22!
   - Determine the step count (2, 3, or 4 steps) and duration of each step organically to match the activity:
     * Valid configurations: 15m + 15m = 30m, 5m + 15m + 10m = 30m, 10m + 15m + 5m = 30m, 5m + 20m + 5m = 30m, 5m + 10m + 10m + 5m = 30m, etc.
   - Do NOT default to a fixed time or equal split on every lesson. Time allocation must reflect the actual depth of each step's tasks.
   - The total across all development steps must sum to exactly 30 minutes.
{step_assessment_rule}
7. Creative In-Class Assignment ('post_activity', time: exactly 5 minutes total):
   - Must be an original, highly engaging 5-minute active in-class evaluation check directly addressing '{lesson_topic}', the period's learning outcomes, and grounded in the authentic Sri Lankan context (NOT take-home homework).
   - MULTI-PERIOD DIVERSITY & INNOVATION MANDATE:
     * Across a {total_periods}-period sequence, each period MUST feature a completely different assignment format (NEVER repeat the same type of assignment across periods!).
     * You have complete pedagogical freedom: you may use the suggested format for Period {current_period} ({period_suggested_style}), OR invent a BRAND NEW creative format (e.g., Mini Speed Debate, 60-Second Civic Pitch, Headline Writing, Case Verdict, Taboo Word Challenge, or your own original active learning check).
   - The formats below are pedagogical inspiration only—DO NOT copy or hardcode generic sentences! Generate a brand new, unique task tailored specifically to '{lesson_topic}':
     * Creative Rhyming Poem / Verses: Students compose or recite a short 2-4 line original rhyming verse directly summarizing the core civic concept, duty, or value of '{lesson_topic}'.
     * Rapid Team Quiz / Competition: Fast-paced buzzer or board challenge testing 2 specific conceptual questions from this period's Sri Lankan topic.
     * Concept Drawing / Quick Sketch Challenge: Students rapidly sketch a symbol, emblem, or diagram representing the core solution to the Sri Lankan scenario studied.
     * Pass-the-Parcel Concept Ball: Students pass a prompt ball with question cards; student holding it solves a short scenario dilemma on '{lesson_topic}'.
     * Statement Display & Vote: Teacher displays an agree/disagree civic statement relevant to Sri Lankan society on this topic; students vote and justify their stance.
   - Describe the concrete prompt, student interaction, and teacher feedback for this 5-minute task.
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
- The 'the_entrance' MUST be an engaging 5-minute motivational hook grounded in the target learning outcomes, selected activity, textbook details, and Teacher Guide (TIG), detailing both teacher launch actions and student active responses.
- The 'post_activity' MUST be a creative, highly engaging 5-minute active in-class evaluation (creative poem/verse recitation, rapid quiz competition, concept drawing challenge, pass-the-parcel, or statement display & vote).

{{
  "grade": "{grade_level}",
  "subject": "{subject}",
  "time_allocation": "40 Minutes (Period {current_period} of {total_periods})",
  "competence": "Broad curriculum competency standard in plain English",
  "competence_level": "{competency_level}",
  "lesson": "{lesson_topic}",
  "the_entrance": "<string: creative 5-minute motivational hook connecting learning outcomes, textbook, and TIG to launch the activity, detailing teacher prompt and student responses>",
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
      "student_activities": "string (Detailed 2-4 sentences: active student debate, problem-solving, synthesis, or peer evaluation)",
      "assessment_and_feedback": ""
    }}
  ],
  "summary": "string (2-minute synthesis of core student discoveries on this period's outcomes)",
  "assessment_and_feedback_whole_lesson": "string (Formative feedback criteria for this lesson)",
  "post_activity": "string (Creative 5-minute active in-class evaluation check: rhyming poem/verse, rapid quiz competition, concept sketch challenge, pass-the-parcel, or statement display & vote)"
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