"""
Period-Aware Independent 3-Option Activity Generator Engine for Civic Education.
Implements strict anti-repetition filtering across periods using previous_period_activities.
Rotates pedagogy tracks (Simulation, Field Inquiry, Collaborative Jigsaw) without duplication
and integrates the Step 5 Grouping & Logistics Engine to eliminate passive bystanders.
"""

import hashlib
import json
import logging
import re
from typing import List, Dict, Any, Optional

from app.services.grouping_logistics_engine import (
    GroupingLogisticsEngine,
    GroupingLogisticsResult,
)

logger = logging.getLogger("ActivityOptionsEngine")

# Master Pedagogical Tracks and Sub-Methods
PEDAGOGICAL_TRACK_DEFINITIONS = {
    "Track 1 (Simulative & Roleplay)": [
        "Mock Local Council / Pradeshiya Sabha Session",
        "Courtroom / Citizen Grievance Tribunal",
        "Citizen-Officer Deliberation Roleplay",
        "1-Minute Frozen Tableau Drama",
    ],
    "Track 2 (Empirical & Investigative Inquiry)": [
        "School-Ground Walk & Facility Audit",
        "Public Service Case Study & Dilemma Cards",
        "Community Observation Checklist & Mapping",
        "Institutional Fact-Finding Station",
    ],
    "Track 3 (Collaborative Design & Problem-Solving)": [
        "Station Jigsaw Synthesis Matrix",
        "Citizen Charter / Wall Newspaper Poster",
        "Consensus Problem-Solving Carousel",
        "Public Issue Tree / Cause-Effect Diagram",
    ],
}


def detect_used_pedagogical_tracks(previous_activities: List[str]) -> List[str]:
    """
    Analyzes strings in previous_period_activities to identify used pedagogies
    (e.g., drama, simulation, walk, interview, jigsaw, matrix).
    """
    used_tracks = set()
    text = " ".join(previous_activities).lower()

    if any(k in text for k in ["roleplay", "drama", "simulation", "mock", "court", "council", "parliament"]):
        used_tracks.add("Simulative & Roleplay")
    if any(k in text for k in ["walk", "field", "inquiry", "investigat", "case study", "dilemma", "audit", "observ"]):
        used_tracks.add("Empirical & Investigative Inquiry")
    if any(k in text for k in ["jigsaw", "station", "carousel", "charter", "infographic", "matrix", "poster"]):
        used_tracks.add("Collaborative Design & Problem-Solving")

    return list(used_tracks)


def build_period_options_prompt(
    competency_level: str,
    period_outcomes: List[str],
    current_period: int,
    total_periods: int,
    student_count: int,
    lesson_topic: str,
    grade_level: str,
    classroom_environment: str = "Standard Classroom",
    accessible_resources: Optional[List[str]] = None,
    previous_activities: Optional[List[str]] = None,
    progression_context: str = "",
) -> str:
    """
    Constructs a rigid, student-centred prompt for Llama 3 forcing exactly
    3 distinct activity options aligned strictly to the requested period's outcomes
    while enforcing negative constraints against previously used methodologies and
    injecting Step 5 grouping logistics.
    """
    outcomes_formatted = (
        "\n".join([f"- {o}" for o in period_outcomes])
        if period_outcomes
        else "- Master foundational civic concepts of this competency level."
    )
    resources_formatted = (
        ", ".join(accessible_resources)
        if accessible_resources
        else "Standard blackboard, paper, student notebooks"
    )

    prev_acts = previous_activities or []
    used_tracks = detect_used_pedagogical_tracks(prev_acts)

    # Step 5: Algorithmic Grouping & Logistics Resolution
    logistics: GroupingLogisticsResult = GroupingLogisticsEngine.calculate_grouping(student_count)
    role_names_str = ", ".join([r.role_name for r in logistics.roles_assigned])

    anti_repetition_prompt = ""
    if prev_acts:
        avoid_items = ", ".join([f"'{a}'" for a in prev_acts])
        detected_tracks_str = ", ".join(used_tracks) if used_tracks else "General lecture / prior tasks"
        anti_repetition_prompt = f"""
CRITICAL ANTI-REPETITION MANDATE (PERIOD CONTINUITY GUARD):
1. The teacher has ALREADY conducted these activities in earlier periods: [{avoid_items}].
2. Detected Previous Pedagogies: [{detected_tracks_str}].
3. STRICT PROHIBITION: DO NOT duplicate, re-run, or lightly rename the above methods.
4. If Period 1 used 'Roleplay/Mock Council', Period {current_period} MUST pivot to an empirical method (like a Case Audit or School Walk) or a cooperative synthesis (like Station Jigsaw).
"""

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert curriculum designer and pedagogical consultant for the Sri Lankan National Institute of Education (NIE) Civic Education Curriculum (Grades 6-9).
Your mission is to generate exactly THREE (3) meaningfully distinct student-centred activity cards for Period {current_period} of a {total_periods}-period competency sequence.

STRICT PEDAGOGICAL REQUIREMENTS:
1. Target Outcomes: Address ONLY the outcomes allocated to Period {current_period}. Do not skip ahead or incorporate outcomes meant for other periods.
2. Competency-Specific Activities: Design every option specifically for Competency Level {competency_level} and its target outcomes below. Do not generate a generic activity set that could be reused for another competency level.
3. Cross-Level Uniqueness: For the same period, these activities must be different from activities generated for every other competency level. Do not reuse an activity's scenario, student task, teaching approach, or expected output across competency levels; make the differences substantive, not just wording changes.
4. Period-Specific Design: Make each activity specific to Period {current_period}, its allocated outcomes, and the stated learning progression. Do not copy a period's activities to another period.
5. Distinct Pedagogical Tracks: Use three different, outcome-relevant approaches chosen from methods such as simulation, roleplay, observation, case inquiry, evidence analysis, jigsaw, problem-solving, debate, creative design, or presentation. Select methods appropriate to these specific outcomes rather than assigning the same three methods to every competency level.
6. Student-Centred Facilitation: Students actively investigate, discuss, and create; the teacher acts strictly as a facilitator, timekeeper, and prompt guide.
7. Step 5 Grouping & Logistics Mandate:
   - Partition Scheme: {logistics.group_summary_label}.
   - Roles to Distribute: {role_names_str}.
   - Management Guidance: {logistics.pedagogy_adaptation}.
   - Zero bystanders: Every student must have one of the designated roles above.
   - State how all {student_count} students participate, how the teacher supervises the groups, and how the activity fits the 30-minute development period.
   - Use only these available resources: {resources_formatted}. Do not require unavailable equipment, printing, or off-site access; provide a feasible adaptation for {classroom_environment}.
8. 5-Minute Assessment Preview: Include a creative, active 5-minute learning check (e.g., tableau, rhyme, exit slip, pass-the-parcel quiz).
9. Period {current_period} outcomes for Competency Level {competency_level}:
{outcomes_formatted}
{anti_repetition_prompt}

Respond ONLY with valid JSON matching this schema:
{{
  "topic": "{lesson_topic}",
  "period": {current_period},
  "options": [
    {{
      "id": "option_1",
      "title": "<Action-oriented active title>",
      "pedagogy_type": "<e.g. Simulation / Roleplay>",
      "description": "<Concise 2-3 sentence overview of the student inquiry>",
      "student_action_summary": "<What students physically investigate, discuss, or produce>",
      "teacher_facilitation_summary": "<Guiding questions, scaffolding prompts, and timekeeping>",
      "student_grouping": "<Strictly follow: {logistics.group_summary_label} with assigned roles: {role_names_str}>",
      "required_materials": ["<Resource 1>", "<Resource 2>"],
      "approximate_duration_minutes": 30,
      "expected_student_output": "<Tangible artifact: chart, roleplay enactment, citizen draft>",
      "creative_assessment_preview": "<Feasible 5-minute review matching the period's outcomes>",
      "low_resource_alternative": "<Zero-cost fallback if materials are unavailable>"
    }},
    {{
      "id": "option_2",
      "title": "<Action-oriented active title>",
      "pedagogy_type": "<e.g. Case Inquiry / Evidence Audit>",
      "description": "...",
      "student_action_summary": "...",
      "teacher_facilitation_summary": "...",
      "student_grouping": "<Strictly follow: {logistics.group_summary_label} with assigned roles: {role_names_str}>",
      "required_materials": ["..."],
      "approximate_duration_minutes": 30,
      "expected_student_output": "...",
      "creative_assessment_preview": "...",
      "low_resource_alternative": "..."
    }},
    {{
      "id": "option_3",
      "title": "<Action-oriented active title>",
      "pedagogy_type": "<e.g. Station Jigsaw / Consensus Matrix>",
      "description": "...",
      "student_action_summary": "...",
      "teacher_facilitation_summary": "...",
      "student_grouping": "<Strictly follow: {logistics.group_summary_label} with assigned roles: {role_names_str}>",
      "required_materials": ["..."],
      "approximate_duration_minutes": 30,
      "expected_student_output": "...",
      "creative_assessment_preview": "...",
      "low_resource_alternative": "..."
    }}
  ]
}}
<|eot_id|><|start_header_id|>user<|end_header_id|>
CONTEXT:
- Grade: {grade_level} | Subject: Civic Education | Competency Level: {competency_level}
- Topic: {lesson_topic}
- Period Allocation: Period {current_period} of {total_periods} (40 Minutes)
- Student Count: {student_count} | Classroom Setting: {classroom_environment}
- Available Classroom Resources: {resources_formatted}

ALLOCATED VERBATIM LEARNING OUTCOMES FOR PERIOD {current_period}:
{outcomes_formatted}

INTERNAL SEQUENCE GUIDANCE FOR THIS PERIOD:
{progression_context or "Use the period position to sequence introduction, development, application, and formative assessment."}

Generate the 3 distinct, non-repetitive activity options now in valid JSON.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
    return prompt


def generate_fallback_options(
    competency_level: str,
    period_outcomes: List[str],
    current_period: int,
    total_periods: int,
    student_count: int,
    lesson_topic: str,
    previous_activities: Optional[List[str]] = None,
    classroom_environment: str = "Standard Classroom",
    accessible_resources: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Deterministic rule-based fallback that programmatically inspects
    previous_activities to ensure no fallback activity repeats earlier tracks
    and strictly applies Step 5 grouping logistics to every card.
    """
    # Clean base topic to avoid repeated '(Period X)' suffixes
    clean_topic = re.sub(r"\s*\(Period\s+\d+.*?\)", "", lesson_topic, flags=re.IGNORECASE).strip()
    if not clean_topic:
        clean_topic = f"Competency {competency_level}"

    # Step 5: Calculate exact grouping partition and roles
    logistics: GroupingLogisticsResult = GroupingLogisticsEngine.calculate_grouping(student_count)
    roles_str = ", ".join([r.role_name for r in logistics.roles_assigned])
    grouping_desc = f"{logistics.group_summary_label} with assigned roles: {roles_str}."
    available_materials = (
        list(accessible_resources)
        if accessible_resources
        else ["Blackboard", "Paper", "Student notebooks"]
    )

    first_outcome = (
        period_outcomes[0]
        if period_outcomes
        else f"Key concepts of Competency {competency_level}"
    )

    # Class-size specific participation and facilitation dynamics
    if student_count < 15:
        size_action_note = (
            f"Small class focus ({student_count} students): Working in {logistics.total_groups} compact seminar teams "
            f"({logistics.group_summary_label}), each student takes on active direct roles ({roles_str}) with continuous discussion."
        )
        size_facilitation_note = (
            f"Facilitates an intensive seminar circle across {logistics.group_summary_label}, "
            "directly engaging each student with outcome-focused probing questions."
        )
    elif student_count >= 46:
        size_action_note = (
            f"Large class management ({student_count} students): Organized into {logistics.total_groups} cluster teams "
            f"({logistics.group_summary_label}), students collaborate in assigned role pairs ({roles_str}) "
            "to ensure zero passive bystanders before consolidating team findings."
        )
        size_facilitation_note = (
            f"Monitors {logistics.total_groups} cluster stations, duplicates materials across teams, "
            "and coordinates timed spokesperson presentations to maintain momentum."
        )
    else:
        size_action_note = (
            f"Standard class layout ({student_count} students): Desks arranged into {logistics.total_groups} teams "
            f"({logistics.group_summary_label}), with students rotating responsibilities ({roles_str}) without bystanders."
        )
        size_facilitation_note = (
            f"Circulates across {logistics.total_groups} teams, facilitating role execution and formatively checking progress."
        )

    options_pool = [
        {
            "id": "opt_sim",
            "track": "Simulative & Roleplay",
            "title": f"Participatory Council Hearing: {clean_topic}",
            "pedagogy_type": "Simulation & Roleplay",
            "description": f"Students conduct a simulated community forum addressing '{first_outcome}'. Teams take civic roles, debate feasible responses, and agree on a resolution using oral discussion or the available board and notebooks.",
            "student_action_summary": f"Prepare brief citizen statements, propose priorities, and vote on a community resolution. {size_action_note}",
            "teacher_facilitation_summary": f"{size_facilitation_note} Introduces the scenario, moderates turns, and enforces time limits.",
            "student_grouping": grouping_desc,
            "required_materials": ["Role cue cards", "Blackboard for recording resolutions", "Notebooks"],
            "approximate_duration_minutes": 30,
            "expected_student_output": "Approved 3-point citizen resolution sheet recorded in notebooks.",
            "creative_assessment_preview": "1-Minute Freeze-Frame Tableau: Teams depict a moment of civic consensus.",
            "low_resource_alternative": "Assign verbal roles without physical paper cards.",
        },
        {
            "id": "opt_inq",
            "track": "Empirical & Investigative Inquiry",
            "title": f"Evidence-Based Case Dilemma Audit: {clean_topic}",
            "pedagogy_type": "Case Inquiry / Evidence Analysis",
            "description": f"Teams analyze a teacher-presented real-world civic dilemma reflecting '{first_outcome}'. They investigate institutional duties versus citizen responsibilities.",
            "student_action_summary": f"Discuss the scenario, identify civic duties, and record or report supporting evidence. {size_action_note}",
            "teacher_facilitation_summary": f"{size_facilitation_note} Provides scaffolding questions to guide student reasoning from facts to solutions.",
            "student_grouping": grouping_desc,
            "required_materials": ["Dilemma scenario sheets", "Observation charts"],
            "approximate_duration_minutes": 30,
            "expected_student_output": "Completed Civic Rights and Duties Inquiry Matrix.",
            "creative_assessment_preview": "Rapid Exit Slip: Students submit one duty and one right on a slip of paper.",
            "low_resource_alternative": "Write scenarios on the blackboard for students to copy.",
        },
        {
            "id": "opt_jig",
            "track": "Collaborative Design & Problem-Solving",
            "title": f"Thematic Station Jigsaw & Infographic Wall: {clean_topic}",
            "pedagogy_type": "Station Jigsaw / Collaborative Design",
            "description": f"Students explore teacher-designated board or discussion stations about '{first_outcome}'. Home groups reassemble to teach peers and synthesize key ideas.",
            "student_action_summary": f"Explore station prompts, return to home groups to teach peers, and co-create a summary. {size_action_note}",
            "teacher_facilitation_summary": f"{size_facilitation_note} Manages station rotation with clear time cues and formatively checks peer teaching.",
            "student_grouping": grouping_desc,
            "required_materials": ["Chart paper / Blackboard sections", "Color chalk/pens"],
            "approximate_duration_minutes": 30,
            "expected_student_output": "Synthesized Civic Action Infographic Poster.",
            "creative_assessment_preview": "2-Line Rhyming Slogan: Groups chant a summary of their core takeaway.",
            "low_resource_alternative": "Use notebook pages pinned to desks as station hubs.",
        },
        {
            "id": "opt_walk",
            "track": "Empirical & Investigative Inquiry",
            "title": f"School-Ground Field Audit & System Walk: {clean_topic}",
            "pedagogy_type": "Field Investigation / School Walk",
            "description": f"Students conduct a structured observation of an accessible school area or classroom example to examine systems related to '{first_outcome}'.",
            "student_action_summary": f"Record or verbally report observations, identify system gaps, and present recommendations. {size_action_note}",
            "teacher_facilitation_summary": f"{size_facilitation_note} Supervises movement, directs attention to evidence, and facilitates debriefing.",
            "student_grouping": grouping_desc,
            "required_materials": ["Clipboards or notebooks", "Audit checklist"],
            "approximate_duration_minutes": 30,
            "expected_student_output": "Completed Institutional Observation Checklist.",
            "creative_assessment_preview": "3-Question Peer Quiz: Student pairs quiz one another on observed civic structures.",
            "low_resource_alternative": "Draw the school organizational tree on the blackboard if outdoor access is restricted.",
        },
    ]

    existing_titles = " ".join(str(activity).lower() for activity in previous_activities or [])
    for track_name, method_names in PEDAGOGICAL_TRACK_DEFINITIONS.items():
        if "simulative" in track_name.lower():
            track = "Simulative & Roleplay"
            pedagogy_type = "Simulation / Roleplay"
            task = f"Students take civic roles, respond to a shared scenario, and agree on a reasoned decision. {size_action_note}"
            output = "A short role-based civic decision and its reasons."
            assessment = "Students state one role responsibility and explain how it supported the decision."
        elif "empirical" in track_name.lower():
            track = "Empirical & Investigative Inquiry"
            pedagogy_type = "Observation / Evidence Inquiry"
            task = f"Students inspect the provided scenario or accessible surroundings, record evidence, and compare findings. {size_action_note}"
            output = "An evidence record with one supported conclusion."
            assessment = "A paired evidence check: name one observation and the outcome it supports."
        else:
            track = "Collaborative Design & Problem-Solving"
            pedagogy_type = "Collaborative Design"
            task = f"Students negotiate a solution, create a shared civic artifact, and review another group's proposal. {size_action_note}"
            output = "A group civic proposal, diagram, or public information message."
            assessment = "Groups give one-sentence feedback connecting a peer proposal to the outcome."

        for method_name in method_names:
            if method_name.lower() in existing_titles:
                continue
            options_pool.append({
                "id": f"fallback_{len(options_pool) + 1}",
                "track": track,
                "title": f"{method_name}: {clean_topic}",
                "pedagogy_type": pedagogy_type,
                "description": f"Students use {method_name.lower()} to explore '{first_outcome}'. {task}",
                "student_action_summary": task,
                "teacher_facilitation_summary": f"{size_facilitation_note} Frames the task around '{first_outcome}' and monitors progress.",
                "student_grouping": grouping_desc,
                "required_materials": ["Student notebooks", "Blackboard or available paper"],
                "approximate_duration_minutes": 30,
                "expected_student_output": output,
                "creative_assessment_preview": assessment,
                "low_resource_alternative": "Use spoken prompts and notebook pages if printed or display materials are unavailable.",
            })

    # Vary fallback activity sets by the full competency, period, and allocated
    # outcomes; using only the final competency digit causes unrelated levels to collide.
    seed = "|".join(
        [competency_level.strip(), str(current_period), *period_outcomes]
    )
    rotated_pool = sorted(
        options_pool,
        key=lambda option: hashlib.sha256(
            f"{seed}|{option['id']}".encode("utf-8")
        ).digest(),
    )

    # Exclude previously selected task structures and titles
    selected = []
    for option in rotated_pool:
        opt_base = option["title"].split(":")[0].strip().lower()
        if opt_base not in existing_titles and option["title"].lower() not in existing_titles:
            selected.append(option)
        if len(selected) == 3:
            break

    if len(selected) < 3:
        selected_ids = {option["id"] for option in selected}
        for option in rotated_pool:
            if option["id"] not in selected_ids and option not in selected:
                selected.append(option)
            if len(selected) == 3:
                break

    for option in selected:
        if (
            (
                option["id"] == "opt_walk"
                or any(token in option["title"].casefold() for token in ("school-ground walk", "field audit"))
            )
            and "ground" not in classroom_environment.casefold()
            and "outdoor" not in classroom_environment.casefold()
        ):
            outcome_verb = first_outcome.casefold()
            if "identif" in outcome_verb:
                activity_focus = "Civic Evidence Classification"
                task = "classify teacher-presented examples, justify the categories, and check another group's reasoning"
                output = "A classified set of civic examples with brief justifications."
            elif "explain" in outcome_verb:
                activity_focus = "Civic Cause-and-Effect Mapping"
                task = "map how the presented civic examples connect, explain those relationships, and review a peer map"
                output = "A cause-and-effect map with student explanations."
            elif "investigat" in outcome_verb:
                activity_focus = "Civic Source Investigation"
                task = "compare teacher-presented evidence, record findings, and support a conclusion with evidence"
                output = "An evidence-based conclusion with supporting observations."
            elif "present" in outcome_verb or "appreciat" in outcome_verb:
                activity_focus = "Civic Recommendation Forum"
                task = "prepare and present a reasoned viewpoint, listen to peer responses, and refine a recommendation"
                output = "A supported viewpoint and refined recommendation."
            else:
                activity_focus = "Civic Systems Analysis"
                task = "analyze a teacher-presented civic example, identify its key features, and agree on a supported conclusion"
                output = "A group analysis with a supported conclusion."
            option["title"] = f"Competency {competency_level} {activity_focus}: {clean_topic}"
            option["description"] = (
                f"Students work with a teacher-presented classroom example about '{first_outcome}' "
                f"to {task}, without leaving the classroom."
            )
            option["student_action_summary"] = f"{task.capitalize()}. {size_action_note}"
            option["student_grouping"] = grouping_desc
            option["expected_student_output"] = output
            option["creative_assessment_preview"] = (
                f"Each group explains one part of its {activity_focus.casefold()} and links it to the outcome."
            )
            option["low_resource_alternative"] = (
                "Use a spoken teacher prompt and oral group responses if writing materials are unavailable."
            )
        option["required_materials"] = available_materials
        option["teacher_facilitation_summary"] = (
            f"Organizes all {student_count} students using {grouping_desc} "
            f"and monitors progress with outcome-focused prompts and time checks. {size_facilitation_note}"
        )

    # Re-index IDs to option_1, option_2, option_3 and bind outcomes
    final_options = []
    for idx, opt in enumerate(selected, 1):
        clean_opt = {k: v for k, v in opt.items() if k != "track"}
        clean_opt["id"] = f"option_{idx}"
        clean_opt["learning_outcomes_addressed"] = period_outcomes
        final_options.append(clean_opt)

    return {
        "topic": f"{clean_topic} (Period {current_period} of {total_periods})" if total_periods > 1 else clean_topic,
        "period": current_period,
        "options": final_options,
    }


def check_teacher_activity_suitability(
    custom_activity: str,
    period_outcomes: List[str],
    competency_level: str,
    grade_level: str = "Grade 8",
    subject: str = "Civic Education",
    current_period: int = 1,
    total_periods: int = 1,
    student_count: int = 35,
    classroom_environment: str = "Standard Classroom",
    accessible_resources: Optional[List[str]] = None,
    ollama_url: Optional[str] = None,
    model_name: str = "llama3",
) -> Dict[str, Any]:
    """
    RAG-driven evaluator checking whether a teacher's custom activity is suitable
    for achieving the allocated learning outcomes in a 40-minute period.
    If suitable: returns is_suitable=True.
    If not suitable: returns is_suitable=False, explaining why citing outcomes,
    and provides a concrete alternative activity aligned with the period's outcomes.
    """
    clean_activity = (custom_activity or "").strip()
    outcomes_summary = "; ".join(period_outcomes) if period_outcomes else "Curriculum Outcomes"

    # Pre-generate a high-quality alternative option from the pedagogical engine
    alt_result = generate_fallback_options(
        competency_level=competency_level,
        period_outcomes=period_outcomes,
        current_period=current_period,
        total_periods=total_periods,
        student_count=student_count,
        lesson_topic=f"Competency {competency_level}",
        previous_activities=[],
        classroom_environment=classroom_environment,
        accessible_resources=accessible_resources or [],
    )
    fallback_option = alt_result["options"][0] if alt_result.get("options") else None
    alt_title = fallback_option["title"] if fallback_option else f"Interactive Civic Investigation for Period {current_period}"
    alt_desc = fallback_option["description"] if fallback_option else f"Students work in collaborative small groups to examine real-world examples and achieve: {outcomes_summary}."

    # 1. Sanity check: Too short or empty
    if not clean_activity or len(clean_activity) < 8:
        return {
            "is_suitable": False,
            "reason": (
                f"The activity description is too brief to confirm alignment with the allocated "
                f"learning outcome(s) for Period {current_period}: {outcomes_summary}."
            ),
            "suggested_activity": alt_desc,
            "suggested_activity_title": alt_title,
        }

    # 2. Check for obvious off-topic / non-civic domains (e.g. Science, Mathematics, Biology)
    UNRELATED_DOMAINS = [
        "photosynthesis", "chlorophyll", "mitosis", "meiosis", "cellular respiration",
        "quadratic equation", "pythagorean", "trigonometry", "algebraic expression",
        "chemical reaction", "titration", "periodic table", "atomic structure",
        "circulatory system", "digestive system", "newton's laws", "electromagnetism",
        "magnetism", "gravitational force", "calculus", "geometry proof",
    ]
    activity_lower = clean_activity.casefold()
    for term in UNRELATED_DOMAINS:
        if term in activity_lower:
            return {
                "is_suitable": False,
                "reason": (
                    f"The proposed activity focuses on an unrelated scientific or mathematical topic ('{term}') "
                    f"rather than the Civic Education learning outcome(s) allocated for Period {current_period}: {outcomes_summary}. "
                    "In Civic Education, activities must guide students to explore democratic governance, public institutions, rights, duties, and community systems."
                ),
                "suggested_activity": alt_desc,
                "suggested_activity_title": alt_title,
            }

    # 3. LLM-based evaluation via local Ollama endpoint (if reachable)
    try:
        import urllib.request
        endpoint = ollama_url or "http://localhost:11434"
        prompt = (
            "You are an official National Institute of Education (NIE) Sri Lanka curriculum validator for Civic Education.\n"
            f"Subject: {subject} ({grade_level})\n"
            f"Competency Level: {competency_level}\n"
            f"Period: Period {current_period} of {total_periods} (40-Minute Duration)\n"
            f"Allocated Learning Outcomes for this Period:\n" +
            "\n".join(f"- {o}" for o in (period_outcomes or [])) + "\n\n"
            f"Teacher's Proposed Activity:\n\"{clean_activity}\"\n\n"
            "Task: Evaluate whether this activity is SUITABLE for achieving the allocated learning outcomes.\n"
            "Rules:\n"
            "1. An activity is SUITABLE if it engages students in learning, exploring, roleplaying, or discussing concepts in the allocated outcomes.\n"
            "2. An activity is NOT SUITABLE if it is off-topic, contradicts the outcomes, lacks active student participation, or cannot be done in 40 minutes.\n"
            "3. If NOT SUITABLE, state the exact mismatch in 'reason' citing the outcomes, and provide an engaging alternative classroom activity in 'suggested_activity'.\n\n"
            "Return ONLY a JSON object:\n"
            '{\n  "is_suitable": true or false,\n  "reason": "explanation of alignment or mismatch with outcomes",\n  "suggested_activity": "alternative description if unsuitable, else empty",\n  "suggested_activity_title": "alternative title if unsuitable, else empty"\n}'
        )
        req = urllib.request.Request(
            f"{endpoint}/api/generate",
            data=json.dumps({"model": model_name, "prompt": prompt, "stream": False, "format": "json"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            parsed = json.loads(data.get("response", "{}"))
            if "is_suitable" in parsed:
                is_s = bool(parsed["is_suitable"])
                reason = parsed.get("reason", "")
                s_act = parsed.get("suggested_activity") or alt_desc
                s_title = parsed.get("suggested_activity_title") or alt_title
                return {
                    "is_suitable": is_s,
                    "reason": reason if not is_s else f"Activity aligns with Period {current_period} learning outcome(s): {outcomes_summary}.",
                    "suggested_activity": s_act if not is_s else "",
                    "suggested_activity_title": s_title if not is_s else "",
                }
    except Exception as exc:
        logger.debug("Ollama suitability check call skipped or unavailable: %s", exc)

    # 4. Deterministic pedagogical fallback validation
    civic_keywords = [
        "civic", "public", "service", "community", "council", "sabha", "pradeshiya",
        "citizen", "government", "rights", "duties", "law", "rule", "court",
        "school", "roleplay", "simulation", "debate", "discuss", "video", "clip",
        "inquiry", "investigat", "poster", "presentation", "case study", "dilemma",
        "group", "pair", "students", "learn", "activity", "interview", "question",
    ]
    # Check if there is semantic or keyword alignment with civic concepts or the outcomes
    outcome_words = set(re.findall(r"\w{4,}", outcomes_summary.casefold()))
    activity_words = set(re.findall(r"\w{4,}", activity_lower))

    has_civic_term = any(k in activity_lower for k in civic_keywords)
    has_outcome_overlap = bool(activity_words & outcome_words)

    if has_civic_term or has_outcome_overlap:
        return {
            "is_suitable": True,
            "reason": f"Activity aligns with Period {current_period} learning outcome(s): {outcomes_summary}.",
            "suggested_activity": "",
            "suggested_activity_title": "",
        }

    return {
        "is_suitable": False,
        "reason": (
            f"The proposed activity lacks clear pedagogical alignment with the allocated learning outcome(s) "
            f"for Period {current_period}: {outcomes_summary}. Please align the activity with the civic concepts."
        ),
        "suggested_activity": alt_desc,
        "suggested_activity_title": alt_title,
    }