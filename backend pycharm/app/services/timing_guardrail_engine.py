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
    2: [12, 18],
    3: [8, 14, 8],
    4: [6, 10, 8, 6],
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
    ) -> List[LessonDevelopmentStepDto]:
        """
        Guarantees that the sum of lesson development steps equals exactly 30 minutes.
        Repairs LLM drift without failing generation or throwing validation errors.
        """
        if not steps:
            # Fallback to default 3-step scaffold if LLM emitted an empty array
            return [
                LessonDevelopmentStepDto(
                    step_number=1,
                    time_minutes=8,
                    learning_teaching_method="Task Orientation & Prompt Distribution",
                    learning_teaching_aids="Task assignment cards, chalkboard",
                    teacher_activities="Distributes materials and sets investigative goals.",
                    student_activities="Review task cards in assigned groups.",
                    assessment_and_feedback="Checks student readiness and clarifies questions.",
                ),
                LessonDevelopmentStepDto(
                    step_number=2,
                    time_minutes=14,
                    learning_teaching_method="Cooperative Group Investigation",
                    learning_teaching_aids="Worksheets, student notebooks",
                    teacher_activities="Circulates to provide scaffolding and monitor roles.",
                    student_activities="Collaborate within assigned roles to solve the problem.",
                    assessment_and_feedback="Provides formative feedback on ongoing discussion.",
                ),
                LessonDevelopmentStepDto(
                    step_number=3,
                    time_minutes=8,
                    learning_teaching_method="Plenary Presentation & Review",
                    learning_teaching_aids="Blackboard, completed posters",
                    teacher_activities="Facilitates peer review and synthesizes main findings.",
                    student_activities="Spokespersons share group outputs with class.",
                    assessment_and_feedback="Clarifies misconceptions and provides peer assessment.",
                ),
            ]

        step_count = len(steps)
        current_sum = sum(s.time_minutes for s in steps)

        # Re-index step numbers consecutively (1 to N)
        for idx, s in enumerate(steps, start=1):
            s.step_number = idx

        # If already exactly 30 minutes, preserve LLM's proportional decisions
        if current_sum == 30:
            return steps

        logger.warning(
            "Timing drift detected: Developmental steps sum to %dm (target: 30m). Auto-repairing...",
            current_sum,
        )

        # Strategy A: Use proven preset if step count is between 1 and 4
        if step_count in STANDARD_DEVELOPMENT_STEP_PRESETS:
            preset = STANDARD_DEVELOPMENT_STEP_PRESETS[step_count]
            for s, allocated_mins in zip(steps, preset):
                s.time_minutes = allocated_mins
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

        # 2. Timing Auto-Repair
        plan.lesson_development_steps = TimingGuardrailEngine.auto_repair_step_timings(
            plan.lesson_development_steps
        )

        # 3. Time Allocation Formatting
        plan.time_allocation = f"40 Minutes (Period {requested_period} of {total_periods})"

        focus = next(
            (outcome.strip().rstrip(".") for outcome in verbatim_outcomes if outcome.strip()),
            lesson_topic.strip() or "the period topic",
        )
        activity_lines = (selected_activity or "").strip().splitlines()
        activity = activity_lines[0] if activity_lines else ""
        activity = re.sub(r"^Activity:\s*", "", activity, flags=re.IGNORECASE).strip()
        activity = activity or "the selected student activity"
        relevant_terms = {
            word.casefold()
            for word in re.findall(r"[A-Za-z]{4,}", focus)
        }
        unavailable_text = re.compile(
            r"https?://|www\.|unknown|not available|n/?a\b|todo|placeholder",
            re.IGNORECASE,
        )

        def needs_repair(text: Optional[str], phase: str) -> bool:
            normalized = (text or "").strip()
            if len(normalized) < 30 or unavailable_text.search(normalized):
                return True
            if phase == "introduction":
                has_teacher = "teacher" in normalized.casefold()
                has_students = any(term in normalized.casefold() for term in ("students", "learners"))
                return not (has_teacher and has_students) or (
                    bool(relevant_terms)
                    and not any(term in normalized.casefold() for term in relevant_terms)
                )
            return (
                any(
                    phrase in normalized.casefold()
                    for phrase in ("homework", "take-home", "at home", "next lesson", "outside class")
                )
                or not any(
                    verb in normalized.casefold()
                    for verb in (
                        "write", "draw", "answer", "complete", "exit", "quiz", "identify",
                        "explain", "state", "share", "prepare", "create", "record", "submit",
                        "respond", "describe",
                    )
                )
                or (
                    bool(relevant_terms)
                    and not any(term in normalized.casefold() for term in relevant_terms)
                )
            )

        if needs_repair(plan.the_entrance, "introduction"):
            plan.the_entrance = (
                f"5-minute introduction: The teacher writes or reads “{focus}” and asks students "
                "to name one example they have seen in everyday life. Students share brief responses; "
                f"the teacher connects their examples to {activity} and explains how it will help "
                "them explore this period's outcome."
            )
        elif not re.search(r"\b5\s*[- ]?minutes?\b", plan.the_entrance, re.IGNORECASE):
            plan.the_entrance = f"5-minute introduction: {plan.the_entrance.strip()}"

        if needs_repair(plan.post_activity, "assignment"):
            plan.post_activity = (
                f"5-minute in-class assignment: Each student completes a short exit response explaining "
                f"one finding about “{focus}” using evidence or an example from {activity}. "
                "The teacher reviews responses for an accurate link to the period outcome."
            )
        elif not re.search(r"\b5\s*[- ]?minutes?\b", plan.post_activity, re.IGNORECASE):
            plan.post_activity = f"5-minute in-class assignment: {plan.post_activity.strip()}"

        if not plan.assessment_and_feedback_whole_lesson or len(plan.assessment_and_feedback_whole_lesson.strip()) < 10 or unavailable_text.search(plan.assessment_and_feedback_whole_lesson):
            plan.assessment_and_feedback_whole_lesson = (
                f"Use the student's five-minute assignment response to check understanding of “{focus}” "
                "and give one concise correction or affirmation."
            )

        if not plan.summary or len(plan.summary.strip()) < 15 or unavailable_text.search(plan.summary):
            plan.summary = (
                f"Synthesize key student findings from {activity}, emphasizing the core principles "
                f"of “{focus}” and clarifying any lingering misconceptions."
            )

        if plan.attachments:
            plan.attachments = [
                att.strip() for att in plan.attachments
                if not unavailable_text.search(att) and len(att.strip()) >= 3
            ]

        # 5. Sanitize all developmental steps from URLs and placeholders
        for idx, step in enumerate(plan.lesson_development_steps, start=1):
            # Sanitize learning_teaching_method
            method_str = (step.learning_teaching_method or "").strip()
            if not method_str or len(method_str) < 3 or unavailable_text.search(method_str):
                if "learning-teaching-method" in method_str:
                    slug = re.sub(r"^https?://[^\s/]+/learning-teaching-method/?", "", method_str)
                    step.learning_teaching_method = slug.replace("-", " ").strip().title() or "Guided Inquiry & Discussion"
                elif idx == 1:
                    step.learning_teaching_method = "Task Orientation & Guided Inquiry Setup"
                elif idx == 2:
                    step.learning_teaching_method = activity if len(activity) < 50 else "Interactive Inquiry & Problem-Solving"
                else:
                    step.learning_teaching_method = "Plenary Presentation & Review"

            # Sanitize learning_teaching_aids
            aids_str = (step.learning_teaching_aids or "").strip()
            if not aids_str or len(aids_str) < 3 or unavailable_text.search(aids_str):
                if "learning-teaching-aids" in aids_str:
                    slug = re.sub(r"^https?://[^\s/]+/learning-teaching-aids/?", "", aids_str)
                    step.learning_teaching_aids = slug.replace("-", ", ").strip().title() or "Chalkboard, student notebooks, task prompt cards"
                elif idx == 1:
                    step.learning_teaching_aids = "Inquiry prompt cards, chalkboard, student notebooks"
                elif idx == 2:
                    step.learning_teaching_aids = "Activity scenario cards, observation sheets, chart paper"
                else:
                    step.learning_teaching_aids = "Presentation board, student summary sheets, whiteboard"

            # Sanitize teacher_activities
            t_str = (step.teacher_activities or "").strip()
            if not t_str or len(t_str) < 20 or unavailable_text.search(t_str):
                if idx == 1:
                    step.teacher_activities = (
                        f"The teacher introduces the lesson inquiry on '{focus}', organizes students into collaborative teams "
                        "with designated roles, and distributes inquiry task prompt cards."
                    )
                elif idx == 2:
                    step.teacher_activities = (
                        f"The teacher actively circulates among the groups to facilitate {activity}, scaffolds student "
                        f"discussions around '{focus}', prompts critical thinking, and formatively monitors student engagement."
                    )
                else:
                    step.teacher_activities = (
                        f"The teacher facilitates group presentations, synthesizes student discoveries regarding '{focus}', "
                        "highlights core civic values, and formatively clarifies any conceptual misconceptions."
                    )

            # Sanitize student_activities
            s_str = (step.student_activities or "").strip()
            if not s_str or len(s_str) < 20 or unavailable_text.search(s_str):
                if idx == 1:
                    step.student_activities = (
                        f"Students arrange themselves in assigned group roles, examine the inquiry prompt concerning '{focus}', "
                        "and prepare materials for their investigation."
                    )
                elif idx == 2:
                    step.student_activities = (
                        f"Students actively carry out {activity}, collaborating in teams to analyze real-world civic situations "
                        f"related to '{focus}' without passive bystanders."
                    )
                else:
                    step.student_activities = (
                        f"Team spokespersons present their group's findings on '{focus}' to the class, compare conclusions with peers, "
                        "and record constructive feedback in their notebooks."
                    )

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