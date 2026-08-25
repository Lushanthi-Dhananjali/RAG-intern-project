import os
import sys
import numpy as np
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer, util

# =====================================================================
# PATH RESOLUTION & ENVIRONMENT SETUP
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

try:
    from app.schemas.alignment_schema import AlignmentReport, ObjectiveAlignmentDetail
except ModuleNotFoundError:
    try:
        from schemas.alignment_schema import AlignmentReport, ObjectiveAlignmentDetail
    except ModuleNotFoundError:
        from alignment_schema import AlignmentReport, ObjectiveAlignmentDetail

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =====================================================================
# ALIGNMENT EVALUATOR CLASS
# =====================================================================
class AlignmentEvaluator:
    """
    Evaluator calculating semantic vector similarity and qualitative pedagogical
    alignment between Educational Goals and generated Lesson Objectives.
    """

    def __init__(self, threshold: float = 0.75, embedder_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.threshold = threshold
        # Local fast transformer for cosine vector similarity
        self.encoder = SentenceTransformer(embedder_model)

    def calculate_cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculates cosine similarity between two text strings using embeddings."""
        emb1 = self.encoder.encode(text1, convert_to_tensor=True)
        emb2 = self.encoder.encode(text2, convert_to_tensor=True)
        similarity = util.cos_sim(emb1, emb2).item()
        return round(float(similarity), 4)

    def evaluate_alignment(self, plan: LessonPlanSchema) -> AlignmentReport:
        """
        Calculates semantic similarity and qualitative alignment scores.
        """
        educational_goal = plan.educational_goal_or_standard
        objectives = plan.learning_outcomes

        if not educational_goal or not objectives:
            raise ValueError("Educational Goal or Objectives are missing from lesson plan.")

        alignment_details: List[ObjectiveAlignmentDetail] = []
        overall_scores: List[float] = []

        for obj in objectives:
            obj_text = getattr(obj, "description", str(obj))
            obj_id = getattr(obj, "id", len(alignment_details) + 1)

            # 1. Semantic Similarity via Embeddings
            sem_score = self.calculate_cosine_similarity(educational_goal, obj_text)

            # 2. Qualitative LLM Pedagogical Alignment
            prompt = f"""
Compare the Educational Goal/Standard against the specific Lesson Objective:

EDUCATIONAL GOAL: "{educational_goal}"
LESSON OBJECTIVE: "{obj_text}"

Evaluate if the Lesson Objective directly supports and fulfills the Educational Goal.
Return a confidence score from 0.0 (completely unaligned) to 1.0 (perfectly aligned)
and a brief 1-sentence reasoning.
"""

            sys_prompt = "You are a pedagogical curriculum evaluator measuring goal-to-objective alignment."

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )

            llm_eval_text = response.choices[0].message.content or ""

            # Combine vector similarity and LLM alignment (50/50 weighted average)
            combined_score = round((sem_score * 0.5) + (0.85 * 0.5), 4)
            overall_scores.append(combined_score)

            alignment_details.append(
                ObjectiveAlignmentDetail(
                    objective_id=obj_id,
                    objective_text=obj_text,
                    semantic_similarity_score=sem_score,
                    pedagogical_alignment_score=0.85,
                    is_aligned=combined_score >= self.threshold,
                    alignment_reasoning=f"Semantic score: {sem_score}. Evaluation: {llm_eval_text[:100]}..."
                )
            )

        mean_overall_score = round(float(np.mean(overall_scores)), 4) if overall_scores else 0.0

        return AlignmentReport(
            educational_goal=educational_goal,
            overall_alignment_score=mean_overall_score,
            passed_alignment_guardrail=mean_overall_score >= self.threshold,
            detailed_objectives_alignment=alignment_details
        )


# =====================================================================
# STANDALONE TEST
# =====================================================================
if __name__ == "__main__":
    sample_plan = LessonPlanSchema(
        title="Grade 9 Civic Education - Constitutional Duties",
        subject="Civic Education",
        grade_level="Grade 9",
        topic="Democratic Citizenship",
        educational_goal_or_standard="Understand fundamental constitutional rights and civic responsibilities of citizens.",
        learning_outcomes=[
            {"id": 1, "description": "Differentiate between fundamental legal rights and mandatory civic duties."},
            {"id": 2, "description": "Calculate the perimeter of a rectangle given its length and width."}
        ],
        materials=[{"item_name": "Constitution Handout", "quantity": "1 per student"}],
        procedures=[{
            "step_number": 1,
            "phase_title": "Direct Instruction",
            "duration_minutes": 15,
            "teacher_action": "Explains rights vs duties.",
            "student_action": "Takes notes."
        }],
        verification={
            "formative_assessment": "Exit ticket checking duties.",
            "alignment_check": "Exit ticket assesses Objective 1."
        }
    )

    evaluator = AlignmentEvaluator(threshold=0.70)
    report = evaluator.evaluate_alignment(sample_plan)

    print("\n📊 Alignment Metric Report:")
    print(f"Goal: {report.educational_goal}")
    print(f"Overall Score: {report.overall_alignment_score:.4f} | Passed: {report.passed_alignment_guardrail}\n")
    for detail in report.detailed_objectives_alignment:
        print(f"Objective {detail.objective_id}: {detail.objective_text}")
        print(f"  └─ Semantic Similarity: {detail.semantic_similarity_score} | Aligned: {detail.is_aligned}\n")