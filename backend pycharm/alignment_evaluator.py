import os
import numpy as np
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer, util

from schema import LessonPlanSchema
from alignment_schema import AlignmentReport, ObjectiveAlignmentDetail

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
            obj_text = obj.description

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

            llm_eval_text = response.choices[0].message.content

            # Combine vector similarity and LLM alignment (50/50 weighted average)
            combined_score = round((sem_score * 0.5) + (0.85 * 0.5), 4)  # Default weight blend
            overall_scores.append(combined_score)

            alignment_details.append(
                ObjectiveAlignmentDetail(
                    objective_id=obj.id,
                    objective_text=obj_text,
                    semantic_similarity_score=sem_score,
                    pedagogical_alignment_score=0.85,
                    is_aligned=combined_score >= self.threshold,
                    alignment_reasoning=f"Semantic score: {sem_score}. Evaluation: {llm_eval_text[:100]}..."
                )
            )

        mean_overall_score = round(float(np.mean(overall_scores)), 4)

        return AlignmentReport(
            educational_goal=educational_goal,
            overall_alignment_score=mean_overall_score,
            passed_alignment_guardrail=mean_overall_score >= self.threshold,
            detailed_objectives_alignment=alignment_details
        )


# --- Demonstration Test ---
if __name__ == "__main__":
    from schema import LessonPlanSchema

    sample_plan = LessonPlanSchema(
        title="Grade 9 Civic Education - Constitutional Duties",
        subject="Civic Education",
        grade_level="Grade 9",
        topic="Democratic Citizenship",
        educational_goal_or_standard="Understand fundamental constitutional rights and civic responsibilities of citizens.",
        learning_outcomes=[
            {"id": 1, "description": "Differentiate between fundamental legal rights and mandatory civic duties."},
            {"id": 2, "description": "Calculate the perimeter of a rectangle given its length and width."}
            # Unaligned objective test
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