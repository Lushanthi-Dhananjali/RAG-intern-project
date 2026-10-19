"""
Period-Aware Independent 3-Option Activity Generator Engine for Civic Education.
Implements strict anti-repetition filtering across periods using previous_period_activities.
Rotates pedagogy tracks (Simulation, Field Inquiry, Collaborative Jigsaw) without duplication
and integrates the Step 5 Grouping & Logistics Engine to eliminate passive bystanders.
"""

import json
import re
import logging
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
2. Distinct Pedagogical Tracks:
   - Option 1: Simulative / Roleplay / Mock Deliberation (if not already used).
   - Option 2: Empirical Observation / Case Inquiry / Evidence Analysis.
   - Option 3: Station Jigsaw / Problem-Solving Carousel / Civic Design Matrix.
3. Student-Centred Facilitation: Students actively investigate, discuss, and create; the teacher acts strictly as a facilitator, timekeeper, and prompt guide.
4. Step 5 Grouping & Logistics Mandate:
   - Partition Scheme: {logistics.group_summary_label}.
   - Roles to Distribute: {role_names_str}.
   - Management Guidance: {logistics.pedagogy_adaptation}.
   - Zero bystanders: Every student must have one of the designated roles above.
5. 5-Minute Assessment Preview: Include a creative, active 5-minute learning check (e.g., tableau, rhyme, exit slip, pass-the-parcel quiz).
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
) -> Dict[str, Any]:
    """
    Deterministic rule-based fallback that programmatically inspects
    previous_activities to ensure no fallback activity repeats earlier tracks
    and strictly applies Step 5 grouping logistics to every card.
    """
    # Step 5: Calculate exact grouping partition and roles
    logistics: GroupingLogisticsResult = GroupingLogisticsEngine.calculate_grouping(student_count)
    roles_str = ", ".join([r.role_name for r in logistics.roles_assigned])
    grouping_desc = f"{logistics.group_summary_label} with assigned roles: {roles_str}."

    first_outcome = (
        period_outcomes[0]
        if period_outcomes
        else f"Key concepts of Competency {competency_level}"
    )
    used_tracks = detect_used_pedagogical_tracks(previous_activities or [])

    options_pool = [
        {
            "id": "opt_sim",
            "track": "Simulative & Roleplay",
            "title": f"Participatory Council Hearing: {lesson_topic}",
            "pedagogy_type": "Simulation & Roleplay",
            "description": f"Students conduct a simulated community forum addressing '{first_outcome}'. Teams act as ward citizens, community elders, and public officers to present and debate solutions.",
            "student_action_summary": "Draft 2-minute citizen statements, propose municipal priorities, and vote on a community resolution.",
            "teacher_facilitation_summary": "Acts as meeting speaker, moderates speaking turns, and enforces time limits.",
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
            "title": f"Evidence-Based Case Dilemma Audit: {lesson_topic}",
            "pedagogy_type": "Case Inquiry / Evidence Analysis",
            "description": f"Teams analyze real-world civic dilemma cards reflecting '{first_outcome}'. They investigate institutional duties versus citizen responsibilities.",
            "student_action_summary": "Examine case scenarios, highlight legal/civic duties, and compile evidence on a grievance matrix.",
            "teacher_facilitation_summary": "Provides scaffolding questions to guide student reasoning from facts to solutions.",
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
            "title": f"Thematic Station Jigsaw & Infographic Wall: {lesson_topic}",
            "pedagogy_type": "Station Jigsaw / Collaborative Design",
            "description": f"Students rotate through learning stations exploring sub-themes of '{first_outcome}'. Home groups reassemble to create a synthesized infographic.",
            "student_action_summary": "Master station cards, return to home groups to teach peers, and co-design a poster.",
            "teacher_facilitation_summary": "Manages station rotation buzzer (7 mins/station) and formatively checks peer teaching.",
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
            "title": f"School-Ground Field Audit & System Walk: {lesson_topic}",
            "pedagogy_type": "Field Investigation / School Walk",
            "description": f"Students conduct a structured 15-minute observation walk around the school grounds to observe administrative governance systems related to '{first_outcome}'.",
            "student_action_summary": "Record observations on clipboard sheets, identify system gaps, and present recommendations.",
            "teacher_facilitation_summary": "Supervises perimeter safety, directs student attention to institutional signage, and facilitates debriefing.",
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
            task = "Students take civic roles, respond to a shared scenario, and agree on a reasoned decision."
            output = "A short role-based civic decision and its reasons."
            assessment = "Students state one role responsibility and explain how it supported the decision."
        elif "empirical" in track_name.lower():
            track = "Empirical & Investigative Inquiry"
            pedagogy_type = "Observation / Evidence Inquiry"
            task = "Students inspect the provided scenario or accessible surroundings, record evidence, and compare findings."
            output = "An evidence record with one supported conclusion."
            assessment = "A paired evidence check: name one observation and the outcome it supports."
        else:
            track = "Collaborative Design & Problem-Solving"
            pedagogy_type = "Collaborative Design"
            task = "Students negotiate a solution, create a shared civic artifact, and review another group's proposal."
            output = "A group civic proposal, diagram, or public information message."
            assessment = "Groups give one-sentence feedback connecting a peer proposal to the outcome."

        for method_name in method_names:
            if method_name.lower() in existing_titles:
                continue
            options_pool.append({
                "id": f"fallback_{len(options_pool) + 1}",
                "track": track,
                "title": f"{method_name}: {lesson_topic}",
                "pedagogy_type": pedagogy_type,
                "description": f"Students use {method_name.lower()} to work with '{first_outcome}'. {task}",
                "student_action_summary": task,
                "teacher_facilitation_summary": "Frames the task around the assigned outcome, prompts evidence-based reasoning, and facilitates participation.",
                "student_grouping": grouping_desc,
                "required_materials": ["Student notebooks", "Blackboard or available paper"],
                "approximate_duration_minutes": 30,
                "expected_student_output": output,
                "creative_assessment_preview": assessment,
                "low_resource_alternative": "Use spoken prompts and notebook pages if printed or display materials are unavailable.",
            })

    # Exclude previously selected task structures, then rotate the remaining pedagogies.
    selected = [
        option for option in options_pool
        if option["title"].split(":")[0].lower() not in existing_titles
    ][:3]

    if len(selected) < 3:
        selected_ids = {option["id"] for option in selected}
        selected.extend(
            option for option in options_pool
            if option["id"] not in selected_ids
            and option not in selected
        )
        selected = selected[:3]

    # Re-index IDs to option_1, option_2, option_3
    final_options = []
    for idx, opt in enumerate(selected, 1):
        clean_opt = {k: v for k, v in opt.items() if k != "track"}
        clean_opt["id"] = f"option_{idx}"
        final_options.append(clean_opt)

    return {
        "topic": f"{lesson_topic} (Period {current_period})",
        "period": current_period,
        "options": final_options,
    }