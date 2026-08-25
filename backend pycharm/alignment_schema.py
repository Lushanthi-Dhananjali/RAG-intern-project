from typing import List
from pydantic import BaseModel, Field


class ObjectiveAlignmentDetail(BaseModel):
    objective_id: int
    objective_text: str
    semantic_similarity_score: float = Field(
        description="Cosine similarity score between objective and educational goal (0.0 to 1.0)"
    )
    pedagogical_alignment_score: float = Field(
        description="LLM qualitative evaluation of cognitive alignment (0.0 to 1.0)"
    )
    is_aligned: bool = Field(
        description="True if both semantic and qualitative scores exceed threshold (>= 0.70)"
    )
    alignment_reasoning: str = Field(description="Explanation of why objective aligns or diverges")


class AlignmentReport(BaseModel):
    educational_goal: str
    overall_alignment_score: float = Field(
        description="Average alignment score across all lesson objectives (0.0 to 1.0)"
    )
    passed_alignment_guardrail: bool = Field(
        description="True if overall_alignment_score >= threshold (e.g., 0.75)"
    )
    detailed_objectives_alignment: List[ObjectiveAlignmentDetail]