import os
import sys
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

# =====================================================================
# PATH RESOLUTION & ENVIRONMENT SETUP
# Ensures smooth execution whether run directly or as a FastAPI module
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Import Schemas
try:
    from app.schemas.schema import LessonPlanSchema
except ModuleNotFoundError:
    try:
        from schemas.schema import LessonPlanSchema
    except ModuleNotFoundError:
        from schema import LessonPlanSchema

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
# MODEL & CLIENT CONFIGURATION
# =====================================================================
USE_QWEN_72B = False  # Set to True when using local/remote vLLM endpoint

if USE_QWEN_72B:
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="EMPTY"
    )
    MODEL_NAME = "Qwen/Qwen2-72B-Instruct-AWQ"
else:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    MODEL_NAME = "gpt-4o-mini"


# =====================================================================
# RAG LESSON PLAN GENERATOR
# =====================================================================

class RAGLessonPlanGenerator:
    """
    Activity-based, multi-grade bounded RAG lesson plan generation engine.
    Enforces practical student-centered tasks, chronobiological adaptation,
    strict timetable budgeting, and validation guardrails.
    """

    def __init__(self, chroma_path: Optional[str] = None):
        if chroma_path is None:
            chroma_path = os.path.join(PROJECT_ROOT, "chroma_db")

        self.retriever = MultiGradeBoundaryRetriever(chroma_path=chroma_path)
        self.evaluator = RAGFactCheckingAgent(score_threshold=0.85)
        self.alignment_evaluator = AlignmentEvaluator(threshold=0.75)

    def generate_prompt(
            self,
            user_query: str,
            retrieved_data: Dict[str, Any],
            grade_level: str,
            subject: str,
            time_slot: str = "Pre-Interval",
            duration_minutes: int = 40
    ) -> str:
        """Constructs an activity-centric pedagogical prompt with curriculum boundaries."""
        # Extract content from 3-tier boundary objects
        target_docs = "\n\n".join([
            f"[Target Comp: {item.get('competency', 'General')} | Source: {item.get('source', 'Unknown')}]\n{item.get('content', '')}"
            for item in retrieved_data.get("tier_1_target_content", [])
        ])

        prereq_docs = "\n\n".join([
            f"[Prerequisite Comp: {item.get('competency', 'General')}]\n{item.get('content', '')}"
            for item in retrieved_data.get("tier_2_prerequisites", [])
        ])

        upper_docs = "\n\n".join([
            f"[Upper Boundary Limit]\n{item.get('content', '')}"
            for item in retrieved_data.get("tier_3_upper_boundaries", [])
        ])

        exemplar_docs = "\n\n".join([
            f"[Exemplar Format: {item.get('source', 'Sample Plan')}]\n{item.get('content', '')}"
            for item in retrieved_data.get("practical_exemplars", [])
        ])

        prompt = f"""
You are an expert pedagogical designer creating an activity-based Civic Education lesson plan.

CURRICULUM BOUNDARY RULES:
- Target Grade: {grade_level} (Primary learning outcomes and procedures MUST focus exclusively on this standard).
- Prerequisite Baseline ({prereq_docs[:150]}...): Assume students already know basic concepts from previous grades; do NOT re-teach them from scratch.
- Upper Boundary Limit ({upper_docs[:150]}...): Do NOT introduce advanced concepts intended for higher grades.

PEDAGOGICAL & EXPERIENTIAL LEARNING RULES:
- Enforce active student participation and real-world practical actions.
- If teaching environmental topics, include hands-on outdoor field activities:
  * Waste sorting at source (Organic Compost, Plastic Bottles, Paper, Metal Tins).
  * Direct observation of water/soil pollution in the schoolyard.
  * Tree planting, soil preparation, and scheduled care.
  * Water conservation (inspecting dripping taps) and electricity audits (switching off unused appliances, using sunlight).
- Structure every procedure step with explicit 'teacher_action' (facilitating/guiding) and 'student_action' (observing/sorting/measuring).

TIMETABLE & CHRONOBIOLOGY CONSTRAINTS:
- Assigned Time Slot: {time_slot}
- Total Allocated Duration: {duration_minutes} minutes (Weekly total must fit standard 2 hours/week).
- Time Slot Strategy:
  * Early Morning: Foundational concepts & focused indoor discussion.
  * Pre-Interval (Fatigue/Hunger): High-engagement outdoor inspections and movement.
  * Post-Interval (Restlessness): Collaborative group practical tasks (sorting, planting).
  * End-of-Day: Interactive debriefs, role plays, and reflective wrap-up.

RETRIEVED TARGET CURRICULUM:
{target_docs or "Standard National Civic Education Curriculum Guidelines"}

PRACTICAL EXEMPLAR TEMPLATE:
{exemplar_docs or "Refer to standard experiential learning format."}

USER GENERATION REQUEST:
Subject: {subject}
Grade: {grade_level}
Topic / Goal: {user_query}
"""
        return prompt

    def validate_generation_sequence(self, plan: LessonPlanSchema) -> bool:
        """Validates that all sequence stages exist and contain valid data."""
        if not plan.educational_goal_or_standard or not plan.educational_goal_or_standard.strip():
            raise ValueError("Sequence Failure: Stage 1 (Educational Goal) is empty.")
        if not plan.learning_outcomes:
            raise ValueError("Sequence Failure: Stage 2 (Learning Outcomes) has no entries.")
        if not plan.materials:
            raise ValueError("Sequence Failure: Stage 3 (Materials) has no entries.")
        if not plan.procedures:
            raise ValueError("Sequence Failure: Stage 4 (Procedures) has no steps.")
        if not plan.verification or not plan.verification.formative_assessment.strip():
            raise ValueError("Sequence Failure: Stage 5 (Verification) has no formative assessment.")
        return True

    def generate_lesson_plan(
            self,
            query: str,
            grade_level: str = "Grade 8",
            subject: str = "Civic Education",
            time_slot: str = "Pre-Interval",
            duration_minutes: int = 40
    ) -> LessonPlanSchema:
        """
        Runs the full RAG generation pipeline with 3-tier multi-grade context retrieval,
        structured JSON formatting, and verification guardrails.
        """
        # Step 1: Retrieve 3-tier bounded context from ChromaDB
        retrieved_data = self.retriever.retrieve_3tier_boundaries(
            query=query,
            target_grade=grade_level,
            subject=subject
        )

        # Step 2: Build contextual prompt
        prompt = self.generate_prompt(
            user_query=query,
            retrieved_data=retrieved_data,
            grade_level=grade_level,
            subject=subject,
            time_slot=time_slot,
            duration_minutes=duration_minutes
        )

        print(f"⏳ Generating activity-based lesson plan for [{grade_level} - {subject}] ({time_slot})...")

        # Step 3: Call LLM with structured schema parsing
        response = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized curriculum design assistant that outputs strictly formatted, practical lesson plans."
                },
                {"role": "user", "content": prompt}
            ],
            response_format=LessonPlanSchema
        )
        plan = response.choices[0].message.parsed

        # Step 4: Validate Sequence Completeness
        self.validate_generation_sequence(plan)

        # Step 5: Fact-Checking Guardrail
        all_contexts = [
            item.get("content", "")
            for item in
            (retrieved_data.get("tier_1_target_content", []) + retrieved_data.get("practical_exemplars", []))
        ]
        eval_report = self.evaluator.evaluate_lesson_plan(plan, all_contexts)
        print(
            f"🛡️ Guardrail Check -> Grounding Score: {eval_report.grounding_score:.2f} | Passed: {eval_report.passed}")

        # Step 6: Alignment Metric Guardrail
        align_report = self.alignment_evaluator.evaluate_alignment(plan)
        print(
            f"🎯 Goal Alignment Score: {align_report.overall_alignment_score:.2f} | Passed: {align_report.passed_alignment_guardrail}")

        return plan


# =====================================================================
# STANDALONE TEST
# =====================================================================
if __name__ == "__main__":
    generator = RAGLessonPlanGenerator()
    test_query = "Protecting the environment: practical waste segregation, tree planting, and water saving"

    result = generator.generate_lesson_plan(
        query=test_query,
        grade_level="Grade 8",
        subject="Civic Education",
        time_slot="Pre-Interval",
        duration_minutes=40
    )

    print("\n" + "=" * 60)
    print("✅ EXPERIENTIAL LESSON PLAN GENERATED SUCCESSFULLY!")
    print(f"Title: {result.title}")
    print(f"Topic: {result.topic}")
    print(f"Goal: {result.educational_goal_or_standard}")
    print(f"Duration: {result.estimated_duration_minutes} mins")
    print(f"Total Outcomes: {len(result.learning_outcomes)}")
    print(f"Total Materials: {len(result.materials)}")
    print(f"Total Procedures: {len(result.procedures)}")