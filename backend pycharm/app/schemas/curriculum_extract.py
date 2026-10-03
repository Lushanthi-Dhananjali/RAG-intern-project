from pydantic import BaseModel, Field


class CurriculumExtractRequest(BaseModel):
    raw_text: str = Field(
        default="",
        description="Raw unstructured curriculum or syllabus text to be parsed",
        examples=["Grade 8 Civic Education Unit 1: Democratic Governance and Citizen Participation..."]
    )