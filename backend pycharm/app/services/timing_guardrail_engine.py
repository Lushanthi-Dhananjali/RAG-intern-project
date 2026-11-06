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
            act_clean = (selected_activity or "Collaborative Inquiry").splitlines()[0]
            act_clean = re.sub(r"^Activity:\s*", "", act_clean, flags=re.IGNORECASE).strip() or "Collaborative Inquiry"
            topic_clean = focus_outcome or lesson_topic or "Civic Core Principles"
            return [
                LessonDevelopmentStepDto(
                    step_number=1,
                    time_minutes=10,
                    learning_teaching_method=f"Orientation & {act_clean} Launch",
                    learning_teaching_aids=f"Task cards for {act_clean}, chalkboard, student notebooks",
                    teacher_activities=f"Teacher introduces the Sri Lankan real-world scenario for '{topic_clean}', clarifies objectives, and distributes task cards for {act_clean}.",
                    student_activities=f"Students arrange into collaborative groups, review inquiry prompts for {act_clean}, assign group roles, and formulate investigative questions.",
                    assessment_and_feedback="",
                ),
                LessonDevelopmentStepDto(
                    step_number=2,
                    time_minutes=10,
                    learning_teaching_method=act_clean,
                    learning_teaching_aids=f"Activity worksheets, scenario cards, and materials for {act_clean}",
                    teacher_activities=f"Teacher circulates among student groups as facilitator, scaffolds student inquiry into '{topic_clean}', and monitors dynamic execution of {act_clean}.",
                    student_activities=f"Students actively collaborate in assigned roles to execute {act_clean}, analyzing civic situations related to '{topic_clean}' without passive spectators.",
                    assessment_and_feedback="",
                ),
                LessonDevelopmentStepDto(
                    step_number=3,
                    time_minutes=10,
                    learning_teaching_method=f"Presentation & Synthesis of {act_clean}",
                    learning_teaching_aids=f"Completed group charts from {act_clean}, whiteboard",
                    teacher_activities=f"Teacher moderates student team presentations, facilitates constructive peer review, and synthesizes discoveries regarding '{topic_clean}'.",
                    student_activities=f"Group spokespersons present findings and solutions from {act_clean}; peers evaluate presentations and note key takeaways in their notebooks.",
                    assessment_and_feedback="",
                ),
            ]

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

        # Strategy B: Proportional scaling for 5+ steps
        # Normalize and clamp delta into the longest middle activity step
        scale_factor = 30.0 / max(1, current_sum)
        allocated_so_far = 0

        for i in range(step_count - 1):
            normalized = max(3, round(steps[i].time_minutes * scale_factor))
            steps[i].time_minutes = normalized
            allocated_so_far += normalized

        # Assign remaining minutes to final step, ensuring at least 3 minutes
        steps[-1].time_minutes = max(3, 30 - allocated_so_far)

        # Final pass verification
        final_sum = sum(s.time_minutes for s in steps)
        if final_sum != 30:
            steps[1].time_minutes += (30 - final_sum)

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

        def needs_repair(text: Optional[str], phase: str) -> bool:
            normalized = (text or "").strip()
            if len(normalized) < 25 or unavailable_text.search(normalized):
                return True
            if normalized in ("...", "...", "string", "<string>") or normalized.endswith("..."):
                if len(normalized) < 45 or "linking prior knowledge" in normalized or "concluding task" in normalized:
                    return True
            if "Teacher presents everyday scenario and motivational hook" in normalized:
                return True
            if "Each student writes two key responsibilities on their reflection sheet" in normalized:
                return True
            if phase == "introduction":
                return False
            if phase == "assignment":
                if any(
                    phrase in normalized.casefold()
                    for phrase in ("homework", "take-home", "at home", "next lesson", "outside class")
                ):
                    return True
                return False
            return False

        if needs_repair(plan.the_entrance, "introduction"):
            if requested_period == 1:
                plan.the_entrance = (
                    f"5-minute motivational entrance: The teacher presents an authentic Sri Lankan real-life situation related to '{focus}' "
                    "and invites students to share an everyday observation from their home or community. Students discuss briefly in pairs, "
                    f"and the teacher connects their real-world observations directly to today's {activity}."
                )
            elif requested_period == 2:
                plan.the_entrance = (
                    f"5-minute motivational entrance: The teacher reviews key findings from Period 1 with a quick dilemma question on '{focus}'. "
                    f"Students share reflections from their notebooks, and the teacher transitions into the collaborative inquiry phase of {activity}."
                )
            else:
                plan.the_entrance = (
                    f"5-minute motivational entrance: The teacher introduces an engaging community inquiry question on '{focus}' affecting "
                    f"Sri Lankan society. Students briefly brainstorm in their teams, and the teacher sets the stage for today's active execution of {activity}."
                )
        elif not re.search(r"5\s*[- ]?minutes?", plan.the_entrance, re.IGNORECASE):
            plan.the_entrance = f"5-minute introduction: {plan.the_entrance.strip()}"

        if needs_repair(plan.post_activity, "assignment"):
            if requested_period == 1:
                plan.post_activity = (
                    f"5-minute creative in-class assignment: Rapid Team Mini-Quiz. The teacher presents 3 quick scenario questions about '{focus}', "
                    f"and student teams hold up colored cards to vote and give a 1-sentence justification using evidence from {activity}."
                )
            elif requested_period == 2:
                plan.post_activity = (
                    f"5-minute creative in-class assignment: 2-Line Rhyming Verse / Quick Sketch Challenge. Each cooperative team creates a 2-line rhyming "
                    f"couplet or a quick symbolic sketch illustrating how '{focus}' was demonstrated during {activity}, then shares it with the class."
                )
            else:
                plan.post_activity = (
                    f"5-minute creative in-class assignment: Pass-the-Parcel Concept Ball & Statement Vote. A concept ball is passed while a beat plays; "
                    f"the student holding the ball responds to a quick real-life dilemma on '{focus}', followed by a class consensus vote."
                )
        elif not re.search(r"5\s*[- ]?minutes?", plan.post_activity, re.IGNORECASE):
            plan.post_activity = f"5-minute in-class assignment: {plan.post_activity.strip()}"

        if (
            not plan.assessment_and_feedback_whole_lesson
            or len(plan.assessment_and_feedback_whole_lesson.strip()) < 10
            or unavailable_text.search(plan.assessment_and_feedback_whole_lesson)
            or "final closure formative" in plan.assessment_and_feedback_whole_lesson.lower()
        ):
            plan.assessment_and_feedback_whole_lesson = (
                f"3-minute formative feedback: Formatively evaluate student contributions and understanding of '{focus}' during {activity} "
                "and the 5-minute closing check, offering immediate verbal affirmation and constructive feedback."
            )

        if (
            not plan.summary
            or len(plan.summary.strip()) < 15
            or unavailable_text.search(plan.summary)
            or "consolidation and synthesis" in plan.summary.lower()
        ):
            plan.summary = (
                f"2-minute consolidation: Synthesize core student findings from {activity}, highlighting how '{focus}' applies to real Sri Lankan "
                "community life and resolving any conceptual misconceptions."
            )

        if plan.attachments:
            plan.attachments = [
                att.strip() for att in plan.attachments
                if not unavailable_text.search(att) and len(att.strip()) >= 3
            ]

        # 5. Sanitize all developmental steps from URLs, placeholders, and duplicate repetitive sentences
        seen_methods = set()
        seen_teacher_acts = set()
        seen_student_acts = set()

        for idx, step in enumerate(plan.lesson_development_steps, start=1):
            # Sanitize learning_teaching_method: keep LLM method, only clean if missing/URL/duplicate
            method_str = (step.learning_teaching_method or "").strip()
            method_str = re.sub(r"^<string:\s*[^>]+>\s*", "", method_str, flags=re.IGNORECASE).strip()
            is_generic_placeholder = any(
                p in method_str.casefold()
                for p in ("task orientation", "guided inquiry launch", "active student-centered investigation", "spokesperson presentation, peer review")
            )
            is_dup_method = method_str.casefold() in seen_methods

            if not method_str or len(method_str) < 3 or unavailable_text.search(method_str) or is_generic_placeholder or is_dup_method:
                if "learning-teaching-method" in method_str:
                    slug = re.sub(r"^https?://[^\s/]+/learning-teaching-method/?", "", method_str)
                    step.learning_teaching_method = slug.replace("-", " ").strip().title() or f"{activity} Exploration"
                elif idx == 1:
                    step.learning_teaching_method = f"Orientation & {activity} Setup"
                elif idx == 2:
                    step.learning_teaching_method = f"Collaborative Deep-Dive: {activity}"
                elif idx == 3:
                    step.learning_teaching_method = f"Spokesperson Presentation & Peer Review: {activity}"
                else:
                    step.learning_teaching_method = f"Plenary Consolidation: {activity}"
            else:
                step.learning_teaching_method = method_str
            seen_methods.add(step.learning_teaching_method.casefold())

            # Sanitize learning_teaching_aids: keep LLM aids, only clean if missing/URL/none
            aids_str = (step.learning_teaching_aids or "").strip()
            aids_str = re.sub(r"^<string:\s*[^>]+>\s*", "", aids_str, flags=re.IGNORECASE).strip()
            is_none_aids = aids_str.casefold() in ("none", "none.", "n/a", "null", "no aids", "not applicable")
            if not aids_str or len(aids_str) < 3 or is_none_aids or unavailable_text.search(aids_str):
                if "learning-teaching-aids" in aids_str:
                    slug = re.sub(r"^https?://[^\s/]+/learning-teaching-aids/?", "", aids_str)
                    step.learning_teaching_aids = slug.replace("-", ", ").strip().title() or f"Task materials for {activity}"
                elif idx == 1:
                    step.learning_teaching_aids = f"Inquiry prompt cards for {activity}, scenario prompts, chalkboard, student notebooks"
                elif idx == 2:
                    step.learning_teaching_aids = f"Worksheets and activity cards for {activity}, chart paper, markers"
                elif idx == 3:
                    step.learning_teaching_aids = f"Presentation charts created during {activity}, whiteboard, peer review criteria sheets"
                else:
                    step.learning_teaching_aids = f"Synthesis reflection sheets and summary cards for {activity}"
            else:
                step.learning_teaching_aids = aids_str

            # Sanitize teacher_activities: PRESERVE LLM GENERATED CONTENT! DO NOT HARDCODE OR OVERWRITE!
            t_str = (step.teacher_activities or "").strip()
            t_str = re.sub(r"^<string:\s*[^>]+>\s*", "", t_str, flags=re.IGNORECASE)
            t_str = re.sub(r"\.\.\.$", "", t_str).strip()
            is_dup_teacher = t_str.casefold() in seen_teacher_acts

            # Only provide fallback if LLM generated literally nothing (< 15 chars), contained a URL, or repeated identical text from an earlier step
            if not t_str or len(t_str) < 15 or is_dup_teacher or unavailable_text.search(t_str):
                if idx == 1:
                    step.teacher_activities = (
                        f"The teacher presents the Sri Lankan real-world dilemma on '{focus}', organizes students into collaborative teams "
                        f"with designated roles, and distributes inquiry task cards for {activity} as facilitator without lecturing."
                    )
                elif idx == 2:
                    step.teacher_activities = (
                        f"The teacher actively circulates among the groups executing {activity}, scaffolds student "
                        f"discussions around '{focus}' with probing questions, and formatively observes team collaboration."
                    )
                elif idx == 3:
                    step.teacher_activities = (
                        f"The teacher moderates group spokesperson presentations on '{focus}', guides peer groups in offering "
                        f"constructive feedback, and synthesizes the core civic insights discovered through {activity}."
                    )
                else:
                    step.teacher_activities = (
                        f"The teacher facilitates final group consensus on '{focus}', helps students resolve conceptual questions, "
                        f"and consolidates key learnings from {activity}."
                    )
            else:
                step.teacher_activities = t_str
            seen_teacher_acts.add(step.teacher_activities.casefold())

            # Sanitize student_activities: PRESERVE LLM GENERATED CONTENT! DO NOT HARDCODE OR OVERWRITE!
            s_str = (step.student_activities or "").strip()
            s_str = re.sub(r"^<string:\s*[^>]+>\s*", "", s_str, flags=re.IGNORECASE)
            s_str = re.sub(r"\.\.\.$", "", s_str).strip()
            is_dup_student = s_str.casefold() in seen_student_acts

            # Only provide fallback if LLM generated literally nothing (< 15 chars), contained a URL, or repeated identical text from an earlier step
            if not s_str or len(s_str) < 15 or is_dup_student or unavailable_text.search(s_str):
                if idx == 1:
                    step.student_activities = (
                        f"Students arrange themselves in assigned group roles, examine the inquiry challenge concerning '{focus}', "
                        f"and prepare their collaborative materials for {activity}."
                    )
                elif idx == 2:
                    step.student_activities = (
                        f"Students actively carry out {activity}, working in teams to analyze real-world civic situations "
                        f"related to '{focus}' and co-create their group findings without passive bystanders."
                    )
                elif idx == 3:
                    step.student_activities = (
                        f"Team spokespersons present their group's findings on '{focus}' to the class, compare conclusions with peers, "
                        "and record constructive feedback in their notebooks."
                    )
                else:
                    step.student_activities = (
                        f"Students review feedback received from peer teams, refine their group conclusions regarding '{focus}', "
                        "and note personal civic responsibilities in their reflection sheets."
                    )
            else:
                step.student_activities = s_str
            seen_student_acts.add(step.student_activities.casefold())

            # Sanitize other and assessment_and_feedback
            if step.other and unavailable_text.search(step.other):
                step.other = ""
            if step.assessment_and_feedback and unavailable_text.search(step.assessment_and_feedback):
                step.assessment_and_feedback = f"Checks student participation and understanding of '{focus}'."

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