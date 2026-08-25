import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

from schema import LessonPlanSchema
from evaluator import RAGFactCheckingAgent
from alignment_evaluator import AlignmentEvaluator

load_dotenv()

# =====================================================================
# MODEL & CLIENT CONFIGURATION
# Set USE_QWEN_72B to True if using vLLM/OpenRouter, or False for OpenAI
# =====================================================================
USE_QWEN_72B = False

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
# MULTI-GRADE BOUNDARY RETRIEVER
# =====================================================================

class MultiGradeRetriever:
    """
    Retrieves multi-grade curriculum boundaries from local ChromaDB:
    - Target Grade (Core competencies)
    - Lower Grade (Prerequisites baseline)
    - Upper Grade (Boundary limits to prevent syllabus creep)
    - Practical Exemplars (Hands-on reference templates)
    """

    def __init__(self, chroma_path: str = "./chroma_db", collection_name: str = "curriculum_syllabus"):
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def retrieve_bounded_context(
        self,
        query: str,
        grade_level: str = "Grade 8",
        subject: str = "Civic Education"
    ) -> Dict[str, List[str]]:
        # Map grade boundaries
        lower_grade = "Grade 7" if grade_level == "Grade 8" else None
        upper_grade = "Grade 9" if grade_level == "Grade 8" else None

        # 1. Target Core Curriculum
        target_res = self.collection.query(
            query_texts=[query],
            n_results=3,
            where={
                "$and": [
                    {"grade_level": grade_level},
                    {"subject": subject}
                ]
            }
        )

        # 2. Prerequisite Knowledge (Lower Grade)
        prereq_res = {"documents": [[]]}
        if lower_grade:
            prereq_res = self.collection.query(
                query_texts=[query],
                n_results=1,
                where={
                    "$and": [
                        {"grade_level": lower_grade},
                        {"subject": subject}
                    ]
                }
            )

        # 3. Upper Boundary (Next Grade limit)
        upper_res = {"documents": [[]]}
        if upper_grade:
            upper_res = self.collection.query(
                query_texts=[query],
                n_results=1,
                where={
                    "$and": [
                        {"grade_level": upper_grade},
                        {"subject": subject}
                    ]
                }
            )

        # 4. Hands-on / Experiential Exemplar Plan
        exemplar_res = self.collection.query(
            query_texts=[query],
            n_results=1,
            where={"category": "practical_exemplar"}
        )

        return {
            "target_context": target_res.get("documents", [[]])[0],
            "prerequisite_context": prereq_res.get("documents", [[]])[0],
            "upper_boundary_context": upper_res.get("documents", [[]])[0],
            "exemplar_context": exemplar_res.get("documents", [[]])[0]
        }


# =====================================================================
# RAG LESSON PLAN GENERATOR
# =====================================================================

class RAGLessonPlanGenerator:
    """
    Experiential, multi-grade bounded RAG generator.
    Enforces practical student-centered tasks, chronobiological adaptation,
    strict timetable budgeting, and validation guardrails.
    """

    def __init__(self):
        self.retriever = MultiGradeRetriever()
        self.evaluator = RAGFactCheckingAgent(score_threshold=0.85)
        self.alignment_evaluator = AlignmentEvaluator(threshold=0.75)

    def generate_prompt(
        self,
        user_query: str,
        retrieved_data: Dict[str, List[str]],
        grade_level: str,
        subject: str,
        time_slot: str = "Pre-Interval",
        duration_minutes: int = 40
    ) -> str:
        target_docs = "\n".join(retrieved_data.get("target_context", []))
        prereq_docs = "\n".join(retrieved_data.get("prerequisite_context", []))
        upper_docs = "\n".join(retrieved_data.get("upper_boundary_context", []))
        exemplar_docs = "\n".join(retrieved_data.get("exemplar_context", []))

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
        Runs the full RAG generation pipeline with multi-grade context retrieval,
        structured JSON formatting, and verification guardrails.
        """
        # Step 1: Retrieve bounded context from ChromaDB
        retrieved_data = self.retriever.retrieve_bounded_context(
            query=query,
            grade_level=grade_level,
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
        all_contexts = retrieved_data.get("target_context", []) + retrieved_data.get("exemplar_context", [])
        eval_report = self.evaluator.evaluate_lesson_plan(plan, all_contexts)
        print(f"🛡️ Guardrail Check -> Grounding Score: {eval_report.grounding_score:.2f} | Passed: {eval_report.passed}")

        # Step 6: Alignment Metric Guardrail
        align_report = self.alignment_evaluator.evaluate_alignment(plan)
        print(f"🎯 Goal Alignment Score: {align_report.overall_alignment_score:.2f} | Passed: {align_report.passed_alignment_guardrail}")

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
    print(f"Goal: {result.educational_goal_or_standard}")
    print(f"Duration: {result.estimated_duration_minutes} mins")
    print(f"Total Outcomes: {len(result.learning_outcomes)}")
    print(f"Total Materials: {len(result.materials)}")
    print(f"Total Procedures: {len(result.procedures)}")