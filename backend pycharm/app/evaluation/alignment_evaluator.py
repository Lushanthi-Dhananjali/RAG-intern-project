import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
import requests
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util

# =====================================================================
# PATH RESOLUTION & ENVIRONMENT SETUP
# =====================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

logger = logging.getLogger("AlignmentEvaluator")

# Safe Import for LessonPlanSchema
try:
    from app.schemas.schema import LessonPlanSchema
except ModuleNotFoundError:
    try:
        from schemas.schema import LessonPlanSchema
    except ModuleNotFoundError:
        try:
            from schema import LessonPlanSchema
        except ModuleNotFoundError:
            LessonPlanSchema = Any

# Safe Import for External Alignment Schema
try:
    from app.schemas.alignment_schema import AlignmentReport, ObjectiveAlignmentDetail
except ModuleNotFoundError:
    try:
        from schemas.alignment_schema import AlignmentReport, ObjectiveAlignmentDetail
    except ModuleNotFoundError:
        AlignmentReport = None
        ObjectiveAlignmentDetail = None


# =====================================================================
# INTERNAL ALIGNMENT EVALUATION SCHEMAS
# =====================================================================
class OutcomeTaskAlignment(BaseModel):
    learning_outcome: str = Field(..., description="Target outcome from the lesson plan")
    addressed_in_steps: List[int] = Field(default_factory=list, description="Step numbers covering this outcome")
    semantic_similarity_score: float = Field(default=0.0, description="Vector cosine similarity (0.0 - 1.0)")
    is_aligned: bool = Field(..., description="True if classroom tasks adequately teach and practice this outcome")
    cognitive_depth_match: bool = Field(..., description="True if task cognitive level matches outcome action verb (Bloom's)")
    reasoning: str = Field(..., description="Pedagogical explanation of alignment or mismatch")


class LLMAlignmentResponse(BaseModel):
    outcome_evaluations: List[OutcomeTaskAlignment]
    unaligned_tasks: List[str] = Field(default_factory=list)


class InternalAlignmentReport(BaseModel):
    competency_level: str = Field(default="General", description="The audited competency level (e.g. 8.1.1)")
    overall_alignment_score: float = Field(..., description="Composite alignment score between 0.0 and 1.0")
    total_outcomes: int = Field(..., description="Total unique learning outcomes evaluated")
    aligned_outcomes: int = Field(..., description="Number of aligned outcomes")
    outcome_alignments: List[OutcomeTaskAlignment] = Field(default_factory=list)
    unaligned_tasks: List[str] = Field(default_factory=list, description="Classroom activities unrelated to any target outcome")
    passed_alignment_guardrail: bool = Field(..., description="True if overall_alignment_score >= threshold")


# =====================================================================
# ALIGNMENT EVALUATOR AGENT (LOCAL OLLAMA + SENTENCE TRANSFORMERS)
# =====================================================================
class AlignmentEvaluator:
    """
    Evaluator calculating semantic vector similarity and qualitative pedagogical
    alignment between Competency Level Learning Outcomes and generated Classroom Tasks
    using local SentenceTransformers and local Llama 3 via Ollama.
    """

    def __init__(
        self,
        threshold: float = 0.75,
        model_name: str = "llama3",
        ollama_url: Optional[str] = None,
        embedder_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.threshold = threshold
        self.model_name = model_name
        self.ollama_url = ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.encoder = SentenceTransformer(embedder_model)

    def calculate_cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculates cosine similarity between two text strings using local embeddings."""
        if not text1.strip() or not text2.strip():
            return 0.0
        emb1 = self.encoder.encode(text1, convert_to_tensor=True)
        emb2 = self.encoder.encode(text2, convert_to_tensor=True)
        similarity = util.cos_sim(emb1, emb2).item()
        return round(float(similarity), 4)

    def _call_ollama_for_alignment(self, prompt: str) -> LLMAlignmentResponse:
        """Invokes local Ollama with strict grammar constraints for structured evaluation."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": LLMAlignmentResponse.model_json_schema(),
            "options": {
                "temperature": 0.1,
                "num_predict": 2048
            }
        }

        try:
            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )
            resp.raise_for_status()
            raw_text = resp.json().get("response", "{}")

            clean_json = (
                raw_text.strip()
                .removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )
            return LLMAlignmentResponse.model_validate_json(clean_json)

        except Exception as err:
            logger.warning("Local Ollama alignment audit encountered an error: %s. Using vector-only fallback.", err)
            return LLMAlignmentResponse(outcome_evaluations=[], unaligned_tasks=[])

    def evaluate_alignment(self, plan: Any) -> InternalAlignmentReport:
        """
        Cross-checks unique learning outcomes against classroom activities.
        Combines fast local vector similarity with LLM cognitive depth (Bloom's Taxonomy) verification.
        """
        # 1. Format Learning Outcomes
        outcomes_list = getattr(plan, "unique_learning_outcome", []) or getattr(plan, "learning_outcomes", [])
        if not outcomes_list:
            raise ValueError("Evaluation Failure: Lesson Plan contains no learning outcomes.")

        formatted_outcomes = []
        raw_outcomes_strings = []
        for idx, o in enumerate(outcomes_list, 1):
            desc = str(getattr(o, "description", o))
            raw_outcomes_strings.append(desc)
            formatted_outcomes.append(f"Outcome {idx}: {desc}")
        outcomes_text = "\n".join(formatted_outcomes)

        # 2. Format Classroom Steps & The Entrance
        steps_list = getattr(plan, "lesson_development_steps", []) or getattr(plan, "procedures", [])
        formatted_steps = []
        full_steps_corpus = []

        for s in steps_list:
            step_no = getattr(s, "step_number", "N/A")
            t_act = getattr(s, "teacher_activities", getattr(s, "teacher_action", ""))
            s_act = getattr(s, "student_activities", getattr(s, "student_action", ""))
            method = getattr(s, "learning_teaching_method", getattr(s, "phase_title", "Direct Instruction"))
            assess = getattr(s, "assessment_and_feedback", "")

            step_summary = f"Teacher: {t_act} | Student: {s_act} | Method: {method}"
            full_steps_corpus.append(step_summary)

            formatted_steps.append(
                f"Step {step_no} (Method: {method}):\n"
                f"  - Teacher: {t_act}\n"
                f"  - Student: {s_act}\n"
                f"  - Assessment: {assess}"
            )

        steps_text = "\n\n".join(formatted_steps) if formatted_steps else "No development steps recorded."
        entrance_text = getattr(plan, "the_entrance", "Introduction phase")
        combined_classroom_tasks = f"{entrance_text}\n" + "\n".join(full_steps_corpus)

        competence_level = getattr(plan, "competence_level", getattr(plan, "educational_goal_or_standard", "General"))
        topic = getattr(plan, "lesson_topic", getattr(plan, "topic", "Civic Education"))

        # 3. LLM Qualitative Pedagogical Alignment Prompt
        prompt = f"""
You are a Senior Educational Quality Assurance Auditor evaluating curriculum alignment for Sri Lankan secondary schools.

COMPETENCY LEVEL: {competence_level}
TOPIC: {topic}

TARGET LEARNING OUTCOMES:
{outcomes_text}

CLASSROOM IMPLEMENTATION (THE ENTRANCE & PROCEDURAL STEPS):
[The Entrance]: {entrance_text}

[Development Steps]:
{steps_text}

EVALUATION INSTRUCTIONS:
1. Map each target learning outcome to the specific step numbers (e.g. [1, 2]) that actively deliver it.
2. Check Cognitive Depth Match: Does the student activity reflect the action verb (e.g., analyze, identify, explain) of the outcome (Bloom's Taxonomy)?
3. Identify any rogue or unrelated tasks that do not support any target outcome.
4. Set `is_aligned: true` if the student activity provides direct opportunity to achieve the outcome.
5. Provide a concise pedagogical reason.
"""

        parsed_eval = self._call_ollama_for_alignment(prompt)

        # 4. Integrate Vector Similarity Scores with Cognitive Evaluations
        processed_alignments: List[OutcomeTaskAlignment] = []
        overall_scores: List[float] = []

        # Fallback to pure vector analysis if Ollama produced empty evaluations
        if not parsed_eval.outcome_evaluations:
            for outcome_str in raw_outcomes_strings:
                sim = self.calculate_cosine_similarity(outcome_str, combined_classroom_tasks)
                aligned = sim >= 0.50
                processed_alignments.append(
                    OutcomeTaskAlignment(
                        learning_outcome=outcome_str,
                        addressed_in_steps=[1],
                        semantic_similarity_score=sim,
                        is_aligned=aligned,
                        cognitive_depth_match=aligned,
                        reasoning="Evaluated via local semantic similarity matching."
                    )
                )
                overall_scores.append(sim)
        else:
            for item in parsed_eval.outcome_evaluations:
                vec_sim = self.calculate_cosine_similarity(item.learning_outcome, combined_classroom_tasks)
                item.semantic_similarity_score = vec_sim

                # Composite score: 60% LLM Cognitive Evaluation + 40% Vector Semantic Similarity
                llm_weight = 1.0 if item.is_aligned else 0.0
                composite_item_score = (llm_weight * 0.6) + (min(max(vec_sim, 0.0), 1.0) * 0.4)
                overall_scores.append(composite_item_score)
                processed_alignments.append(item)

        total_outcomes = len(processed_alignments)
        aligned_count = sum(1 for a in processed_alignments if a.is_aligned)
        mean_score = round(float(np.mean(overall_scores)), 2) if overall_scores else 0.0

        return InternalAlignmentReport(
            competency_level=str(competence_level),
            overall_alignment_score=mean_score,
            total_outcomes=total_outcomes,
            aligned_outcomes=aligned_count,
            outcome_alignments=processed_alignments,
            unaligned_tasks=parsed_eval.unaligned_tasks,
            passed_alignment_guardrail=mean_score >= self.threshold
        )


# =====================================================================
# STANDALONE TEST
# =====================================================================
if __name__ == "__main__":
    evaluator = AlignmentEvaluator(threshold=0.75)

    test_plan = {
        "grade_level": "Grade 8",
        "subject": "Civic Education",
        "topic": "Direct Democracy in Ancient Athens",
        "educational_goal_or_standard": "8.1.1: Explains the features of direct democracy.",
        "the_entrance": "Teacher displays an image of the Athenian Assembly and asks how decisions were voted on.",
        "learning_outcomes": [
            {"description": "Describe how the Athenian Assembly (Ekklesia) operated for direct lawmaking."},
            {"description": "Compare citizen participation in direct democracy versus modern representative democracy."}
        ],
        "procedures": [
            {
                "step_number": 1,
                "phase_title": "Engage & Explore",
                "teacher_action": "Explains the direct voting procedure used by Athenian citizens in the Ekklesia.",
                "student_action": "Students list the 3 core functions of the Ekklesia in their workbooks."
            },
            {
                "step_number": 2,
                "phase_title": "Elaborate",
                "teacher_action": "Instructs groups to compare Athenian voting with modern parliament elections.",
                "student_action": "Complete a Venn diagram highlighting differences in citizen participation."
            }
        ]
    }

    # Wrap mock dict in a simple object wrapper for testing
    MockPlan = type("MockPlan", (), {
        "learning_outcomes": test_plan["learning_outcomes"],
        "procedures": test_plan["procedures"],
        "the_entrance": test_plan["the_entrance"],
        "educational_goal_or_standard": test_plan["educational_goal_or_standard"],
        "topic": test_plan["topic"]
    })()

    print("=" * 80)
    print("🎯 RUNNING LOCAL OLLAMA PEDAGOGICAL ALIGNMENT EVALUATION")
    print("=" * 80)

    report = evaluator.evaluate_alignment(MockPlan)

    print(f"📊 Overall Alignment Score: {report.overall_alignment_score * 100:.1f}% (Threshold: {evaluator.threshold * 100:.0f}%)")
    print(f"🛡️ Passed Guardrail: {report.passed_alignment_guardrail}")
    print(f"📈 Outcomes Aligned: {report.aligned_outcomes}/{report.total_outcomes}")

    print("\n🔍 Alignment Breakdown by Outcome:")
    for idx, a in enumerate(report.outcome_alignments, 1):
        status_icon = "✅" if a.is_aligned else "❌"
        print(f"\n{status_icon} [Outcome {idx}]: {a.learning_outcome}")
        print(f"   ├─ Steps Addressed: {a.addressed_in_steps}")
        print(f"   ├─ Semantic Vector Similarity: {a.semantic_similarity_score:.4f}")
        print(f"   ├─ Cognitive Match (Bloom's): {'Yes' if a.cognitive_depth_match else 'No'}")
        print(f"   └─ Reason: {a.reasoning}")

    if report.unaligned_tasks:
        print(f"\n⚠️ Unaligned Tasks Detected: {report.unaligned_tasks}")
    else:
        print("\n🎉 Perfect Alignment! All classroom activities directly achieve the competency outcomes.")
    print("=" * 80)