from typing import List
from pydantic import BaseModel, Field


class VerifyAlignmentRequest(BaseModel):
    educational_goal: str = Field(
        default="",
        description="Target educational goal or competence level",
        examples=["8.1 Identifies the characteristics of direct democracy in ancient Athens."]
    )
    lesson_objectives: List[str] = Field(
        default_factory=list,
        description="List of specific learning objectives to evaluate for alignment",
        examples=[[
            "Explain the role of the Citizens' Assembly (Ecclesia)",
            "Compare direct participation with representative forms of governance"
        ]]
    )