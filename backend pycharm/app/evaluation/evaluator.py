import os
import sys
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field
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

# Safe Import for LessonPlanSchema
try:
    from app.schemas.schema import LessonPlanSchema
except ModuleNotFoundError:
    try:
        from schemas.schema import LessonPlanSchema
    except ModuleNotFoundError:
        from schema import LessonPlanSchema

# Safe Import for External FactCheckReport (or fallback to local definition)
try:
    from app.schemas.evaluator_schema import FactCheckReport
except ModuleNotFoundError:
    try:
        from schemas.evaluator_schema import FactCheckReport
    except ModuleNotFoundError:
        try:
            from evaluator_schema import FactCheckReport
        except ModuleNotFoundError:
            FactCheckReport = None

# Initialize OpenAI client safely
_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=_api_key) if _api_key else None


# =====================================================================
# EVALUATION & GUARDRAIL SCHEMAS
# =====================================================================
class ClaimVerificationResult(BaseModel):
    claim: str = Field(..., description="Atomic claim extracted from the generated lesson plan")
    is_grounded: bool = Field(...,
                              description="Whether the claim is directly supported or derived from TIG/Textbook context")
    reason: str = Field(..., description="Explanation citing or summarizing the supporting context")


class InternalFactCheckReport(BaseModel):
    grounding_score: float = Field(..., description="Ratio of verified claims (0.0 - 1.0)")
    total_claims: int = Field(..., description="Total number of evaluated claims")
    verified_claims: int = Field(..., description="Number of grounded claims")
    unsupported_claims: List[str] = Field(default_factory=list,
                                          description="Claims flagged as unsupported/hallucinated")
    verifications: List[ClaimVerificationResult] = Field(default_factory=list,
                                                         description="Detailed list of verification results")
    passed: bool = Field(..., description="True if grounding_score >= score_threshold")


# Use external schema if available, otherwise use internal definition
ActiveFactCheckReport = FactCheckReport or InternalFactCheckReport


# =====================================================================
# RAG FACT-CHECKING & GROUNDING AGENT
# =====================================================================
class RAGFactCheckingAgent:
    """
    Guardrail Agent that audits whether a generated LEARN LessonPlanSchema
    is strictly grounded in the official Teacher Instructional Guide (TIG) and Textbook context.
    Measures RAG Faithfulness and prevents curriculum hallucinations.
    """

    def __init__(self, score_threshold: float = 0.85, model_name: str = "gpt-4o-mini"):
        self.score_threshold = score_threshold
        self.model_name = model_name

    def _extract_plan_text_for_evaluation(self, plan: LessonPlanSchema) -> str:
        """
        Extracts all core pedagogical content and teacher-student interactions
        from the LEARN structured lesson plan.
        """
        # Outcomes extraction
        outcomes_list = getattr(plan, "unique_learning_outcome", []) or getattr(plan, "learning_outcomes", [])
        formatted_outcomes = []
        for o in outcomes_list:
            if hasattr(o, "description"):
                formatted_outcomes.append(str(o.description))
            else:
                formatted_outcomes.append(str(o))
        outcomes_str = "; ".join(formatted_outcomes) if formatted_outcomes else "No explicit outcomes recorded"

        # Development steps extraction
        steps_list = getattr(plan, "lesson_development_steps", []) or getattr(plan, "procedures", [])
        step_lines = []
        for s in steps_list:
            step_no = getattr(s, "step_number", getattr(s, "step", "N/A"))
            t_act = getattr(s, "teacher_activities", getattr(s, "teacher_action", ""))
            s_act = getattr(s, "student_activities", getattr(s, "student_action", ""))
            method = getattr(s, "learning_teaching_method", getattr(s, "phase_title", "Direct Instruction"))
            aids = getattr(s, "learning_teaching_aids", "Standard aids")
            assess = getattr(s, "assessment_and_feedback", "")

            step_lines.append(
                f"  - Step {step_no}: Method: {method} | Aids: {aids} | Teacher: {t_act} | Student: {s_act} | Assessment: {assess}"
            )
        steps_str = "\n".join(step_lines) if step_lines else "No sequential development steps recorded"

        competence = getattr(plan, "competence", getattr(plan, "educational_goal_or_standard", "General"))
        competence_level = getattr(plan, "competence_level", "General")
        topic = getattr(plan, "lesson_topic", getattr(plan, "topic", getattr(plan, "title", "Civic Education Lesson")))
        entrance = getattr(plan, "the_entrance", "Introduction phase")
        summary = getattr(plan, "summary", "")
        post_activity = getattr(plan, "post_activity", "Homework/Extension")
        whole_assessment = getattr(plan, "assessment_and_feedback_whole_lesson", "")

        return f"""
Competence: {competence}
Competence Level: {competence_level}
Lesson Topic: {topic}
Unique Learning Outcomes: {outcomes_str}
The Entrance (3-5 mins): {entrance}
Lesson Development Steps:
{steps_str}
Summary: {summary}
Whole Lesson Assessment: {whole_assessment}
Post Activity: {post_activity}
"""

    def evaluate_lesson_plan(
            self,
            plan: LessonPlanSchema,
            retrieved_contexts: List[Union[Dict[str, Any], str]]
    ) -> InternalFactCheckReport:
        """
        Decomposes the lesson plan into atomic claims and cross-checks them against
        retrieved TIG guidelines and textbook paragraphs.
        """
        # 1. Format reference contexts (handles dictionaries or raw strings)
        reference_text_parts = []
        for idx, ctx in enumerate(retrieved_contexts, 1):
            if isinstance(ctx, dict):
                src = ctx.get("source", f"Reference Source {idx}")
                doc_type = ctx.get("doc_type", "Reference")
                content = ctx.get("content", "")
                if content.strip():
                    reference_text_parts.append(f"[{doc_type.upper()} | Source: {src}]:\n{content.strip()}")
            elif isinstance(ctx, str) and ctx.strip():
                reference_text_parts.append(f"[REFERENCE DOC {idx}]:\n{ctx.strip()}")

        combined_context = "\n\n".join(
            reference_text_parts) if reference_text_parts else "NO OFFICIAL CURRICULUM CONTEXT PROVIDED"
        plan_text = self._extract_plan_text_for_evaluation(plan)

        # 2. Construct evaluation prompt
        evaluation_prompt = f"""
You are an expert curriculum compliance auditor evaluating a Sri Lankan School Lesson Plan.
Your task is to verify whether the Generated Lesson Plan is strictly grounded in the Official TIG and Textbook Context.

=== OFFICIAL TIG & TEXTBOOK CONTEXT ===
{combined_context}
======================================

=== GENERATED LESSON PLAN TO AUDIT ===
{plan_text}
======================================

AUDIT INSTRUCTIONS:
1. Extract 5 to 10 key factual and pedagogical statements from the lesson plan (learning concepts, competency codes, teacher activity explanations, definitions, and student tasks).
2. For each claim, determine whether it is supported or directly derived from the official context.
3. Mark `is_grounded: true` if the concept is aligned with the syllabus topics, level boundaries, and pedagogical guidance.
4. Mark `is_grounded: false` if it introduces external, hallucinated, factually inaccurate, or out-of-scope concepts.
5. Provide a short reason citing evidence from the context.
"""

        class VerificationResponse(BaseModel):
            verifications: List[ClaimVerificationResult]

        # 3. Perform Structured Guardrail Evaluation
        response = client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a rigorous educational compliance and fact-checking evaluator."},
                {"role": "user", "content": evaluation_prompt}
            ],
            response_format=VerificationResponse
        )

        results: List[ClaimVerificationResult] = response.choices[0].message.parsed.verifications

        total_claims = len(results)
        verified_count = sum(1 for r in results if r.is_grounded)
        unsupported = [r.claim for r in results if not r.is_grounded]

        grounding_score = (verified_count / total_claims) if total_claims > 0 else 1.0
        passed = grounding_score >= self.score_threshold

        return InternalFactCheckReport(
            grounding_score=round(grounding_score, 2),
            total_claims=total_claims,
            verified_claims=verified_count,
            unsupported_claims=unsupported,
            verifications=results,
            passed=passed
        )


# =====================================================================
# STANDALONE TEST
# =====================================================================
if __name__ == "__main__":
    evaluator = RAGFactCheckingAgent(score_threshold=0.85)

    # Sample LEARN structured lesson plan for testing
    sample_plan = LessonPlanSchema(
        page_no="01",
        lesson_plan_number="01",
        date="2026-09-01",
        grade="Grade 8",
        subject="Civic Education",
        time_allocation="40 Minutes (1 Period)",
        competence="Competency 8.0: Explores democratic governance structures.",
        competence_level="8.1.1: Identifies the origins and key features of direct democracy.",
        lesson_topic="Features of Direct Democracy in Ancient Athens",
        unique_learning_outcome=[
            "Define the concept of direct democracy using Athens as an example.",
            "Identify key differences between direct voting and representative decision making."
        ],
        the_entrance="Teacher asks: 'If every single student voted on every rule in school, how would it work?' Activates prior knowledge.",
        lesson_development_steps=[
            {
                "step_number": 1,
                "learning_teaching_method": "Direct Instruction with Chart",
                "learning_teaching_aids": "Athenian Assembly Wall Chart",
                "teacher_activities": "Explains the Athenian assembly (Ekklesia) where adult citizens voted directly.",
                "student_activities": "Notes down the key governance councils in exercise books.",
                "assessment_and_feedback": "Oral questions to 2 students on who qualified as a citizen.",
                "time_minutes": "15 mins",
                "other": "Write core terms on board."
            },
            {
                "step_number": 2,
                "learning_teaching_method": "Small Group Inquiry",
                "learning_teaching_aids": "Work Card Handout",
                "teacher_activities": "Distributes scenario cards comparing direct voting vs elected representatives.",
                "student_activities": "Discuss in groups of 4 and summarize advantages and limitations.",
                "assessment_and_feedback": "Teacher circulates and reviews group points.",
                "time_minutes": "15 mins",
                "other": "Workstation seating."
            }
        ],
        summary="Consolidates that direct democracy allowed direct participation in small populations like Athens.",
        assessment_and_feedback_whole_lesson="3-question formative exit ticket on direct democracy features.",
        post_activity="Record how family or village elders make decisions in community groups.",
        information_sources=["Teacher Instructional Guide Grade 8", "Civic Education Textbook Grade 8"],
        attachments=["Work Card 1", "Exit Ticket Rubric"],
        reflection="Pending lesson delivery."
    )

    sample_contexts = [
        {
            "source": "Grade 8 Civic Education TIG",
            "doc_type": "teacher_guide",
            "content": "Competency Level 8.1.1: Direct democracy in Ancient Athens where citizens directly participated in the Ekklesia (Assembly) to pass laws."
        },
        {
            "source": "Grade 8 Civic Education Textbook",
            "doc_type": "textbook",
            "content": "In ancient Athens, citizens gathered in open assemblies to cast votes directly. However, in modern large populations, representative democracy is adopted."
        }
    ]

    print("=" * 80)
    print("🛡️ RUNNING RAG FACT-CHECKING GUARDRAIL EVALUATION")
    print("=" * 80)

    report = evaluator.evaluate_lesson_plan(sample_plan, sample_contexts)

    print(f"📊 Grounding Score: {report.grounding_score:.2f} (Threshold: {evaluator.score_threshold})")
    print(f"✅ Passed Guardrail: {report.passed}")
    print(f"📈 Total Claims Audited: {report.total_claims} | Verified: {report.verified_claims}")

    print("\n🔍 Claim-by-Claim Breakdown:")
    for idx, v in enumerate(report.verifications, 1):
        status_icon = "✅" if v.is_grounded else "❌"
        print(f"  {status_icon} Claim {idx}: {v.claim}")
        print(f"     Reason: {v.reason}")

    if report.unsupported_claims:
        print(f"\n⚠️ Unsupported Claims Detected: {report.unsupported_claims}")
    else:
        print("\n🎉 Zero hallucinations detected! The lesson plan is 100% grounded in TIG guidelines.")
    print("=" * 80)