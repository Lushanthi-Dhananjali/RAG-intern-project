from typing import List
from pydantic import BaseModel, Field


class ClaimVerification(BaseModel):
    claim: str = Field(description="Individual factual statement extracted from generated lesson plan")
    is_supported: bool = Field(description="True if claim is explicitly supported by reference documents")
    source_reference: str = Field(description="Document ID/Snippet supporting the claim, or 'NOT_FOUND'")


class FactCheckReport(BaseModel):
    total_claims_extracted: int = Field(description="Total factual claims evaluated")
    supported_claims_count: int = Field(description="Number of claims verified against reference docs")
    grounding_score: float = Field(description="Faithfulness ratio (supported_claims / total_claims)")
    passed: bool = Field(description="True if grounding_score >= threshold (e.g., 0.85)")
    unsupported_claims: List[str] = Field(description="List of hallucinated or ungrounded claims")
    explanation: str = Field(description="Brief summary of verification findings")