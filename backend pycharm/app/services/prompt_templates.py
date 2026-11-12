import json
import re
from typing import Optional, List, Dict, Any

# =====================================================================
# SYSTEM INSTRUCTION: LEARN KANDY PRACTICE TEACHING FORMAT
# =====================================================================
LEARN_PRACTICE_TEACHING_PROMPT = """You are an expert Sri Lankan School Teacher and Curriculum Specialist preparing a comprehensive lesson plan for Practice Teaching in Kandy (LEARN).

CRITICAL PEDAGOGICAL & GROUNDING DIRECTIVES:
1. STRICT 40-MINUTE PERIOD STRUCTURE:
- Every single lesson plan represents strictly 1 instructional period of exactly 40 minutes.
- Entrance / Motivational Introduction: Exactly 5 Minutes.
- Lesson Development: Exactly 30 Minutes distributed across sequential development steps.
- Closure & Creative Assessment: Exactly 5 Minutes.

2. STUDENT-CENTERED PEDAGOGY (TEACHER AS FACILITATOR):
- The teacher must NEVER deliver passive monologues.
- The teacher's role is strictly that of a facilitator, circulating among student groups, providing prompt cards, and managing time.
- Students lead the inquiry, perform investigations, conduct roleplays, and present discoveries.

3. DO NOT GENERATE LEARNING OUTCOMES:
- Do NOT generate, rewrite, or invent any learning outcomes in your output JSON.
- The official learning outcomes are already fixed by the NIE syllabus and handled programmatically.
- Use the provided official learning outcomes ONLY as an instructional reference to design matching teaching activities, steps, and assessments.

4. 5-MINUTE ROUND MULTIPLES & DYNAMIC TIME ALLOCATION:
- Every step's 'time_minutes' in 'lesson_development_steps' MUST be a clean multiple of 5 (e.g., 5, 10, 15, 20).
- NEVER output odd or irregular times like 7, 11, 13, 17, or 22 minutes.
- The total sum of 'time_minutes' across all development steps MUST strictly equal 30 minutes.
- Determine the step count (2, 3, or 4 steps) and duration dynamically to suit the actual depth of each step (e.g. 15m+15m, 5m+15m+10m, 10m+15m+5m, 5m+20m+5m, or 5m+10m+10m+5m). Do not force a fixed time or equal split on every lesson.

5. CREATIVE FORMATIVE IN-CLASS ASSIGNMENT & CLOSURE ('post_activity'):
- Must be an original, highly creative 5-minute active in-class evaluation directly matching this specific period's topic, learning outcomes, and grounded in the authentic Sri Lankan context (NOT take-home homework).
- Use the classic 5-minute assignment examples (quiz, pass-the-parcel, drawing, poem, display statement, small competition) whenever they fit the lesson well—freshly tailored to the topic—AND also invent brand-new creative interactive assignments and creative verses.
- NEVER lock any format to a period number, and NEVER repeat the same underlying activity mechanic across periods or recent plans; vary the interaction mode (oral/verse, visual/drawing, quiz/competition, movement/tactile, statement vote, or original new formats).

6. NO PLACEHOLDERS: Extract actual syllabus concepts, facts, and evaluation questions directly from the provided TIG and Textbook context.
7. ABSOLUTE PROHIBITION OF URLs AND WEB LINKS:
- NEVER output URLs, website links, or http/https links anywhere in any field of the lesson plan.
- All fields ('competence', 'competence_level', 'teacher_activities', 'student_activities', 'learning_teaching_method', 'learning_teaching_aids', etc.) MUST be written in clear instructional English or curriculum codes describing actual syllabus standards, classroom actions, physical aids, and pedagogical methods.
8. OUTPUT: Output ONLY a single, valid JSON object matching the requested schema without markdown code fences or conversational preambles.
"""

LEARN_5E_SYSTEM_PROMPT = LEARN_PRACTICE_TEACHING_PROMPT


def build_creative_assignment_directive(
    lesson_topic: str,
    previous_assignments: Optional[List[str]] = None,
) -> str:
    """
    Builds open-ended creative assignment instructions using existing formats strictly
    as inspiration while pushing the LLM to invent brand-new formats and creative verses.
    """
    prev_block = ""
    cleaned_prev = [p.strip() for p in (previous_assignments or []) if p and p.strip()]
    if cleaned_prev:
        items = "\n".join(f"     * {p[:180]}" for p in cleaned_prev[:4])
        prev_block = (
            "\n   - STRICT ANTI-REPETITION MANDATE — DO NOT REPEAT ANY OF THESE RECENT ASSIGNMENTS OR THEIR UNDERLYING MECHANIC:\n"
            f"{items}\n"
            "     You MUST choose a genuinely DIFFERENT interaction mode and activity mechanic from the ones above—"
            "never just change object or theme names while keeping the same mechanic!"
        )

    return (
        f"   - Must be an original, highly engaging 5-minute active in-class evaluation check directly addressing '{lesson_topic}', "
        "the period's learning outcomes, and grounded in the authentic Sri Lankan context (NOT take-home homework).\n"
        "   - BALANCED VARIETY & CREATIVE INNOVATION MANDATE:\n"
        "     * NEVER fix or assign any specific assignment type to a period number.\n"
        "     * You may freely choose and creatively adapt any of the classic 5-minute assignment examples "
        "(quiz, pass-the-parcel, drawing, poem, display statement, small competition) when it fits the lesson well, "
        "OR invent a BRAND-NEW, original 5-minute interactive assignment or creative verse/version uniquely tailored to "
        "this lesson's topic, learning outcomes, and chosen activity.\n"
        "     * Balance BOTH: do not rely solely on the 6 examples, and do not avoid them either—mix classic examples "
        "(freshly tailored to the topic) with brand-new creative formats across lessons.\n"
        "     * Prioritize true variety in student interaction mode (oral/verse, visual sketch, fast quiz/game, tactile/movement, "
        "statement debate, or a newly invented format)—do not repeat the same underlying mechanic across lessons."
        f"{prev_block}\n"
        "   - Describe the concrete prompt, active student interaction, and immediate teacher feedback achievable within 5 minutes."
    )


# =====================================================================
# 1. ACTIVITY OPTIONS GENERATOR PROMPT BUILDER
# =====================================================================
def build_activity_options_prompt(
    competency_level: str,
    grade: str,
    subject: str,
    topic: str,
    student_count: int,
    periods: int,
    tig_context: str
) -> str:
    """
    Constructs a lightweight prompt to generate 3 creative, diverse student-centered
    pedagogical activity options tailored to class size and Sri Lankan classroom reality.
    """
    return f"""You are an innovative Sri Lankan Master Teacher and Curriculum Expert in {subject}.
Based on the official NIE syllabus context below, suggest EXACTLY 3 distinct, highly creative, student-centered activity themes.

### CONSTRAINTS & CLASS DYNAMICS:
- Grade: {grade}
- Subject: {subject}
- Competency Level: {competency_level}
- Lesson Focus: {topic}
- Student Count: {student_count} students
- Time Available: {periods * 40} minutes ({periods} Period{'s' if periods > 1 else ''})

### CLASS SIZE ADAPTATION RULE:
- For class of {student_count} students, organize workable group logistics (e.g., small groups of 4-6, stations, or paired turns) so every single child is actively engaged without chaos.

### 3 DISTINCT STRATEGY TYPES REQUIRED:
- Option 1 (Performative / Drama / Simulation): e.g., Mock Parliament/Court, Roleplay of local councilors, consumer complaint drama.
- Option 2 (Exploratory / Inquiry / School-Walk): e.g., Campus observation, gathering real school waste/resources, interview school staff, investigative inquiry.
- Option 3 (Collaborative Station / Artifact & Jigsaw Analysis): e.g., Gallery walk, document analysis, poster jigsaw, board game or civic card challenge.

### OFFICIAL SYLLABUS CONTEXT:
{tig_context[:3000]}

### OUTPUT FORMAT:
Return strictly a valid JSON object matching this schema without markdown code blocks:
{{
  "options": [
    {{
      "id": "option_1",
      "title": "Creative Title for Drama/Simulation",
      "pedagogy_type": "Drama / Simulation",
      "description": "Clear step-by-step summary of the main student inquiry",
      "student_grouping": "Specific grouping structure for {student_count} students",
      "required_materials": ["Item 1", "Item 2"],
      "creative_assessment_preview": "5-minute closing check (e.g. quick freeze frame, verse, or card game)"
    }},
    {{
      "id": "option_2",
      "title": "Creative Title for School Inquiry/Walk",
      "pedagogy_type": "Inquiry / Field Investigation",
      "description": "Clear step-by-step summary of the activity",
      "student_grouping": "Specific grouping structure for {student_count} students",
      "required_materials": ["Clipboards/Sheets", "Observation Chart"],
      "creative_assessment_preview": "5-minute closing check"
    }},
    {{
      "id": "option_3",
      "title": "Creative Title for Jigsaw/Interactive Station",
      "pedagogy_type": "Jigsaw Cooperative Work",
      "description": "Clear step-by-step summary of the activity",
      "student_grouping": "Specific grouping structure for {student_count} students",
      "required_materials": ["Worksheets", "Chart Paper"],
      "creative_assessment_preview": "5-minute closing check"
    }}
  ]
}}
"""


# =====================================================================
# 2. 40-MINUTE STUDENT-CENTERED LESSON PLAN PROMPT BUILDER
# =====================================================================
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
    selected_activity_strategy: Optional[str] = None,
    student_count: int = 35,
    current_period: int = 1,
    total_periods: int = 1,
) -> str:
    """
    Constructs an authoritative prompt tailored to the Sri Lankan NIE curriculum
    and the LEARN Kandy Lesson Plan Structure.
    Enforces a strict 40-minute period breakdown (5m Intro, 30m Development, 5m Creative Assessment)
    and shapes steps around the chosen student-centered activity strategy.
    """
    subject_clean = subject.strip()
    grade_clean = grade.strip()
    is_science = "science" in subject_clean.lower()
    is_civic_education = subject_clean.casefold() == "civic education"

    # Time allocation for a single period plan
    time_allocation_label = f"40 Minutes (Period {current_period} of {total_periods})"


    # Format strategy directions
    if selected_activity_strategy and selected_activity_strategy.strip():
        strategy_directive = f"""### MANDATORY STUDENT-CENTERED PEDAGOGICAL STRATEGY:
{selected_activity_strategy.strip()}
- You MUST design the development steps strictly based on this selected activity theme.
- The classroom structure must accommodate {student_count} students dynamically."""
    else:
        strategy_directive = f"""### MANDATORY STUDENT-CENTERED PEDAGOGICAL STRATEGY:
Cooperative Student-Led Investigation with hands-on task cards and structured peer presentations suitable for {student_count} students."""

    # Dynamic Subject Pedagogy
    if is_science:
        pedagogy_guidelines = """- Pedagogy: 5E Inquiry Cycle (Engagement, Exploration, Explanation, Elaboration, Evaluation).
- Science Activities: Hands-on student experiments, apparatus handling, empirical observations, and hypothesis testing.
- Facilitation: Teacher guides questions; students manipulate materials, record observations, and present findings."""
    else:
        pedagogy_guidelines = """- Pedagogy: Student-centered inquiry, simulation, roleplay, field observation, or station work.
- Civic Activities: Democratic debate, institutional roleplay, case evaluation, mapping public amenities, and community problem solving.
- Facilitation: Teacher provides task cards and scaffolds; students debate, perform, analyze, and synthesize in groups."""

    # Format Official Outcomes for Reference
    if retrieved_outcomes and len(retrieved_outcomes) > 0:
        outcomes_ref_text = "\n".join([f"• {item}" for item in retrieved_outcomes])
    else:
        outcomes_ref_text = "Refer to the Learning Outcomes column in the TIG syllabus table."

    # LEARN Kandy JSON Schema Specification (Strict 5m - 30m - 5m)
    schema_spec = {
        "grade": grade_clean,
        "subject": subject_clean,
        "time_allocation": time_allocation_label,
        "competence": "string (The broad competency title from the TIG table)",
        "competence_level": f"{competency_level}",
        "lesson": f"{query} (Period {current_period})",
        "the_entrance": (
            "string (Motivational hook grounded in learning outcomes, textbook, and TIG to launch the activity. Duration: Exactly 5 Minutes)"
        ),
        "lesson_development_steps": [
            {
                "step_number": 1,
                "teacher_activities": "string (Detailed 2-4 sentences: teacher facilitator actions introducing the activity and guiding group inquiry)",
                "student_activities": f"string (Detailed 2-4 sentences: students collaborate in groups for {student_count} students, review tasks, and investigate)",
                "learning_teaching_method": "string (Specific pedagogical phase name organically matching this activity's first stage)",
                "learning_teaching_aids": "string (Specific physical task cards, problem scenarios, or charts - never 'None')",
                "assessment_and_feedback": "",
                "time_minutes": "integer (Auto-calculated multiple of 5 suited to this phase's depth, e.g. 5, 10, 15, or 20)",
                "other": "string (Group seating arrangement, resource distribution notes)",
            },
            {
                "step_number": 2,
                "teacher_activities": "string (Detailed 2-4 sentences: teacher circulating, asking probing questions, and scaffolding inquiry)",
                "student_activities": "string (Detailed 2-4 sentences: active student debate, problem-solving, synthesis, or presentation)",
                "learning_teaching_method": "string (Specific pedagogical phase name organically matching this activity's execution or synthesis stage)",
                "learning_teaching_aids": "string (Specific physical artifacts, evidence cards, presentation charts, or whiteboard - never 'None')",
                "assessment_and_feedback": "",
                "time_minutes": "integer (Auto-calculated multiple of 5 suited to this phase's depth; sum of all steps must equal 30 mins)",
                "other": "string (Differentiation for mixed abilities, timekeeping reminders)",
            },
        ],
        "summary": "string (Recap of key student discoveries and core concepts formulated during the lesson)",
        "assessment_and_feedback_whole_lesson": (
            "string (Generated 3-minute active assessment; the summary and assessment together complete the final 5-minute closure)"
            if is_civic_education
            else "string (Creative 5-minute active check—e.g. 2-line rhyming verse reciting core duties, rapid sketch review, freeze frame, or pass-the-parcel quiz)"
        ),
        "post_activity": "string (A genuinely fresh, creative 5-minute active in-class assignment uniquely invented for this topic and Sri Lankan context—inspired by existing creative ideas without copying rigid templates; never take-home homework)",
        "information_sources": [],
        "attachments": [
            "string (Concrete title of the activity sheet, roleplay cue cards, or observation checklist used)"
        ],
    }

    exemplar_section = (
        f"\n### EXEMPLAR REFERENCE STRUCTURE:\n{exemplar_context.strip()}\n"
        if exemplar_context.strip()
        else ""
    )

    prompt = f"""### SYSTEM PEDAGOGICAL INSTRUCTION:
{LEARN_PRACTICE_TEACHING_PROMPT}

### CONTEXT FROM TEACHER INSTRUCTIONAL GUIDE (TIG) & PUPIL'S TEXTBOOK:
{retrieved_context.strip() if retrieved_context.strip() else "Extract and generate strictly based on the Sri Lankan National Curriculum."}
{exemplar_section}
### LESSON PARAMETERS:
- Grade: {grade_clean}
- Subject: {subject_clean}
- Competency Level: {competency_level}
- Lesson Topic: {query}
- Allocation: {time_allocation_label} (Strictly 40 Minutes)
- Target Period: Period {current_period} of {total_periods}
- Class Size: {student_count} Students

{strategy_directive}

### OFFICIAL NIE LEARNING OUTCOMES FOR THIS PERIOD (REFERENCE ONLY):
{outcomes_ref_text}
(CRITICAL: DO NOT reproduce or output these learning outcomes in your JSON. Use them solely as guidance to structure the activity steps.)

### SUBJECT PEDAGOGY:
{pedagogy_guidelines}

### CRITICAL REQUIREMENTS:
1. 'grade': Must be "{grade_clean}".
2. 'subject': Must be "{subject_clean}".
3. 'competence': Extract the broad main competency standard from the TIG table.
4. 'competence_level': Must be set strictly to: "{competency_level}".
5. NO OUTCOMES FIELD: Strictly DO NOT generate 'unique_learning_outcome' in your JSON.
6. STRICT 40-MINUTE PACING RULES:
   - 'the_entrance': Must be an active motivational hook lasting EXACTLY 5 minutes, grounded dynamically in the retrieved learning outcomes, selected activity, textbook details, and Teacher Guide (TIG) to launch the activity, detailing teacher launch prompt and student responses.
   - 'lesson_development_steps': Must produce distinct student-centered steps (2, 3, or 4 steps) tailored to the activity.
     * Each step's 'time_minutes' must be a clean multiple of 5 (e.g. 5, 10, 15, 20).
     * The SUM of all development steps MUST EQUAL EXACTLY 30 MINUTES. Do not force fixed time splits.
   - 'assessment_and_feedback_whole_lesson': {"Must provide a generated 3-minute active evaluation; together with the 2-minute summary this completes the final 5-minute Assessment & Closure." if is_civic_education else "Must provide a creative, active evaluation lasting EXACTLY 5 minutes (e.g., 2-line rhyming verse reciting core duties, rapid sketch review, freeze frame tableau, pass-the-parcel quiz)."}
   - TOTAL PERIOD DURATION: 5m (Entrance) + 30m (Development) + 5m ({"Summary & Assessment Closure" if is_civic_education else "Assessment"}) = 40 MINUTES.
7. CLASS ADAPTATION: Explicitly detail group sizing and tasks tailored for {student_count} students.
8. Return ONLY a single valid JSON object. No Markdown code fences, no conversational preambles or notes.
9. Do not invent information_sources; the backend fills this field only from retrieved source metadata.
10. ABSOLUTE PROHIBITION OF URLs: NEVER output URLs or web links anywhere in ANY field (including 'competence' and 'competence_level'). Write concrete pedagogical classroom descriptions or curriculum codes only.
{"11. In 'assessment_and_feedback' inside development steps, keep it empty (\"\"). Full lesson assessment is strictly in 'assessment_and_feedback_whole_lesson'." if is_civic_education else ""}
{"12. For Civic Education, write the Entrance introduction and final Assessment & Closure from the supplied curriculum context and allocated outcomes. Return content only, never URLs or links." if is_civic_education else ""}

OUTPUT SCHEMA:
{json.dumps(schema_spec, indent=2)}

Valid JSON:"""

    return prompt