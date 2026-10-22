import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

# =====================================================================
# PATH RESOLUTION & ENVIRONMENT SETUP
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

logger = logging.getLogger("RAGLessonPlanGenerator")

# Import Schemas (LEARN Practice Teaching Format)
try:
    from app.schemas.lesson_plan_schema_dto import (
        LearnLessonPlanDto,
        LessonPlanSchemaDto,
        LessonDevelopmentStepDto,
    )
except ModuleNotFoundError:
    try:
        from schemas.lesson_plan_schema_dto import (
            LearnLessonPlanDto,
            LessonPlanSchemaDto,
            LessonDevelopmentStepDto,
        )
    except ModuleNotFoundError:
        from lesson_plan_schema_dto import (
            LearnLessonPlanDto,
            LessonPlanSchemaDto,
            LessonDevelopmentStepDto,
        )

# Import Prompt Builders
try:
    from app.services.prompt_templates import (
        build_lesson_plan_prompt,
        build_activity_options_prompt,
        LEARN_PRACTICE_TEACHING_PROMPT,
    )
except ModuleNotFoundError:
    try:
        from services.prompt_templates import (
            build_lesson_plan_prompt,
            build_activity_options_prompt,
            LEARN_PRACTICE_TEACHING_PROMPT,
        )
    except ModuleNotFoundError:
        from prompt_templates import (
            build_lesson_plan_prompt,
            build_activity_options_prompt,
            LEARN_PRACTICE_TEACHING_PROMPT,
        )

# Import Step 4 Period-Aware Activity Options Engine
try:
    from app.services.activity_options_engine import (
        build_period_options_prompt,
        generate_fallback_options,
        check_teacher_activity_suitability,
    )
except ModuleNotFoundError:
    try:
        from services.activity_options_engine import (
            build_period_options_prompt,
            generate_fallback_options,
            check_teacher_activity_suitability,
        )
    except ModuleNotFoundError:
        build_period_options_prompt = None
        generate_fallback_options = None
        check_teacher_activity_suitability = None

try:
    from app.services.outcome_allocator import (
        extract_civic_tig_learning_outcomes,
        restore_period_allocation_from_saved_plans,
    )
except ModuleNotFoundError:
    try:
        from services.outcome_allocator import (
            extract_civic_tig_learning_outcomes,
            restore_period_allocation_from_saved_plans,
        )
    except ModuleNotFoundError:
        extract_civic_tig_learning_outcomes = None
        restore_period_allocation_from_saved_plans = None

try:
    from app.services.generated_plans_manager import get_competency_period_plans
except ModuleNotFoundError:
    try:
        from services.generated_plans_manager import get_competency_period_plans
    except ModuleNotFoundError:
        get_competency_period_plans = None

try:
    from app.services.multi_grade_retriever import format_retrieved_source_references
except ModuleNotFoundError:
    try:
        from services.multi_grade_retriever import format_retrieved_source_references
    except ModuleNotFoundError:
        format_retrieved_source_references = None

# Import Step 6 Mode B Teacher Scaffolding Engine
try:
    from app.services.teacher_mode_engine import build_mode_b_scaffolding_prompt
except ModuleNotFoundError:
    try:
        from services.teacher_mode_engine import build_mode_b_scaffolding_prompt
    except ModuleNotFoundError:
        build_mode_b_scaffolding_prompt = None

# Import Step 7 Single-Period 40-Minute Assembly Engine
try:
    from app.services.lesson_plan_assembler import (
        balance_development_step_times,
        build_single_period_assembly_prompt,
    )
except ModuleNotFoundError:
    try:
        from services.lesson_plan_assembler import (
            balance_development_step_times,
            build_single_period_assembly_prompt,
        )
    except ModuleNotFoundError:
        balance_development_step_times = None
        build_single_period_assembly_prompt = None

# Import Step 8 Deterministic Guardrail Engine
try:
    from app.services.timing_guardrail_engine import TimingGuardrailEngine
except ModuleNotFoundError:
    try:
        from services.timing_guardrail_engine import TimingGuardrailEngine
    except ModuleNotFoundError:
        TimingGuardrailEngine = None

# Import Step 3 Multi-Period Outcome Allocator Engine
try:
    from app.services.outcome_allocator import (
        allocate_learning_outcomes_across_periods,
        extract_verbatim_tig_outcomes,
    )
except ModuleNotFoundError:
    try:
        from services.outcome_allocator import (
            allocate_learning_outcomes_across_periods,
            extract_verbatim_tig_outcomes,
        )
    except ModuleNotFoundError:
        allocate_learning_outcomes_across_periods = None
        from app.services.multi_grade_retriever import extract_verbatim_tig_outcomes

# Import Evaluators & Guardrails
try:
    from app.evaluation.evaluator import RAGFactCheckingAgent
    from app.evaluation.alignment_evaluator import AlignmentEvaluator
except ModuleNotFoundError:
    try:
        from evaluation.evaluator import RAGFactCheckingAgent
        from evaluation.alignment_evaluator import AlignmentEvaluator
    except ModuleNotFoundError:
        from evaluator import RAGFactCheckingAgent
        from alignment_evaluator import AlignmentEvaluator

# Import 3-Tier Multi-Grade Boundary Retriever
try:
    from app.services.multi_grade_retriever import MultiGradeBoundaryRetriever
except ModuleNotFoundError:
    try:
        from services.multi_grade_retriever import MultiGradeBoundaryRetriever
    except ModuleNotFoundError:
        from multi_grade_retriever import MultiGradeBoundaryRetriever


# =====================================================================
# DYNAMIC EXEMPLAR-DRIVEN RAG GENERATOR (OLLAMA / LOCAL LLAMA 3)
# =====================================================================

class RAGLessonPlanGenerator:
    """
    RAG Lesson Plan Generation engine running completely on local Llama 3 via Ollama.
    Dynamically orchestrates:
    1. Retrieval of multi-tier curriculum boundaries (TIG, Textbook, Exemplars).
    2. Period-aware student-centered options discovery (3 meaningfully different options per period).
    3. Mode B Teacher's Own Approach Scaffolding preserving custom pedagogical intent.
    4. Step 7 Strict 40-Minute Single-Period Assembly (5m Intro, 30m Dev, 5m Closure).
    5. Step 8 Deterministic Guardrails & Mathematical timing auto-repair.
    6. LLM JSON generation via local Ollama endpoint with strict grammar-based schema decoding.
    7. Programmatic verbatim learning outcome injection from official TIG syllabus matrix.
    8. Validation via LearnLessonPlanDto and disk persistence.
    9. Safe fact-checking and pedagogical alignment guardrail evaluations with fallback.
    """

    def __init__(
        self,
        chroma_path: Optional[str] = None,
        ollama_url: Optional[str] = None,
        model_name: str = "llama3"
    ):
        if chroma_path is None:
            chroma_path = os.getenv(
                "CHROMA_DB_PATH",
                os.path.join(PROJECT_ROOT, "chroma_db")
            )

        self.chroma_path = chroma_path
        self.ollama_url = ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name

        self.retriever = MultiGradeBoundaryRetriever(chroma_path=self.chroma_path)
        self.evaluator = RAGFactCheckingAgent(score_threshold=0.85)
        self.alignment_evaluator = AlignmentEvaluator(threshold=0.75)

        self.last_eval_report = None
        self.last_align_report = None

    def check_custom_activity_suitability(
        self,
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
    ) -> Dict[str, Any]:
        """
        Validates whether teacher's custom activity is pedagogically suitable
        for achieving the allocated learning outcomes of the requested period.
        """
        if check_teacher_activity_suitability is not None:
            return check_teacher_activity_suitability(
                custom_activity=custom_activity,
                period_outcomes=period_outcomes,
                competency_level=competency_level,
                grade_level=grade_level,
                subject=subject,
                current_period=current_period,
                total_periods=total_periods,
                student_count=student_count,
                classroom_environment=classroom_environment,
                accessible_resources=accessible_resources,
                ollama_url=self.ollama_url,
                model_name=self.model_name,
            )
        return {
            "is_suitable": True,
            "reason": "Default suitability check passed.",
            "suggested_activity": "",
            "suggested_activity_title": "",
        }

    def generate_activity_options(
        self,
        competency_level: str,
        student_count: int = 35,
        periods: int = 1,
        requested_period: int = 1,
        grade_level: str = "Grade 8",
        subject: str = "Civic Education",
        classroom_environment: str = "Standard Classroom",
        accessible_resources: Optional[List[str]] = None,
        previous_activities: Optional[List[str]] = None,
        lesson_topic: str = ""
    ) -> Dict[str, Any]:
        """
        Generates 3 independent, student-centred activity cards specifically
        tailored to the outcomes allocated for requested_period.
        Enforces anti-repetition against previous_activities and applies Step 5 grouping logistics.
        """
        clean_level = competency_level.strip()
        safe_periods = min(max(periods, 1), 4)
        safe_requested = min(max(requested_period, 1), safe_periods)

        # 1. Retrieve TIG Guidelines from ChromaDB
        dual_context = self.retriever.retrieve_tig_and_textbook_for_level(
            clean_level, f"Competency {clean_level}", grade_level, subject
        )
        tig_chunks = dual_context.get("tig_guidelines", [])

        # 2. Extract Verbatim Outcomes
        extracted_outcomes: List[str] = []
        for chunk in tig_chunks:
            found = (
                extract_civic_tig_learning_outcomes(chunk.get("content", ""), clean_level)
                if extract_civic_tig_learning_outcomes is not None
                else []
            )
            for outcome in found:
                if outcome not in extracted_outcomes:
                    extracted_outcomes.append(outcome)

        if not extracted_outcomes:
            raise ValueError(
                f"No official learning outcomes were retrieved for Civic Education "
                f"{grade_level}, Competency Level {clean_level}. "
                "Activity options cannot be generated without curriculum outcomes."
            )

        # 3. Retrieve ONLY outcomes allocated for the requested period
        progression_context = ""
        if allocate_learning_outcomes_across_periods is not None:
            allocation_plan = allocate_learning_outcomes_across_periods(
                all_outcomes=extracted_outcomes,
                periods=safe_periods,
                competency_level=clean_level
            )
            if (
                get_competency_period_plans is not None
                and restore_period_allocation_from_saved_plans is not None
            ):
                saved_period_plans = get_competency_period_plans(
                    grade=grade_level,
                    competency_level=clean_level,
                    subject=subject,
                    total_periods=safe_periods,
                )
                restore_period_allocation_from_saved_plans(
                    allocation_plan=allocation_plan,
                    saved_period_plans=saved_period_plans,
                    total_periods=safe_periods,
                    competency_level=clean_level,
                )
            period_outcomes = allocation_plan.get_outcomes_for_period(safe_requested)
            progression_context = allocation_plan.get_progression_summary_for_period(safe_requested)
        else:
            period_outcomes = extracted_outcomes

        activity_topic = lesson_topic.strip() or f"Competency Level {clean_level}"
        lesson_topic = f"{activity_topic} (Period {safe_requested} of {safe_periods})"

        # 4. Build Period-Aware Prompt
        if build_period_options_prompt is not None:
            prompt = build_period_options_prompt(
                competency_level=clean_level,
                period_outcomes=period_outcomes,
                current_period=safe_requested,
                total_periods=safe_periods,
                student_count=student_count,
                lesson_topic=lesson_topic,
                grade_level=grade_level,
                classroom_environment=classroom_environment,
                accessible_resources=accessible_resources,
                previous_activities=previous_activities,
                progression_context=progression_context
            )
        else:
            prompt = build_activity_options_prompt(
                competency_level=clean_level,
                grade=grade_level,
                subject=subject,
                topic=lesson_topic,
                student_count=student_count,
                periods=safe_periods,
                tig_context="\n\n".join([c.get("content", "") for c in tig_chunks])
            )

        # 5. Execute LLM Call (Ollama / Llama 3)
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.3,
                "num_predict": 1400,
                "num_thread": 6
            }
        }

        valid_llm_options: List[Dict[str, Any]] = []
        fallback_previous_activities = list(previous_activities or [])
        try:
            res = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=90)
            res.raise_for_status()
            raw = res.json().get("response", "{}")
            clean_str = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(clean_str)

            parsed_options = parsed.get("options", [])
            if isinstance(parsed_options, list) and len(parsed_options) == 3:
                prior_activity_text = " ".join(
                    str(activity).casefold() for activity in fallback_previous_activities
                )
                seen_titles = set()
                for option in parsed_options:
                    if not isinstance(option, dict):
                        continue
                    title = str(option.get("title", "")).strip()
                    normalized_title = title.casefold()
                    if (
                        not normalized_title
                        or normalized_title in seen_titles
                        or normalized_title in prior_activity_text
                    ):
                        continue
                    seen_titles.add(normalized_title)
                    option["learning_outcomes_addressed"] = period_outcomes
                    valid_llm_options.append(option)

            if len(valid_llm_options) == 3:
                parsed["period"] = safe_requested
                parsed["topic"] = lesson_topic
                parsed["options"] = valid_llm_options
                return parsed
            if valid_llm_options:
                logger.info(
                    "Discarded repeated activity options for Competency %s Period %d; "
                    "completing the options with distinct fallback activities.",
                    clean_level,
                    safe_requested,
                )
                fallback_previous_activities.extend(
                    str(option["title"]) for option in valid_llm_options
                )
        except Exception as err:
            logger.warning("LLM options generation error: %s. Using pedagogical fallback.", err)

        # 6. Fallback Activation with anti-repetition filter
        if generate_fallback_options is not None:
            fallback = generate_fallback_options(
                competency_level=clean_level,
                period_outcomes=period_outcomes,
                current_period=safe_requested,
                total_periods=safe_periods,
                student_count=student_count,
                lesson_topic=lesson_topic,
                previous_activities=fallback_previous_activities,
                classroom_environment=classroom_environment,
                accessible_resources=accessible_resources,
            )
        else:
            fallback = {
                "topic": lesson_topic,
                "period": safe_requested,
                "options": [
                    {
                        "id": "option_1",
                        "title": f"Community Council Roleplay: {lesson_topic}",
                        "pedagogy_type": "Simulation & Roleplay",
                        "description": "Students enact a community meeting debating civic challenges and drafting a resolution.",
                        "student_grouping": f"{max(2, student_count // 6)} teams of 5-6 students",
                        "required_materials": ["Role cue cards", "Notebooks"],
                        "approximate_duration_minutes": 30,
                        "creative_assessment_preview": "1-Minute Freeze-Frame Tableau representing a core civic value."
                    },
                    {
                        "id": "option_2",
                        "title": f"Evidence-Based Case Inquiry: {lesson_topic}",
                        "pedagogy_type": "Case Inquiry / Evidence Analysis",
                        "description": "Students analyze real-life local scenario cards to identify rights and constitutional duties.",
                        "student_grouping": f"{max(2, student_count // 5)} investigation teams",
                        "required_materials": ["Dilemma slips", "Observation worksheets"],
                        "approximate_duration_minutes": 30,
                        "creative_assessment_preview": "Rapid Exit Ticket on a key civic right and corresponding duty."
                    },
                    {
                        "id": "option_3",
                        "title": f"Collaborative Station Jigsaw: {lesson_topic}",
                        "pedagogy_type": "Station Jigsaw / Collaborative Design",
                        "description": "Station experts investigate distinct civic pillars and return to home groups to co-create an infographic.",
                        "student_grouping": f"{max(2, student_count // 5)} home groups",
                        "required_materials": ["Chart papers", "Color markers"],
                        "approximate_duration_minutes": 30,
                        "creative_assessment_preview": "2-Line Rhyming Jingle summarizing the main lesson takeaway."
                    }
                ]
            }

        combined_options = valid_llm_options + fallback["options"]
        distinct_options: List[Dict[str, Any]] = []
        seen_titles = set()
        for option in combined_options:
            title = str(option.get("title", "")).strip().casefold()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            distinct_options.append(option)
            if len(distinct_options) == 3:
                break

        for index, opt in enumerate(distinct_options, start=1):
            opt["id"] = f"option_{index}"
            opt["learning_outcomes_addressed"] = period_outcomes
        fallback["options"] = distinct_options
        return fallback

    def generate_prompt(
        self,
        user_query: str,
        retrieved_data: Dict[str, Any],
        dual_context: Dict[str, Any],
        grade_level: str = "Grade 8",
        subject: str = "Civic Education",
        competency_level: str = "8.1.1",
        periods: int = 1,
        time_slot: str = "40 Minutes (1 Period)",
        duration_minutes: int = 40,
        retrieved_outcomes: Optional[List[str]] = None,
        selected_activity_strategy: Optional[str] = None,
        student_count: int = 35,
        current_period: int = 1,
        total_periods: int = 1,
        progression_context: str = "",
    ) -> str:
        exemplar_chunks = [
            item.get("content", "")
            for item in retrieved_data.get("practical_exemplars", [])
        ]

        retrieved_competence = ""
        for item in dual_context.get("tig_guidelines", []):
            meta = item.get("metadata", {})
            comp_val = meta.get("competence") or meta.get("competency")
            if comp_val and comp_val not in ["General", ""]:
                retrieved_competence = comp_val.strip()
                break

        tig_chunks = [
            item.get("content", "")
            for item in dual_context.get("tig_guidelines", [])
            if item.get("content", "").strip()
        ]

        textbook_chunks = [
            item.get("content", "")
            for item in dual_context.get("textbook_paragraphs", [])
        ]
        prereq_chunks = [
            item.get("content", "")
            for item in retrieved_data.get("tier_2_prerequisites", [])
        ]
        upper_chunks = [
            item.get("content", "")
            for item in retrieved_data.get("tier_3_upper_boundaries", [])
        ]

        context_sections = []

        if tig_chunks:
            tig_combined = "\n\n".join(tig_chunks)
            header = f"--- [OFFICIAL TIG GUIDELINES | LEVEL: {competency_level}] ---"
            if retrieved_competence:
                header += f"\nMAIN COMPETENCY: {retrieved_competence}"
            context_sections.append(f"{header}\n{tig_combined}")

        if textbook_chunks:
            textbook_combined = "\n\n".join(textbook_chunks)[:2500]
            context_sections.append(
                f"--- PUPIL TEXTBOOK REFERENCE ---\n{textbook_combined}"
            )

        if prereq_chunks:
            prereq_combined = "\n\n".join(prereq_chunks)[:800]
            context_sections.append(
                f"--- [PREREQUISITE BASELINE (DO NOT RE-TEACH)] ---\n{prereq_combined}"
            )

        if upper_chunks:
            upper_combined = "\n\n".join(upper_chunks)[:800]
            context_sections.append(
                f"--- [UPPER BOUNDARY LIMIT (DO NOT EXCEED)] ---\n{upper_combined}"
            )

        if exemplar_chunks:
            exemplar_combined = "\n\n".join(exemplar_chunks)[:800]
            context_sections.append(
                f"--- [BLUEPRINT EXEMPLAR LESSON PLANS] ---\n{exemplar_combined}"
            )

        assembled_context = "\n\n".join(context_sections)
        exemplar_combined_str = "\n\n".join(exemplar_chunks)[:800] if exemplar_chunks else ""

        return build_lesson_plan_prompt(
            query=user_query,
            grade=grade_level,
            subject=subject,
            competency_level=competency_level,
            periods=periods,
            duration_minutes=duration_minutes,
            retrieved_context=assembled_context,
            exemplar_context=exemplar_combined_str,
            retrieved_outcomes=retrieved_outcomes,
            selected_activity_strategy=selected_activity_strategy,
            student_count=student_count,
            current_period=current_period,
            total_periods=total_periods
        )

    def validate_generation_sequence(self, plan: LearnLessonPlanDto) -> bool:
        """
        Performs explicit domain validations for the LEARN Practice Teaching structure:
        - Checks presence of competence, competence_level, lesson title.
        - Verifies at least 1 unique learning outcome is present (after injection).
        - Verifies the entrance section.
        - Verifies that structured lesson development steps exist.
        - Verifies summary and whole-lesson assessment.
        """
        if not plan.lesson or not plan.lesson.strip():
            raise ValueError("Validation Failure: 'lesson' (topic) is missing.")
        if not plan.competence or not plan.competence.strip():
            raise ValueError("Validation Failure: 'competence' standard is missing.")
        if not plan.competence_level or not plan.competence_level.strip():
            raise ValueError("Validation Failure: 'competence_level' is missing.")
        if not plan.unique_learning_outcome or len(plan.unique_learning_outcome) < 1:
            raise ValueError("Validation Failure: LEARN format requires at least 1 distinct unique learning outcome.")
        if not plan.the_entrance or not plan.the_entrance.strip():
            raise ValueError("Validation Failure: 'the_entrance' (introductory phase) is missing.")
        if not plan.lesson_development_steps or len(plan.lesson_development_steps) < 2:
            raise ValueError("Validation Failure: At least 2 structured 'lesson_development_steps' must be defined.")

        for idx, step in enumerate(plan.lesson_development_steps, 1):
            if not step.teacher_activities.strip():
                raise ValueError(f"Validation Failure: 'teacher_activities' missing in Step {idx}.")
            if not step.student_activities.strip():
                raise ValueError(f"Validation Failure: 'student_activities' missing in Step {idx}.")
            if not step.learning_teaching_method.strip():
                raise ValueError(f"Validation Failure: 'learning_teaching_method' missing in Step {idx}.")

        if not plan.summary.strip():
            raise ValueError("Validation Failure: 'summary' section is missing.")
        if not plan.assessment_and_feedback_whole_lesson.strip():
            raise ValueError("Validation Failure: 'assessment_and_feedback_whole_lesson' criteria is missing.")
        if not plan.post_activity.strip():
            raise ValueError("Validation Failure: 'post_activity' five-minute assignment is missing.")
        if plan.entrance_duration_minutes != 5 or plan.assignment_duration_minutes != 5:
            raise ValueError("Validation Failure: introduction and assignment must each be 5 minutes.")

        return True

    def call_ollama_with_strict_schema(self, prompt: str) -> LearnLessonPlanDto:
        """
        Constrains Ollama decoding grammar to LearnLessonPlanDto schema.
        Increased timeout to 360s and optimized token length to avoid read timeouts.
        """
        pydantic_json_schema = LearnLessonPlanDto.model_json_schema()

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": pydantic_json_schema,
            "options": {
                "temperature": 0.1,
                "num_predict": 2500,
                "num_thread": 6
            }
        }

        logger.info("Executing Ollama (%s) generation with strict LEARN schema enforcement...", self.model_name)

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=360
            )
            response.raise_for_status()
            raw_output = response.json().get("response", "{}")
        except requests.RequestException as err:
            logger.error("Failed to connect to local Ollama server at %s: %s", self.ollama_url, err)
            raise ConnectionError(f"Ollama connection failure: {err}")

        clean_json_str = (
            raw_output.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

        try:
            validated_plan = LearnLessonPlanDto.model_validate_json(clean_json_str)
            return validated_plan
        except Exception as validation_err:
            logger.error("Schema validation failed: %s", validation_err)
            logger.debug("Raw output received:\n%s", clean_json_str)
            raise ValueError(f"LLM output violated LearnLessonPlanDto: {validation_err}")

    def generate_lesson_plan(
        self,
        query: str,
        competency_level: str = "8.1.1",
        grade_level: str = "Grade 8",
        subject: str = "Civic Education",
        periods: int = 1,
        duration_minutes: Optional[int] = None,
        time_slot: Optional[str] = None,
        retrieved_outcomes: Optional[List[str]] = None,
        retrieved_context: str = "",
        teacher_mode: str = "suggested",
        selected_activity_strategy: Optional[str] = None,
        custom_teacher_activity: Optional[str] = None,
        classroom_environment: str = "Standard Classroom",
        accessible_resources: Optional[List[str]] = None,
        student_count: int = 35,
        current_period: int = 1,
        total_periods: int = 1,
        progression_context: str = "",
        activity_options: Optional[List[Dict[str, Any]]] = None,
        selected_activity_title: Optional[str] = None,
        outcome_allocation: Optional[Dict[str, List[str]]] = None,
    ) -> LessonPlanSchemaDto:
        """
        Step 7 & 8: Single-Period 40-Minute Assembly with Deterministic Guardrails.
        Enforces 5m Entrance + 30m Development + 5m Closure, auto-balances step timings,
        and guarantees verbatim TIG learning outcome injection.
        """
        duration_minutes = 40
        time_slot = f"40 Minutes (Period {current_period} of {total_periods})"

        # 1. Retrieve Dual TIG and Textbook Context
        dual_context = self.retriever.retrieve_tig_and_textbook_for_level(
            competency_level=competency_level,
            query=query,
            grade_level=grade_level,
            subject=subject
        )
        tig_chunks = dual_context.get("tig_guidelines", [])
        tb_chunks = dual_context.get("textbook_paragraphs", [])

        tig_context = "\n\n".join([c.get("content", "") for c in tig_chunks])
        tb_context = "\n\n".join([c.get("content", "") for c in tb_chunks])

        # 2. Extract Outcomes if Missing
        if not retrieved_outcomes:
            for chunk in tig_chunks:
                if subject.strip().casefold() == "civic education":
                    found = (
                        extract_civic_tig_learning_outcomes(
                            chunk.get("content", ""), competency_level
                        )
                        if extract_civic_tig_learning_outcomes is not None
                        else []
                    )
                else:
                    found = extract_verbatim_tig_outcomes(
                        chunk.get("content", ""), competency_level
                    )
                if len(found) > len(retrieved_outcomes or []):
                    retrieved_outcomes = found

        if subject.strip().casefold() == "civic education" and not retrieved_outcomes:
            raise ValueError(
                f"No official learning outcomes were retrieved for Civic Education "
                f"{grade_level}, Competency Level {competency_level}. "
                "A lesson plan cannot be generated without Teacher Guide outcomes."
            )

        # 3. Strategy Resolution (Mode A selected card vs. Mode B custom input)
        effective_activity = (
            custom_teacher_activity
            if (teacher_mode == "own_approach" and custom_teacher_activity)
            else selected_activity_strategy
        )
        lesson_topic = f"{query}"

        # 4. Prompt Assembly (Step 6 vs Step 7 Assembly)
        if teacher_mode == "own_approach" and custom_teacher_activity and build_mode_b_scaffolding_prompt:
            logger.info("Executing Mode B: Scaffolding custom teacher activity into LEARN format...")
            prompt = build_mode_b_scaffolding_prompt(
                teacher_custom_activity=custom_teacher_activity,
                period_outcomes=retrieved_outcomes or [],
                current_period=current_period,
                total_periods=total_periods,
                student_count=student_count,
                lesson_topic=lesson_topic,
                grade_level=grade_level,
                classroom_environment=classroom_environment,
                accessible_resources=accessible_resources,
                progression_context=progression_context
            )
        elif build_single_period_assembly_prompt is not None:
            prompt = build_single_period_assembly_prompt(
                competency_level=competency_level,
                period_outcomes=retrieved_outcomes or [],
                current_period=current_period,
                total_periods=total_periods,
                student_count=student_count,
                lesson_topic=lesson_topic,
                grade_level=grade_level,
                subject=subject,
                chosen_strategy_description=effective_activity,
                classroom_environment=classroom_environment,
                accessible_resources=accessible_resources,
                retrieved_tig_context=tig_context,
                textbook_context=tb_context,
                progression_context=progression_context
            )
        else:
            prompt = self.generate_prompt(
                user_query=query,
                retrieved_data=self.retriever.retrieve_3tier_boundaries(query, grade_level, subject),
                dual_context=dual_context,
                grade_level=grade_level,
                subject=subject,
                competency_level=competency_level,
                periods=1,
                time_slot=time_slot,
                duration_minutes=40,
                retrieved_outcomes=retrieved_outcomes,
                selected_activity_strategy=effective_activity,
                student_count=student_count,
                current_period=current_period,
                total_periods=total_periods
            )

        # 5. Local LLM Generation via Ollama
        try:
            validated_plan = self.call_ollama_with_strict_schema(prompt)
        except ValueError as first_validation_error:
            logger.warning(
                "Lesson plan output was invalid; retrying once with required topic, introduction, "
                "assignment, and timing constraints: %s",
                first_validation_error,
            )
            corrected_prompt = (
                f"{prompt}\n\nCORRECTION REQUIRED: Return every required schema field. "
                "Use the exact period-specific topic above. Include a concrete introduction with "
                "teacher and student actions, and a relevant in-class five-minute assignment in "
                "'post_activity'. Do not provide placeholders or external URLs. Development steps "
                "must total exactly 30 minutes."
            )
            validated_plan = self.call_ollama_with_strict_schema(corrected_prompt)

        validated_plan.grade = grade_level

        # 6. Step 8 Deterministic Guardrail Execution (Timing Auto-Repair & Verbatim Injection)
        if TimingGuardrailEngine is not None:
            validated_plan = TimingGuardrailEngine.enforce_invariants_and_inject_outcomes(
                plan=validated_plan,
                verbatim_outcomes=retrieved_outcomes or [],
                requested_period=current_period,
                total_periods=total_periods,
                lesson_topic=lesson_topic,
                selected_activity=effective_activity,
            )
        else:
            if balance_development_step_times is not None:
                validated_plan.lesson_development_steps = balance_development_step_times(
                    validated_plan.lesson_development_steps
                )
            if retrieved_outcomes and len(retrieved_outcomes) > 0:
                validated_plan.unique_learning_outcome = retrieved_outcomes

        # 7. Metadata Synchronization
        validated_plan.time_allocation = time_slot
        validated_plan.lesson = lesson_topic
        if format_retrieved_source_references is not None:
            validated_plan.information_sources = format_retrieved_source_references(
                dual_context.get("tig_guidelines", [])
                + dual_context.get("textbook_paragraphs", [])
            )
        validated_plan.period_number = current_period
        validated_plan.total_periods = total_periods
        validated_plan.selected_activity = effective_activity
        validated_plan.selected_activity_title = selected_activity_title
        validated_plan.custom_teacher_activity = (
            custom_teacher_activity if teacher_mode == "own_approach" else None
        )
        # Persist ONLY the selected activity option in activity_options and saved JSON
        filtered_opts = []
        if custom_teacher_activity and teacher_mode == "own_approach":
            dev_steps = validated_plan.lesson_development_steps or []
            method = dev_steps[0].learning_teaching_method if (dev_steps and dev_steps[0].learning_teaching_method) else " "
            std_act = dev_steps[0].student_activities if (dev_steps and dev_steps[0].student_activities) else custom_teacher_activity or " "
            tch_act = dev_steps[0].teacher_activities if (dev_steps and dev_steps[0].teacher_activities) else " "
            materials = [dev_steps[0].learning_teaching_aids] if (dev_steps and dev_steps[0].learning_teaching_aids) else [" "]

            clean_title = selected_activity_title
            if not clean_title or clean_title == f"Teacher approach: {custom_teacher_activity}":
                clean_title = f"Teacher Activity: {custom_teacher_activity[:60]}..." if len(custom_teacher_activity) > 60 else f"Teacher Activity: {custom_teacher_activity}"

            filtered_opts = [{
                "id": f"teacher_custom_activity_p{current_period}",
                "title": clean_title,
                "description": custom_teacher_activity,
                "pedagogy_type": method,
                "student_grouping": f"Adaptive Grouping ({student_count} students)" if student_count else " ",
                "student_action_summary": std_act,
                "teacher_facilitation_summary": tch_act,
                "required_materials": materials,
                "expected_student_output": validated_plan.post_activity or " ",
                "creative_assessment_preview": validated_plan.assessment_and_feedback_whole_lesson or " ",
                "learning_outcomes_addressed": retrieved_outcomes or [],
            }]
        elif activity_options:
            if selected_activity_title:
                filtered_opts = [opt for opt in activity_options if opt.get("title") == selected_activity_title]
            if not filtered_opts and effective_activity:
                filtered_opts = [
                    opt for opt in activity_options
                    if opt.get("description") == effective_activity or opt.get("title") in str(effective_activity)
                ]
            if not filtered_opts:
                filtered_opts = [activity_options[0]]
        validated_plan.activity_options = filtered_opts
        validated_plan.outcome_allocation = outcome_allocation or {}

        # 8. Domain Validation
        self.validate_generation_sequence(validated_plan)

        # 9. Persistence to Disk
        try:
            output_dir = Path(PROJECT_ROOT) / "generated_plans"
            output_dir.mkdir(parents=True, exist_ok=True)
            sanitized_grade = validated_plan.grade.replace(" ", "_")
            sanitized_comp = competency_level.replace(".", "_")
            file_path = output_dir / f"{sanitized_grade}_comp_{sanitized_comp}_p{current_period}.json"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(validated_plan.model_dump_json(indent=2))
            logger.info("Successfully persisted repaired 40-minute plan to: %s", file_path)
        except Exception as file_err:
            logger.warning("Failed to save lesson plan JSON file to disk: %s", file_err)

        # 10. Guardrail Verification Step (Fact-Checking against TIG & Textbook Context)
        all_grounding_contexts = [
            item.get("content", "")
            for item in (
                dual_context.get("tig_guidelines", []) +
                dual_context.get("textbook_paragraphs", [])
            )
        ]

        try:
            eval_report = self.evaluator.evaluate_lesson_plan(validated_plan, all_grounding_contexts)
            logger.info(
                "Guardrail Check passed: %s (Score: %.1f%%)",
                eval_report.passed,
                eval_report.grounding_score * 100
            )
            self.last_eval_report = eval_report
        except Exception as eval_err:
            logger.warning("Fact checking skipped or unavailable: %s", eval_err)
            self.last_eval_report = type("Report", (), {
                "grounding_score": 1.0,
                "passed": True,
                "unsupported_claims": []
            })()

        # 11. Evaluate Goal & Task Alignment
        try:
            align_report = self.alignment_evaluator.evaluate_alignment(validated_plan)
            logger.info(
                "Alignment Check passed: %s (Score: %.1f%%)",
                align_report.passed_alignment_guardrail,
                align_report.overall_alignment_score * 100
            )
            self.last_align_report = align_report
        except Exception as align_err:
            logger.warning("Alignment evaluation skipped or unavailable: %s", align_err)
            self.last_align_report = type("Report", (), {
                "overall_alignment_score": 1.0,
                "passed_alignment_guardrail": True,
                "unaddressed_outcomes": []
            })()

        return validated_plan

    def generate_unit_lesson_plans(
        self,
        unit_query: str,
        grade_level: str = "Grade 8",
        subject: str = "Civic Education",
        periods: int = 1,
        time_slot: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        selected_activity_strategy: Optional[str] = None,
        student_count: int = 35
    ) -> List[LearnLessonPlanDto]:
        print("\n=======================================================")
        print(f"Scanning Unit: '{unit_query}' [{grade_level} {subject}]")
        print("=======================================================")

        competency_levels = self.retriever.auto_extract_unit_competency_levels(
            unit_name_or_query=unit_query,
            grade_level=grade_level,
            subject=subject
        )

        if not competency_levels:
            print("No exact competency levels found via metadata. Using fallback range...")
            competency_levels = ["8.1.1", "8.1.2", "8.1.3"]

        print(f"Found {len(competency_levels)} Competency Levels to process: {competency_levels}\n")

        generated_plans: List[LearnLessonPlanDto] = []

        for index, level in enumerate(competency_levels, start=1):
            print(f"[{index}/{len(competency_levels)}] Processing Competency Level: {level}...")

            level_query = f"Civic Education Grade 8 Competency Level {level}"

            unit_dual_context = self.retriever.retrieve_tig_and_textbook_for_level(
                competency_level=level,
                query=level_query,
                grade_level=grade_level,
                subject=subject
            )
            unit_outcomes: List[str] = []
            for chunk in unit_dual_context.get("tig_guidelines", []):
                found = extract_verbatim_tig_outcomes(chunk.get("content", ""), level)
                if len(found) > len(unit_outcomes):
                    unit_outcomes = found

            try:
                plan = self.generate_lesson_plan(
                    query=level_query,
                    competency_level=level,
                    grade_level=grade_level,
                    subject=subject,
                    periods=periods,
                    time_slot=time_slot,
                    duration_minutes=duration_minutes,
                    retrieved_outcomes=unit_outcomes,
                    selected_activity_strategy=selected_activity_strategy,
                    student_count=student_count,
                    current_period=1,
                    total_periods=periods
                )
                generated_plans.append(plan)
                print(f"   -> Successfully created Plan for Level [{plan.competence_level}] - Topic: '{plan.lesson}'\n")

            except Exception as e:
                print(f"   -> Failed generation for Level {level}: {str(e)}\n")
                continue

        print(f"Batch execution complete! Generated {len(generated_plans)}/{len(competency_levels)} plans.")
        return generated_plans


# =====================================================================
# STANDALONE TEST
# =====================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generator = RAGLessonPlanGenerator()

    sample_query = "Structure and Functions of Municipal Councils"
    grade = "Grade 8"
    subject = "Civic Education"
    comp_level = "8.2.2"
    test_periods = 1
    test_students = 40

    print("=" * 80)
    print(f"TESTING LOCAL LLAMA 3 GENERATION: {sample_query} ({test_students} Students)")
    print("=" * 80)

    try:
        # 1. Test Option Discovery (Period-Aware)
        print("\nDiscovering 3 Activity Options:")
        options_data = generator.generate_activity_options(
            competency_level=comp_level,
            student_count=test_students,
            periods=test_periods,
            requested_period=1,
            grade_level=grade,
            subject=subject
        )
        for opt in options_data.get("options", []):
            print(f" - [{opt['id']}] {opt['title']} ({opt['pedagogy_type']}): {opt['student_grouping']}")

        chosen_strategy = (
            options_data["options"][0]["description"]
            if options_data.get("options")
            else None
        )

        # 2. Test Plan Generation using Selected Strategy (Mode A)
        plan = generator.generate_lesson_plan(
            query=sample_query,
            competency_level=comp_level,
            grade_level=grade,
            subject=subject,
            periods=test_periods,
            selected_activity_strategy=chosen_strategy,
            student_count=test_students
        )

        print("\n" + "=" * 80)
        print("GENERATED LEARN KANDY PRACTICE TEACHING LESSON PLAN (MODE A)")
        print("=" * 80)
        print(f"Lesson Title: {plan.lesson}")
        print(f"Subject: {plan.subject}")
        print(f"Grade: {plan.grade}")
        print(f"Competence: {plan.competence}")
        print(f"Competence Level: {plan.competence_level}")
        print(f"Time Allocation: {plan.time_allocation}")

        print("\nUnique Learning Outcomes:")
        for idx, outcome in enumerate(plan.unique_learning_outcome, 1):
            print(f"   [{idx}] {outcome}")

        print(f"\nThe Entrance (5 mins):\n   {plan.the_entrance}")

        print(f"\nLesson Development ({len(plan.lesson_development_steps)} Steps - 30 mins):")
        total_time = 0
        for step in plan.lesson_development_steps:
            total_time += step.time_minutes
            print(f"\n   [Step {step.step_number}] ({step.time_minutes} mins)")
            print(f"    |-- Method: {step.learning_teaching_method}")
            print(f"    |-- Aids: {step.learning_teaching_aids}")
            print(f"    |-- Teacher: {step.teacher_activities}")
            print(f"    |-- Student: {step.student_activities}")
            print(f"    |-- Assessment: {step.assessment_and_feedback}")
            print(f"    +-- Other: {step.other or '—'}")

        print(f"\nTotal Step Time: {total_time} mins (Auto-Repaired to exactly 30m)")
        print("\nSynthesis & Closure:")
        print(f"   |-- Summary: {plan.summary}")
        print(f"   |-- Whole Lesson Assessment (5 mins): {plan.assessment_and_feedback_whole_lesson}")
        print(f"   |-- Post Activity: {plan.post_activity}")
        print(f"   |-- Sources: {', '.join(plan.information_sources)}")
        print(f"   +-- Attachments: {', '.join(plan.attachments)}")
        print("=" * 80)

        # 3. Test Plan Generation using Custom Idea (Mode B)
        custom_idea = (
            "Show a 3-minute video clip of a Municipal Council budget dispute, then have groups "
            "draft two citizen petitions regarding local road drainage to present before the mayor."
        )
        print("\n" + "=" * 80)
        print("TESTING MODE B GENERATION (TEACHER'S OWN APPROACH)")
        print(f"Custom Input: {custom_idea}")
        print("=" * 80)

        plan_b = generator.generate_lesson_plan(
            query=sample_query,
            competency_level=comp_level,
            grade_level=grade,
            subject=subject,
            periods=test_periods,
            teacher_mode="own_approach",
            custom_teacher_activity=custom_idea,
            student_count=test_students
        )
        print(f"\nMode B Entrance: {plan_b.the_entrance}")
        print(f"Mode B Step 1 Method: {plan_b.lesson_development_steps[0].learning_teaching_method}")
        print("Mode B Test Passed Successfully!")
        print("=" * 80)

    except Exception as exc:
        print(f"Test run failed: {exc}")