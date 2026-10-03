from typing import List
from pydantic import BaseModel, Field


class FactCheckReportDto(BaseModel):
    total_claims_extracted: int = Field(
        default=0,
        description="Total number of factual claims identified in the lesson plan",
        examples=[12]
    )
    supported_claims_count: int = Field(
        default=0,
        description="Number of claims verified against syllabus and textbook contexts",
        examples=[11]
    )
    grounding_score: float = Field(
        default=0.0,
        description="Ratio of supported claims to total claims",
        examples=[0.92]
    )
    passed: bool = Field(
        default=False,
        description="Whether the output satisfies the factual grounding guardrail",
        examples=[True]
    )
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="Claims that could not be corroborated with retrieved contexts"
    )
    explanation: str = Field(
        default="",
        description="Detailed evaluator diagnostic summary",
        examples=["All major historical references match Grade 8 Civic Education curriculum sources."]
    )