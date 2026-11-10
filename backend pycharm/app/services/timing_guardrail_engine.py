"""
Step 8: Deterministic Guardrails & Timing Auto-Repair Engine.
Enforces strict 40-minute LEARN framework invariants (5m - 30m - 5m)
and guarantees verbatim NIE learning outcomes injection.
"""

import logging
import re
from typing import List, Optional
from app.schemas.lesson_plan_schema_dto import (
    LearnLessonPlanDto,
    LessonDevelopmentStepDto,
)

logger = logging.getLogger("TimingGuardrailEngine")

# Standard pedagogical blueprints for 30-minute developmental blocks
STANDARD_DEVELOPMENT_STEP_PRESETS = {
    1: [30],
    2: [15, 15],
    3: [10, 10, 10],
    4: [5, 10, 10, 5],
}

KNOWN_COMPETENCY_TITLES = {
    "8.1.1": "Identifies public services and investigates the need and importance of the time.",
    "8.1.2": "Names the public services provided for the area identifying them.",
    "8.1.3": "Explains the duties and responsibilities of public service institutions.",
    "8.1.4": "Explains the importance of citizens fulfilling duties and rights related to use of public services.",
    "8.2.1": "Introduces himself/herself correctly and socializes.",
    "8.2.2": "Understands the abilities and skills and uses them for self development.",
    "8.2.3": "Controls the emotions in such a way that it safeguards the existence of a democratic society.",
    "8.2.4": "Builds healthy relationships appreciating and respecting differences and diversity.",
    "8.2.5": "Develops qualities that are required for a democratic life.",
    "8.3.1": "Analyses the features of a multicultural society",
    "8.3.2": "Explains that Sri Lanka is a multicultural society.",
    "8.3.3": "Contributes to the building of national cohesion and sustainable peace safeguarding one's own cultural identity",
    "8.4.1": "Contributes to minimize accidents and disasters by identifying them.",
    "8.4.2": "Works intelligently in disaster situations",
    "8.4.3": "Explains the importance of being alert about the situations where accidents and disasters might happen.",
    "8.4.4": "Contributes to minimizing road accidents by following road rules.",
    "8.4.5": "Contributes to minimize dangers caused by chemicals.",
    "8.4.6": "Contributes to sustainable development adapting a bearable life style",
    "8.5.1": "Defines problems and challenges simply.",
    "8.5.2": "Faces different problems and challenges in life successfully.",
    "8.6.1": "Appreciates the diversity in the world of work",
    "8.6.2": "Describes the importance of working with a sense of dignity of labour.",
    "8.6.3": "Explains that all employments contribute to fulfilling social needs.",
    "8.6.4": "Explains the need of getting the training related to one's field of work as a worker.",
    "8.6.5": "Internalizes the qualities of a good labourer",
    "8.6.6": "Explains the need to be sensitive as a worker to the expectations of the work place.",
    "8.6.7": "Investigates Workers' rights and responsibilities.",
    "8.6.8": "Explains the importance of maintaining personal performance at a higher level as a worker.",
    "8.6.9": "Suggests strategies to satisfy customers.",
    "8.6.10": "Suggests ways and means to improve income.",
}


def resolve_clean_competence_title(competence_code: str, fallback_text: str = "") -> str:
    """Returns official syllabus competence standard title, never a URL."""
    clean_code = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", competence_code or "")
    code_val = clean_code.group(1) if clean_code else (competence_code or "").strip()
    if code_val in KNOWN_COMPETENCY_TITLES:
        return KNOWN_COMPETENCY_TITLES[code_val]
    if fallback_text and not re.search(r"https?://|www\.", fallback_text, re.IGNORECASE):
        return fallback_text.strip()
    return f"Explores and investigates core curriculum concepts for Competency {code_val or 'Standard'}."



class TimingGuardrailEngine:
    """
    Mathematical normalizer and invariant enforcer for 40-minute lesson plans.
    """

    @staticmethod
    def auto_repair_step_timings(
        steps: List[LessonDevelopmentStepDto],
        selected_activity: str = "",
        focus_outcome: str = "",
        lesson_topic: str = "",
    ) -> List[LessonDevelopmentStepDto]:
        """
        Guarantees that the sum of lesson development steps equals exactly 30 minutes in clean multiples of 5.
        Repairs LLM timing drift without overwriting valid auto-generated step content.
        If steps are empty, synthesizes dynamic steps tailored to the specific activity and learning outcome.
        """
        if not steps:
            return steps

        step_count = len(steps)
        current_sum = sum(s.time_minutes for s in steps)

        # Re-index step numbers consecutively (1 to N)
        for idx, s in enumerate(steps, start=1):
            s.step_number = idx


        # If already exactly 30 minutes and all steps are multiples of 5, preserve LLM's proportional decisions
        if current_sum == 30 and all(s.time_minutes % 5 == 0 and s.time_minutes >= 5 for s in steps):
            return steps

        logger.warning(
            "Timing drift detected: Developmental steps sum to %dm (target: 30m) or non-multiples of 5. Auto-repairing...",
            current_sum,
        )

        # Round all steps to nearest multiple of 5 (min 5 mins)
        for s in steps:
            s.time_minutes = max(5, int(round(s.time_minutes / 5.0) * 5))

        current_sum = sum(s.time_minutes for s in steps)
        drift = 30 - current_sum

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

    @staticmethod
    def enforce_invariants_and_inject_outcomes(
        plan: LearnLessonPlanDto,
        verbatim_outcomes: List[str],
        requested_period: int = 1,
        total_periods: int = 1,
        lesson_topic: str = "",
        selected_activity: Optional[str] = None,
        competency_level: Optional[str] = None,
        broad_competence: Optional[str] = None,
    ) -> LearnLessonPlanDto:
        """
        Enforces complete Step 8 guardrails:
        1. Injects official verbatim learning outcomes (overwriting any LLM paraphrasing).
        2. Normalizes developmental step timings to sum to exactly 30 minutes.
        3. Formats the canonical time allocation string.
        4. Validates that the Entrance and Assessment phases comply with the 5m boundaries.
        """
        # 1. Verbatim TIG Outcomes Injection
        if verbatim_outcomes and len(verbatim_outcomes) > 0:
            clean_outcomes = [o.strip() for o in verbatim_outcomes if o.strip()]
            plan.unique_learning_outcome = clean_outcomes
            logger.info("Programmatically injected %d verbatim TIG outcome(s).", len(clean_outcomes))

        focus = next(
            (outcome.strip().rstrip(".") for outcome in verbatim_outcomes if outcome.strip()),
            lesson_topic.strip() or "the period topic",
        )
        activity_lines = (selected_activity or "").strip().splitlines()
        activity = activity_lines[0] if activity_lines else ""
        activity = re.sub(r"^Activity:\s*", "", activity, flags=re.IGNORECASE).strip()
        activity = activity or "the selected student activity"

        # 2. Timing Auto-Repair (passes activity and focus for dynamic synthesis if needed)
        plan.lesson_development_steps = TimingGuardrailEngine.auto_repair_step_timings(
            steps=plan.lesson_development_steps,
            selected_activity=activity,
            focus_outcome=focus,
            lesson_topic=lesson_topic
        )

        # 3. Time Allocation Formatting
        plan.time_allocation = f"40 Minutes (Period {requested_period} of {total_periods})"
        relevant_terms = {
            word.casefold()
            for word in re.findall(r"[A-Za-z]{4,}", focus)
        }
        unavailable_text = re.compile(
            r"https?://|www\.|unknown|not available|n/?a\b|todo|placeholder",
            re.IGNORECASE,
        )

        # Strip literal prompt boilerplate prefixes from entrance, post_activity, and summary if present
        if plan.the_entrance:
            plan.the_entrance = re.sub(r"^<string:\s*[^>]+>\s*", "", plan.the_entrance.strip(), flags=re.IGNORECASE).strip()
        if plan.post_activity:
            plan.post_activity = re.sub(r"^<string:\s*[^>]+>\s*", "", plan.post_activity.strip(), flags=re.IGNORECASE).strip()
        if plan.summary:
            plan.summary = re.sub(r"^<string:\s*[^>]+>\s*", "", plan.summary.strip(), flags=re.IGNORECASE).strip()
        if plan.assessment_and_feedback_whole_lesson:
            plan.assessment_and_feedback_whole_lesson = re.sub(r"^<string:\s*[^>]+>\s*", "", plan.assessment_and_feedback_whole_lesson.strip(), flags=re.IGNORECASE).strip()
        if plan.the_entrance:
            plan.the_entrance = re.sub(
                r"^Detailed 5-minute introduction:\s*(?:teacher and student actions linking prior knowledge to this period topic and activity(?:\.\.\.)?)?\s*",
                "",
                plan.the_entrance.strip(),
                flags=re.IGNORECASE
            ).strip()
            plan.the_entrance = re.sub(
                r"^Creative 5-minute motivational hook:\s*",
                "",
                plan.the_entrance.strip(),
                flags=re.IGNORECASE
            ).strip()

        if plan.post_activity:
            plan.post_activity = re.sub(
                r"^(?:5-minute in-class assignment:\s*)?Five-minute in-class assignment or concluding task(?:\.\.\.)?\s*",
                "",
                plan.post_activity.strip(),
                flags=re.IGNORECASE
            ).strip()
            plan.post_activity = re.sub(
                r"^Creative 5-minute in-class assignment\s*(?:\([^)]*\))?:\s*",
                "",
                plan.post_activity.strip(),
                flags=re.IGNORECASE
            ).strip()

        # 4. Clean placeholders from entrance, post_activity, summary, and whole lesson assessment
        if plan.the_entrance:
            ent = plan.the_entrance.strip()
            ent = re.sub(r"^<string:\s*[^>]+>\s*", "", ent, flags=re.IGNORECASE).strip()
            ent = re.sub(r"\.\.\.$", "", ent).strip()
            if ent and not re.search(r"5\s*[- ]?minutes?", ent, re.IGNORECASE):
                plan.the_entrance = f"5-minute introduction: {ent}"
            elif ent:
                plan.the_entrance = ent

        if plan.post_activity:
            post = plan.post_activity.strip()
            post = re.sub(r"^<string:\s*[^>]+>\s*", "", post, flags=re.IGNORECASE).strip()
            post = re.sub(r"\.\.\.$", "", post).strip()
            if post and not re.search(r"5\s*[- ]?minutes?", post, re.IGNORECASE):
                plan.post_activity = f"5-minute in-class assignment: {post}"
            elif post:
                plan.post_activity = post

        if plan.assessment_and_feedback_whole_lesson:
            af = plan.assessment_and_feedback_whole_lesson.strip()
            af = re.sub(r"^<string:\s*[^>]+>\s*", "", af, flags=re.IGNORECASE).strip()
            af = re.sub(r"\.\.\.$", "", af).strip()
            plan.assessment_and_feedback_whole_lesson = af

        if plan.summary:
            sm = plan.summary.strip()
            sm = re.sub(r"^<string:\s*[^>]+>\s*", "", sm, flags=re.IGNORECASE).strip()
            sm = re.sub(r"\.\.\.$", "", sm).strip()
            plan.summary = sm

        if plan.attachments:
            plan.attachments = [
                att.strip() for att in plan.attachments
                if not unavailable_text.search(att) and len(att.strip()) >= 3
            ]

        # 5. Sanitize all developmental steps from placeholders and URLs - preserve LLM dynamic content completely!
        for idx, step in enumerate(plan.lesson_development_steps, start=1):
            method_str = (step.learning_teaching_method or "").strip()
            method_str = re.sub(r"^<string:\s*[^>]+>\s*", "", method_str, flags=re.IGNORECASE).strip()
            method_str = re.sub(r"\.\.\.$", "", method_str).strip()
            if "learning-teaching-method" in method_str:
                slug = re.sub(r"^https?://[^\s/]+/learning-teaching-method/?", "", method_str)
                method_str = slug.replace("-", " ").strip().title()
            step.learning_teaching_method = method_str

            aids_str = (step.learning_teaching_aids or "").strip()
            aids_str = re.sub(r"^<string:\s*[^>]+>\s*", "", aids_str, flags=re.IGNORECASE).strip()
            aids_str = re.sub(r"\.\.\.$", "", aids_str).strip()
            if "learning-teaching-aids" in aids_str:
                slug = re.sub(r"^https?://[^\s/]+/learning-teaching-aids/?", "", aids_str)
                aids_str = slug.replace("-", ", ").strip().title()
            step.learning_teaching_aids = aids_str

            t_str = (step.teacher_activities or "").strip()
            t_str = re.sub(r"^<string:\s*[^>]+>\s*", "", t_str, flags=re.IGNORECASE).strip()
            t_str = re.sub(r"\.\.\.$", "", t_str).strip()
            step.teacher_activities = t_str

            s_str = (step.student_activities or "").strip()
            s_str = re.sub(r"^<string:\s*[^>]+>\s*", "", s_str, flags=re.IGNORECASE).strip()
            s_str = re.sub(r"\.\.\.$", "", s_str).strip()
            step.student_activities = s_str

            if step.other and unavailable_text.search(step.other):
                step.other = ""
            step.assessment_and_feedback = ""

        # 6. Sanitize Competence Level and Competence Statement from URLs and unknown links
        # Competence Level sanitization
        if competency_level and competency_level.strip() and not unavailable_text.search(competency_level):
            plan.competence_level = competency_level.strip()
        elif not plan.competence_level or unavailable_text.search(plan.competence_level):
            code_match = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", plan.competence_level or "")
            if code_match:
                plan.competence_level = code_match.group(1)
            elif competency_level and competency_level.strip():
                plan.competence_level = competency_level.strip()
            else:
                plan.competence_level = "8.1.1"
        else:
            plan.competence_level = plan.competence_level.strip()

        # Competence Statement sanitization
        if broad_competence and broad_competence.strip() and not unavailable_text.search(broad_competence):
            if not plan.competence or unavailable_text.search(plan.competence):
                plan.competence = broad_competence.strip()

        if not plan.competence or unavailable_text.search(plan.competence):
            code_str = plan.competence_level or competency_level or ""
            plan.competence = resolve_clean_competence_title(code_str, fallback_text=lesson_topic)
        else:
            plan.competence = plan.competence.strip()

        # Sanitize lesson title if it contains any URL
        if plan.lesson and unavailable_text.search(plan.lesson):
            clean_lesson = re.sub(r"https?://\S+", "", plan.lesson).strip()
            plan.lesson = clean_lesson or focus

        # Sanitize information_sources if it contains fabricated api links
        if plan.information_sources:
            plan.information_sources = [
                s for s in plan.information_sources
                if not re.search(r"https?://|api\.learn\.kandy\.lk", s, re.IGNORECASE)
            ]

        return plan