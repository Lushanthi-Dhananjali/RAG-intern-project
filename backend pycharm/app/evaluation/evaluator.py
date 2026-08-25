import os
import sys
from typing import List, Dict, Any, Union, Optional
from dotenv import load_dotenv
from openai import OpenAI

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
    from app.schemas.evaluator_schema import FactCheckReport
except ModuleNotFoundError:
    try:
        from app.schemas.evaluator_schema import FactCheckingReport as FactCheckReport
    except ModuleNotFoundError:
        try:
            from schemas.evaluator_schema import FactCheckReport
        except ModuleNotFoundError:
            try:
                from evaluator_schema import FactCheckReport
            except ModuleNotFoundError:
                from evaluator_schema import FactCheckingReport as FactCheckReport

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =====================================================================
# RAG FACT-CHECKING AGENT
# =====================================================================
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
        retrieved_contexts: List[Union[Dict[str, Any], str]]
    ) -> FactCheckReport:
        """
        Decomposes generated lesson plan into key factual claims and cross-checks with context.
        """
        # 1. Format retrieved context as reference material (handles dicts or plain text strings)
        reference_text = ""
        for idx, ctx in enumerate(retrieved_contexts, 1):
            if isinstance(ctx, dict):
                src = ctx.get("source", "Reference Source")
                content = ctx.get("content", "")
                reference_text += f"\n[Reference Doc {idx}] ({src}):\n{content}\n"
            else:
                reference_text += f"\n[Reference Doc {idx}]:\n{ctx}\n"

        # 2. Extract key generation statements
        outcomes = [getattr(o, "description", str(o)) for o in generated_plan.learning_outcomes]
        procedures = [
            f"{getattr(p, 'phase_title', 'Step')}: {getattr(p, 'teacher_action', '')}"
            for p in generated_plan.procedures
        ]
        verification_text = (
            generated_plan.verification.formative_assessment
            if hasattr(generated_plan, "verification") and generated_plan.verification
            else "Standard verification"
        )

        plan_summary = (
            f"Title: {generated_plan.title}\n"
            f"Standard: {generated_plan.educational_goal_or_standard}\n"
            f"Learning Outcomes: {outcomes}\n"
            f"Procedures Summary: {procedures}\n"
            f"Verification: {verification_text}"
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


# =====================================================================
# STANDALONE TEST
# =====================================================================
if __name__ == "__main__":
    evaluator = RAGFactCheckingAgent(score_threshold=0.85)

    sample_plan = LessonPlanSchema(
        title="Grade 8 Civic Education - Environmental Protection",
        subject="Civic Education",
        grade_level="Grade 8",
        topic="Environmental Protection",
        educational_goal_or_standard="Grade 8 Civics Standard 8.1: Environmental Conservation",
        learning_outcomes=[
            {"id": 1, "description": "Identify methods of waste segregation and tree planting."}
        ],
        materials=[{"item_name": "Color-coded waste bins", "quantity": "4 bins"}],
        procedures=[{
            "step_number": 1,
            "phase_title": "Field Activity",
            "duration_minutes": 20,
            "teacher_action": "Guides students in categorizing waste into compost, plastics, and paper.",
            "student_action": "Sort waste items into designated bins."
        }],
        verification={
            "formative_assessment": "Group presentation of waste audit results.",
            "alignment_check": "Assesses knowledge of practical waste management."
        }
    )

    sample_contexts = [{
        "source": "Grade 8 Civic Education Teacher Guide",
        "content": "Competency 8.1 emphasizes practical waste segregation, maintaining compost pits, and schoolyard tree planting."
    }]

    report = evaluator.evaluate_lesson_plan(sample_plan, sample_contexts)

    print("\n📊 Fact-Checking Evaluation Report:")
    print(f"Grounding Score: {report.grounding_score:.2f} (Threshold: 0.85)")
    print(f"Passed Guardrail: {report.passed}")
    print(f"Explanation: {getattr(report, 'explanation', getattr(report, 'reasoning', 'Evaluation complete'))}")