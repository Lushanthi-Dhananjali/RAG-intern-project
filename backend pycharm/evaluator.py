import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

from schema import LessonPlanSchema
from evaluator_schema import FactCheckReport

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class RAGFactCheckingAgent:
    """
    Evaluation Agent that verifies generated lesson plan claims against retrieved reference docs.
    Measures RAG Faithfulness & detects hallucinations.
    """

    def __init__(self, score_threshold: float = 0.85):
        self.score_threshold = score_threshold

    def evaluate_lesson_plan(
            self,
            generated_plan: LessonPlanSchema,
            retrieved_contexts: List[Dict[str, Any]]
    ) -> FactCheckReport:
        """
        Decomposes generated lesson plan into key factual claims and cross-checks with context.
        """
        # 1. Format retrieved context as reference material
        reference_text = ""
        for idx, ctx in enumerate(retrieved_contexts, 1):
            reference_text += f"\n[Reference Doc {idx}] ({ctx['source']}):\n{ctx['content']}\n"

        # 2. Extract key generation statements
        plan_summary = (
            f"Title: {generated_plan.title}\n"
            f"Standard: {generated_plan.educational_goal_or_standard}\n"
            f"Learning Outcomes: {[o.description for o in generated_plan.learning_outcomes]}\n"
            f"Procedures Summary: {[f'{p.phase_title}: {p.teacher_action}' for p in generated_plan.procedures]}\n"
            f"Verification: {generated_plan.verification.formative_assessment}"
        )

        system_prompt = (
            "You are an impartial RAG Fact-Checking and Grounding Evaluator.\n"
            "Your job is to compare a Generated Lesson Plan against provided Reference Documents.\n"
            "1. Extract core factual claims regarding educational standards, topic concepts, and teacher instructions.\n"
            "2. Verify whether EACH claim is supported by the Reference Documents.\n"
            "3. Calculate grounding_score = (supported_claims / total_claims).\n"
            "4. Set passed = True if grounding_score >= threshold, else False.\n"
            "5. List any ungrounded claims."
        )

        user_prompt = f"""
        EVALUATION THRESHOLD: {self.score_threshold}

        REFERENCE DOCUMENTS:
        {reference_text if reference_text.strip() else "NO REFERENCE DOCUMENTS PROVIDED"}

        GENERATED LESSON PLAN:
        {plan_summary}
        """

        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=FactCheckReport
        )

        return response.choices[0].message.parsed


# --- Demonstration Run ---
if __name__ == "__main__":
    from schema import LessonPlanSchema

    evaluator = RAGFactCheckingAgent(score_threshold=0.85)

    sample_plan = LessonPlanSchema(
        title="Grade 9 Civic Education - Fundamental Rights",
        subject="Civic Education",
        grade_level="Grade 9",
        topic="Democratic Governance",
        educational_goal_or_standard="Grade 9 Civics Standard 9.1: Rights and Duties",
        learning_outcomes=[
            {"id": 1, "description": "Differentiate between fundamental rights and civic duties."}
        ],
        materials=[{"item_name": "Constitutional Extracts", "quantity": "1 per pair"}],
        procedures=[{
            "step_number": 1,
            "phase_title": "Direct Instruction",
            "duration_minutes": 15,
            "teacher_action": "Explains rights guaranteed under Article 10 of Constitution.",
            "student_action": "Take notes."
        }],
        verification={
            "formative_assessment": "Exit ticket checking 1 right and 1 duty.",
            "alignment_check": "Exit ticket tests Learning Outcome 1."
        }
    )

    sample_contexts = [{
        "source": "ChromaDB Knowledge Base",
        "content": "Grade 9 Civics Standard 9.1 mandates teaching fundamental constitutional rights and citizen duties."
    }]

    report = evaluator.evaluate_lesson_plan(sample_plan, sample_contexts)

    print("\n📊 Fact-Checking Evaluation Report:")
    print(f"Grounding Score: {report.grounding_score:.2f} (Threshold: 0.85)")
    print(f"Passed Guardrail: {report.passed}")
    print(f"Explanation: {report.explanation}")