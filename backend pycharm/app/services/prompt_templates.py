import json
import re
from typing import Optional

# =====================================================================
# SYSTEM INSTRUCTION: UNIVERSITY OF PERADENIYA PRACTICE TEACHING FORMAT
# =====================================================================
PERADENIYA_PRACTICE_TEACHING_PROMPT = """You are an expert Sri Lankan School Teacher and Curriculum Specialist preparing a comprehensive lesson plan for Practice Teaching at the University of Peradeniya.

CRITICAL PEDAGOGICAL & GROUNDING DIRECTIVES:
1. STRICT TIME ALLOCATION: You MUST use the exact total duration and period count requested (Standard: 1 Period = 40 Minutes).
2. DO NOT GENERATE LEARNING OUTCOMES:
   - Do NOT generate, rewrite, or invent any learning outcomes in your output JSON.
   - The official learning outcomes are already fixed by the NIE syllabus and handled programmatically.
   - Use the provided official learning outcomes ONLY as an instructional reference to design matching teaching activities, steps, and assessments.
3. DYNAMIC STEP BOUNDARIES:
   - For 1 Period (40 mins): Produce AT LEAST 2 distinct sequential steps.
   - For 2 Periods (80 mins): Produce AT LEAST 3 distinct sequential steps.
   - For 3 Periods (120 mins): Produce AT LEAST 4 distinct sequential steps.
   - For 4 Periods (160 mins): Produce AT LEAST 5 distinct sequential steps.
4. 5-MINUTE ROUND MULTIPLES ONLY:
   - Every single step's 'time_minutes' MUST be a clean multiple of 5 (e.g., 5, 10, 15, 20, 25, 30).
   - NEVER output odd or irregular times like 7, 11, 13, 17, or 22 minutes.
5. CONTEXT-BASED STEP PACING: Distribute 'time_minutes' dynamically across all steps based on cognitive complexity.
6. TOTAL TIME INTEGRITY: The sum of 'time_minutes' across all development steps must strictly equal the total allocated duration (40, 80, 120, or 160 minutes).
7. NO PLACEHOLDERS: Extract actual syllabus concepts, facts, and evaluation questions directly from the provided TIG and Textbook context.
8. OUTPUT: Output ONLY a single, valid JSON object matching the requested schema without markdown code fences or conversational preambles.
"""

PERADENIYA_5E_SYSTEM_PROMPT = PERADENIYA_PRACTICE_TEACHING_PROMPT


def build_lesson_plan_prompt(
    query: str,
    grade: str,
    subject: str,
    competency_level: str,
    periods: int = 1,
    duration_minutes: Optional[int] = None,
    retrieved_context: str = "",
    exemplar_context: str = "",
    retrieved_outcomes: Optional[list] = None,
) -> str:
    """Constructs an authoritative prompt tailored to the Sri Lankan NIE curriculum
    and the University of Peradeniya Lesson Plan Structure without generating outcomes.
    """
    subject_clean = subject.strip()
    grade_clean = grade.strip()
    is_science = "science" in subject_clean.lower()

    # 1. Enforce period boundaries (1 to 4) and 40 minutes per period
    if periods is not None and int(periods) > 0:
        safe_periods = min(max(int(periods), 1), 4)
        calculated_duration = safe_periods * 40
    elif duration_minutes is not None and int(duration_minutes) > 0:
        calculated_duration = int(duration_minutes)
        safe_periods = min(max(calculated_duration // 40, 1), 4)
    else:
        safe_periods = 1
        calculated_duration = 40

    time_allocation_label = f"{calculated_duration} Minutes ({safe_periods} {'Period' if safe_periods == 1 else 'Periods'})"

    # 2. Dynamic step minimum rule
    min_steps = safe_periods + 1
    step_rule = (
        f"For {calculated_duration} minutes ({safe_periods} periods), you MUST produce AT LEAST {min_steps} distinct sequential steps "
        f"in 'lesson_development_steps'. Each step's 'time_minutes' must be a multiple of 5, and the sum must equal exactly {calculated_duration} minutes."
    )

    # 3. Dynamic Subject Pedagogy
    if is_science:
        pedagogy_guidelines = """- Pedagogy: 5E Inquiry Cycle (Engagement, Exploration, Explanation, Elaboration, Evaluation).
- Science Activities: Hands-on experiments, scientific observations, laboratory apparatus handling, and safety measures.
- Student engagement: Formulating hypotheses, manipulating variables, recording empirical observations, and drawing conclusions."""
    else:
        pedagogy_guidelines = """- Pedagogy: Discussion, case studies, cooperative group work, and scenario-based roleplay.
- Civic Activities: Democratic participation, institutional awareness, legal and ethical discussions, and community problem-solving.
- Student engagement: Small-group analysis, collaborative debates, peer presentations, and applying civic duties."""

    # 4. Format Official Outcomes for Reference
    if retrieved_outcomes and len(retrieved_outcomes) > 0:
        outcomes_ref_text = "\n".join([f"• {item}" for item in retrieved_outcomes])
    else:
        outcomes_ref_text = "Refer to the Learning Outcomes column in the TIG syllabus table."

    # 5. University of Peradeniya JSON Schema Specification (WITHOUT unique_learning_outcome)
    schema_spec = {
        "grade": grade_clean,
        "subject": subject_clean,
        "time_allocation": time_allocation_label,
        "competence": "string (The broad competency title from the TIG table)",
        "competence_level": f"{competency_level}",
        "lesson": query,
        "the_entrance": (
            "string (Specific motivational hook linking real-world scenario or everyday phenomenon to this topic)"
        ),
        "lesson_development_steps": [
            {
                "step_number": 1,
                "teacher_activities": "string (Direct instructional actions, concept explanations, and guided questions aligned with the syllabus outcomes)",
                "student_activities": "string (Active student inquiries, notes, initial observations, or discussion responses)",
                "learning_teaching_method": "string (e.g., Guided Inquiry, Exposition)",
                "learning_teaching_aids": "string (Concrete teaching aids like textbook diagrams, charts, or lab specimens)",
                "assessment_and_feedback": "string (Formative assessment checks during this step)",
                "time_minutes": 15,
                "other": "string (Blackboard arrangement, safety precautions, or setup notes)",
            },
            {
                "step_number": 2,
                "teacher_activities": "string (Facilitating student practical group activities, experiments, or source analysis)",
                "student_activities": "string (Small group analysis, hands-on experiment, roleplay, or problem-solving tasks)",
                "learning_teaching_method": "string (e.g., Cooperative Group Work, Laboratory Investigation)",
                "learning_teaching_aids": "string (Worksheets, laboratory apparatus, task cards)",
                "assessment_and_feedback": "string (Monitoring group progress and correcting misconceptions)",
                "time_minutes": 30,
                "other": "string (Differentiation, group roles, or laboratory safety)",
            },
            {
                "step_number": 3,
                "teacher_activities": "string (Guiding student presentations, synthesizing findings, and clarifying core concepts)",
                "student_activities": "string (Presenting group outcomes, sharing recorded observations, and comparing notes)",
                "learning_teaching_method": "string (Student Presentations, Guided Discussion)",
                "learning_teaching_aids": "string (Presentation sheets, whiteboard)",
                "assessment_and_feedback": "string (Peer feedback and teacher clarification)",
                "time_minutes": 35,
                "other": "None",
            },
        ],
        "summary": "string (Recap of key findings, core scientific principles, or civic responsibilities)",
        "assessment_and_feedback_whole_lesson": "string (Summative check, exit questions, or evaluation rubric)",
        "post_activity": "string (Concrete homework, workbook exercise, or mini-investigation based on the textbook)",
        "information_sources": [
            "National Institute of Education (NIE) Teacher Instructional Guide",
            f"{grade_clean} Pupil's Textbook",
        ],
        "attachments": [
            "string (Concrete worksheet, laboratory activity sheet, or task card title created for this lesson)"
        ],
    }

    exemplar_section = (
        f"\n### EXEMPLAR REFERENCE STRUCTURE:\n{exemplar_context.strip()}\n"
        if exemplar_context.strip()
        else ""
    )

    prompt = f"""### SYSTEM PEDAGOGICAL INSTRUCTION:
{PERADENIYA_PRACTICE_TEACHING_PROMPT}

### CONTEXT FROM TEACHER INSTRUCTIONAL GUIDE (TIG) & PUPIL'S TEXTBOOK:
{retrieved_context.strip() if retrieved_context.strip() else "Extract and generate strictly based on the Sri Lankan National Curriculum."}
{exemplar_section}
### LESSON PARAMETERS:
- Grade: {grade_clean}
- Subject: {subject_clean}
- Competency Level: {competency_level}
- Lesson Topic: {query}
- Allocation: {time_allocation_label} ({calculated_duration} Minutes)

### OFFICIAL NIE LEARNING OUTCOMES (REFERENCE ONLY):
{outcomes_ref_text}
(CRITICAL: DO NOT reproduce or generate these outcomes in your JSON output. Use them solely as pedagogical guidance for designing the activities and development steps.)

### SUBJECT PEDAGOGY:
{pedagogy_guidelines}

### CRITICAL REQUIREMENTS:
1. 'grade': Must be "{grade_clean}".
2. 'subject': Must be "{subject_clean}".
3. 'competence': Extract the actual main competency title from the TIG table. NEVER write 'Competency Level {competency_level}' inside this field.
4. 'competence_level' MUST be set strictly to: "{competency_level}".
5. NO OUTCOMES FIELD: Strictly DO NOT include 'unique_learning_outcome' in your JSON.
6. STEP COUNT REQUIREMENT: {step_rule}
7. 5-MINUTE ROUND INTERVALS: Every single step's 'time_minutes' MUST be an integer multiple of 5 (e.g., 5, 10, 15, 20, 25, 30). NEVER output irregular minutes.
8. TOTAL DURATION CHECK: The sum of 'time_minutes' across all development steps MUST equal exactly {calculated_duration} minutes.
9. Return ONLY a single valid JSON object. No Markdown code fences, no conversational preambles or notes.

OUTPUT SCHEMA:
{json.dumps(schema_spec, indent=2)}

Valid JSON:"""

    return prompt